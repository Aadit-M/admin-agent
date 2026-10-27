"""LangGraph state, worker execution, and supervisor workflow."""

import json
import time
from typing import TypedDict

from groq import Groq
from langgraph.graph import END, START, StateGraph

from .schemas import (
    EXPENSE_TOOLS_SCHEMA,
    ONBOARDING_TOOLS_SCHEMA,
    SCHEDULING_TOOLS_SCHEMA,
    TRAVEL_VISA_TOOLS_SCHEMA,
)
from .state import build_ambient_context, get_current_state
from .tools import TOOL_FUNCTIONS


class AdminGraphState(TypedDict):
    user_request: str
    ambient_context: str
    completed_agents: list[str]
    agent_reports: list[dict]
    next_agent: str
    routing_reason: str
    final_summary: str

def execute_worker_node(
    agent_name: str,
    system_instructions: str,
    tools_schema: list[dict],
    state: AdminGraphState,
    client: Groq,
    model_id: str,
) -> dict:
    """Runs a specialized domain worker agent with its strict subset of tools."""
    t0 = time.perf_counter()
    ambient = build_ambient_context()
    prior_reports = json.dumps(state.get("agent_reports", []), indent=2)

    messages = [
        {
            "role": "system",
            "content": (
                f"{system_instructions}\n\n"
                f"=== AMBIENT ENTERPRISE CONTEXT (USE THIS FOR IMPLICIT/UNSAID DETAILS) ===\n{ambient}\n\n"
                f"=== COMPLETED WORK FROM OTHER AGENTS SO FAR ===\n{prior_reports}"
            ),
        },
        {"role": "user", "content": state["user_request"]},
    ]

    summary_text = ""
    for _ in range(6):
        resp = client.chat.completions.create(
            model=model_id,
            messages=messages,
            tools=tools_schema,
            tool_choice="auto",
            temperature=0.1,
        )
        msg = resp.choices[0].message
        messages.append(msg)

        if not msg.tool_calls:
            summary_text = msg.content or f"{agent_name} completed all tool actions."
            break

        for tc in msg.tool_calls:
            fn_name = tc.function.name
            fn_args = json.loads(tc.function.arguments)
            t_call_start = time.perf_counter()

            fn = TOOL_FUNCTIONS.get(fn_name)
            fn_out = fn(**fn_args) if fn else {"error": f"Unknown tool {fn_name}"}
            call_ms = round((time.perf_counter() - t_call_start) * 1000, 1)

            get_current_state().tool_logs.append(
                {
                    "step": len(get_current_state().tool_logs) + 1,
                    "agent": agent_name,
                    "tool": fn_name,
                    "args": fn_args,
                    "output": fn_out,
                    "latency_ms": call_ms,
                }
            )

            messages.append(
                {
                    "tool_call_id": tc.id,
                    "role": "tool",
                    "name": fn_name,
                    "content": json.dumps(fn_out),
                }
            )

    elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)
    updated_completed = list(state.get("completed_agents", [])) + [agent_name]
    updated_reports = list(state.get("agent_reports", [])) + [
        {"agent": agent_name, "summary": summary_text, "latency_ms": elapsed_ms}
    ]

    return {
        "ambient_context": build_ambient_context(),
        "completed_agents": updated_completed,
        "agent_reports": updated_reports,
    }

def build_admin_langgraph(client: Groq, model_id: str):
    """Constructs and compiles the LangGraph Supervisor + 4 Worker StateGraph."""

    def orchestrator_node(state: AdminGraphState) -> dict:
        t0 = time.perf_counter()
        completed = state.get("completed_agents", [])
        reports = state.get("agent_reports", [])

        router_prompt = f"""
        You are the LangGraph Supervisor Orchestrator for an Enterprise Admin AI system.
        Inspect the USER REQUEST and determine the next specialist worker agent to invoke.

        AVAILABLE SPECIALIST AGENTS:
        1. "onboarding_agent" -> Offer letters, provisioning corporate emails, software licenses, IT/VPN/YubiKey keys.
        2. "travel_visa_agent" -> Visa policy evaluation, business travel budget checks, visa/travel approval packets.
        3. "expense_agent" -> Expense receipts, vendor invoices, Purchase Order (PO) matching, anomaly triage.
        4. "scheduling_agent" -> Calendar meetings, cross-timezone slot finding, group/all-hands invites, single-paragraph agendas.
        5. "FINISH" -> Select FINISH when all parts of the user's request have been handled by the completed agents.

        ORDERING RULE:
        - If the request involves BOTH onboarding a new employee AND scheduling a meeting that includes them (or 'all employees'), you MUST route to "onboarding_agent" FIRST before "scheduling_agent".
        - Never repeat an agent that is already listed in COMPLETED_AGENTS: {completed}.

        Return ONLY a JSON object with keys:
        {{"next_agent": "<one of: onboarding_agent | travel_visa_agent | expense_agent | scheduling_agent | FINISH>", "reasoning": "<1 sentence why>"}}
        """

        resp = client.chat.completions.create(
            model=model_id,
            messages=[
                {"role": "system", "content": router_prompt},
                {
                    "role": "user",
                    "content": (
                        f"USER REQUEST:\n{state['user_request']}\n\n"
                        f"COMPLETED_AGENTS: {completed}\n"
                        f"REPORTS_SO_FAR: {json.dumps(reports)}"
                    ),
                },
            ],
            response_format={"type": "json_object"},
            temperature=0.0,
        )

        decision = json.loads(resp.choices[0].message.content)
        next_ag = decision.get("next_agent", "FINISH")
        reason = decision.get("reasoning", "Routing determined by supervisor.")

        # Guard against repeating an already completed worker
        if next_ag in completed and next_ag != "FINISH":
            next_ag = "FINISH"
            reason = "All required domain agents have completed execution."

        elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)
        get_current_state().routing_trace.append(
            {
                "hop": len(get_current_state().routing_trace) + 1,
                "from": "orchestrator",
                "to": next_ag,
                "reasoning": reason,
                "latency_ms": elapsed_ms,
            }
        )
        return {"next_agent": next_ag, "routing_reason": reason}

    def onboarding_agent_node(state: AdminGraphState) -> dict:
        prompt = """
        You are the Onboarding & IT Provisioning Agent.
        - Focus ONLY on onboarding logistics in the user prompt (ignore travel, expenses, or meeting scheduling).
        - If citizenship, department, manager, or start_date are not explicitly stated, infer sensible defaults from the Ambient Enterprise Context (e.g. start_date='2026-10-26', manager='Alice Carter', department='Engineering').
        - Execute `send_offer_letter` FIRST, then `provision_software_licenses`, then `generate_it_support_keys`.
        """
        return execute_worker_node("onboarding_agent", prompt, ONBOARDING_TOOLS_SCHEMA, state, client, model_id)

    def travel_visa_agent_node(state: AdminGraphState) -> dict:
        prompt = """
        You are the Visa & Corporate Travel Approval Agent.
        - Focus ONLY on travel and visa approval tasks in the user prompt.
        - Use the Ambient Enterprise Context to automatically infer the employee's citizenship and manager if not explicitly stated in the prompt.
        - Call `evaluate_visa_and_travel_policy` first, and then call `submit_travel_and_visa_approval` to issue the packet and route it to their manager/VP.
        """
        return execute_worker_node("travel_visa_agent", prompt, TRAVEL_VISA_TOOLS_SCHEMA, state, client, model_id)

    def expense_agent_node(state: AdminGraphState) -> dict:
        prompt = """
        You are the Expense & Invoice Triage Agent.
        - Focus ONLY on auditing expense receipts or vendor invoices mentioned in the user prompt.
        - For EVERY expense or invoice item mentioned, call `audit_expense_or_invoice` and then immediately record the outcome with `log_reconciliation_decision`.
        - If a vendor matches an active Purchase Order in the Ambient Context (or if no PO is provided), pass the relevant `po_number` (or empty string `""`).
        """
        return execute_worker_node("expense_agent", prompt, EXPENSE_TOOLS_SCHEMA, state, client, model_id)

    def scheduling_agent_node(state: AdminGraphState) -> dict:
        prompt = """
        You are the Meeting Coordination & Scheduling Agent.
        - Focus ONLY on scheduling meetings and sending calendar email invites.
        - UNSAID / IMPLICIT CONTEXT RULES:
          * If the user says 'all employees', 'everyone', or 'the team', pass `['all']` or read the full roster from the Ambient Enterprise Context.
          * If meeting duration is not stated, default to `30` minutes.
          * If meeting date is not stated or says 'today', use `'2026-10-26'`. If 'tomorrow', use `'2026-10-27'`.
          * If rough agenda notes are brief or unstated, synthesize a polished, executive SINGLE-PARAGRAPH agenda summary based on the meeting purpose and attendees' roles.
        - Call `get_participant_profiles`, then `find_optimal_meeting_slots`, pick the earliest conflict-free slot, call `book_calendar_meeting`, and finally call `send_calendar_email_invite`.
        """
        return execute_worker_node("scheduling_agent", prompt, SCHEDULING_TOOLS_SCHEMA, state, client, model_id)

    def synthesizer_node(state: AdminGraphState) -> dict:
        t0 = time.perf_counter()
        reports = json.dumps(state.get("agent_reports", []), indent=2)
        resp = client.chat.completions.create(
            model=model_id,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are the Executive Synthesizer Node. Combine the completed reports from all specialist "
                        "agents into a concise, executive-ready confirmation summary highlighting exact IDs, "
                        "time slots, policy verdicts, and actions taken."
                    ),
                },
                {
                    "role": "user",
                    "content": f"USER REQUEST:\n{state['user_request']}\n\nSPECIALIST REPORTS:\n{reports}",
                },
            ],
            temperature=0.2,
        )
        elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)
        get_current_state().routing_trace.append(
            {
                "hop": len(get_current_state().routing_trace) + 1,
                "from": "synthesizer",
                "to": "END",
                "reasoning": "Synthesized final cross-agent executive report.",
                "latency_ms": elapsed_ms,
            }
        )
        return {"final_summary": resp.choices[0].message.content}

    # Assemble LangGraph StateGraph
    builder = StateGraph(AdminGraphState)
    builder.add_node("orchestrator", orchestrator_node)
    builder.add_node("onboarding_agent", onboarding_agent_node)
    builder.add_node("travel_visa_agent", travel_visa_agent_node)
    builder.add_node("expense_agent", expense_agent_node)
    builder.add_node("scheduling_agent", scheduling_agent_node)
    builder.add_node("synthesizer", synthesizer_node)

    builder.add_edge(START, "orchestrator")
    builder.add_conditional_edges(
        "orchestrator",
        lambda state: state["next_agent"],
        {
            "onboarding_agent": "onboarding_agent",
            "travel_visa_agent": "travel_visa_agent",
            "expense_agent": "expense_agent",
            "scheduling_agent": "scheduling_agent",
            "FINISH": "synthesizer",
        },
    )
    builder.add_edge("onboarding_agent", "orchestrator")
    builder.add_edge("travel_visa_agent", "orchestrator")
    builder.add_edge("expense_agent", "orchestrator")
    builder.add_edge("scheduling_agent", "orchestrator")
    builder.add_edge("synthesizer", END)

    return builder.compile()
