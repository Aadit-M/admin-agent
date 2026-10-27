"""Session state initialization and ambient enterprise context."""

from contextvars import ContextVar, Token
from contextlib import contextmanager
from typing import Iterator


CURRENT_DEMO_DATE = "2026-10-26"  # Monday, October 26, 2026

_current_state: ContextVar[dict | None] = ContextVar("admin_agent_state", default=None)


class EnterpriseState(dict):
    """Dictionary-backed state retaining the existing tool attribute interface."""

    def __getattr__(self, key: str):
        try:
            return self[key]
        except KeyError as exc:
            raise AttributeError(key) from exc


def create_initial_state() -> dict:
    """Create a fresh enterprise workspace with seeded demo data."""
    return EnterpriseState({
        "directory": {
            "alice": {
                "name": "Alice Carter",
                "role": "VP of Engineering",
                "department": "Engineering",
                "email": "alice@company.com",
                "timezone": "America/New_York",
                "citizenship": "USA",
                "manager": "CEO",
                "work_hours": (8, 18),
                "busy_utc": [
                    ("2026-10-26T12:00:00Z", "2026-10-26T13:00:00Z"),
                    ("2026-10-26T15:00:00Z", "2026-10-26T16:00:00Z"),
                ],
            },
            "bob": {
                "name": "Bob Lindqvist",
                "role": "Staff Engineer",
                "department": "Engineering",
                "email": "bob@company.com",
                "timezone": "Europe/London",
                "citizenship": "UK",
                "manager": "Alice Carter",
                "work_hours": (9, 18),
                "busy_utc": [
                    ("2026-10-26T10:00:00Z", "2026-10-26T11:30:00Z"),
                    ("2026-10-26T13:30:00Z", "2026-10-26T15:00:00Z"),
                ],
            },
            "priya": {
                "name": "Priya Sharma",
                "role": "HR & People Ops Lead",
                "department": "HR & Operations",
                "email": "priya@company.com",
                "timezone": "Asia/Kolkata",
                "citizenship": "India",
                "manager": "Alice Carter",
                "work_hours": (9, 19),
                "busy_utc": [("2026-10-26T09:00:00Z", "2026-10-26T11:00:00Z")],
            },
        },
        "purchase_orders": {
            "PO-2026-101": {
                "vendor": "CloudScale AWS",
                "budget_usd": 4500.0,
                "department": "Engineering",
                "status": "OPEN",
            },
            "PO-2026-102": {
                "vendor": "Global Events Co",
                "budget_usd": 3000.0,
                "department": "HR & Operations",
                "status": "OPEN",
            },
            "PO-2026-103": {
                "vendor": "Apex Hardware",
                "budget_usd": 2800.0,
                "department": "Engineering",
                "status": "OPEN",
            },
        },
        "corporate_policies": {
            "meal_expense_cap_usd": 100.0,
            "flight_hotel_cap_usd": 2500.0,
            "po_required_threshold_usd": 500.0,
            "default_meeting_duration_mins": 30,
        },
        "calendar_events": [],
        "sent_emails": [],
        "onboarding_ledger": {},
        "travel_visa_requests": [],
        "expense_reports": [],
        "routing_trace": [],
        "tool_logs": [],
        "last_graph_state": {},
        "final_summary": None,
    })


def get_current_state() -> dict:
    """Return state bound to the current API request."""
    state = _current_state.get()
    if state is None:
        raise RuntimeError("No enterprise session state is bound to this request.")
    return state


@contextmanager
def bind_state(state: dict) -> Iterator[None]:
    """Bind one session to the current execution context."""
    token: Token = _current_state.set(state)
    try:
        yield
    finally:
        _current_state.reset(token)


def build_ambient_context() -> str:
    """
    Creates an enterprise context snapshot so agents can resolve implicit
    references such as 'all employees', 'engineering team', and 'today'.
    """
    state = get_current_state()
    roster_lines = []
    for key, emp in state["directory"].items():
        roster_lines.append(
            f"- {emp['name']} (Key: '{key}', Role: {emp['role']}, Dept: {emp['department']}, "
            f"Email: {emp['email']}, TZ: {emp['timezone']}, Citizenship: {emp['citizenship']}, "
            f"Manager: {emp['manager']})"
        )
    po_lines = [
        f"- {po_id}: Vendor={data['vendor']}, MaxBudget=${data['budget_usd']}, Dept={data['department']}"
        for po_id, data in state["purchase_orders"].items()
    ]
    policies = state["corporate_policies"]
    return (
        f"CURRENT DATE: Monday, {CURRENT_DEMO_DATE}\n"
        f"ACTIVE EMPLOYEE DIRECTORY ({len(roster_lines)} employees total):\n"
        + "\n".join(roster_lines)
        + "\n\nACTIVE PURCHASE ORDERS (POs):\n"
        + "\n".join(po_lines)
        + "\n\nCORPORATE POLICY DEFAULTS:\n"
        f"- Default Meeting Duration (if unstated): {policies['default_meeting_duration_mins']} mins\n"
        f"- Meal Expense Limit: ${policies['meal_expense_cap_usd']}\n"
        f"- Travel Budget Auto-Approval Cap: ${policies['flight_hotel_cap_usd']}\n"
        f"- Vendor/Software Invoices > ${policies['po_required_threshold_usd']} require a valid matching PO."
    )
