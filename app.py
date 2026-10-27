"""FastAPI application serving the enterprise admin API and React frontend."""

import logging
import os
from pathlib import Path
from threading import Lock, RLock
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from groq import Groq
from pydantic import BaseModel, Field

from admin_app.graph import AdminGraphState, build_admin_langgraph
from admin_app.scenarios import DEMO_SCENARIOS
from admin_app.state import bind_state, build_ambient_context, create_initial_state


load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Enterprise Admin AI", version="1.0.0")
FRONTEND_DIST = Path(__file__).parent / "frontend" / "dist"
SESSION_STATES: dict[str, dict] = {}
SESSION_LOCKS: dict[str, RLock] = {}
SESSIONS_LOCK = Lock()


class WorkflowRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=12000)
    model_id: str = "openai/gpt-oss-120b"
    api_key: str | None = None


def get_session_lock(session_id: str) -> RLock:
    with SESSIONS_LOCK:
        if session_id not in SESSION_LOCKS:
            SESSION_LOCKS[session_id] = RLock()
        return SESSION_LOCKS[session_id]


def get_session_state(session_id: str) -> dict:
    state = SESSION_STATES.get(session_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Workspace not found. Create a new workspace.")
    return state


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/api/session")
def create_session() -> dict:
    session_id = str(uuid4())
    with SESSIONS_LOCK:
        SESSION_STATES[session_id] = create_initial_state()
        SESSION_LOCKS[session_id] = RLock()
    return {"session_id": session_id}


@app.get("/api/session/{session_id}/state")
def session_state(session_id: str) -> dict:
    with get_session_lock(session_id):
        state = get_session_state(session_id)
        with bind_state(state):
            return {**state, "ambient_context": build_ambient_context()}


@app.post("/api/session/{session_id}/reset")
def reset_session(session_id: str) -> dict:
    with get_session_lock(session_id):
        get_session_state(session_id)
        SESSION_STATES[session_id] = create_initial_state()
        return {"status": "reset"}


@app.get("/api/scenarios")
def scenarios() -> list[dict[str, str]]:
    return [{"name": name, "prompt": prompt} for name, prompt in DEMO_SCENARIOS.items()]


@app.post("/api/session/{session_id}/run")
def run_workflow(session_id: str, request: WorkflowRequest) -> dict:
    prompt = request.prompt.strip()
    if not prompt:
        raise HTTPException(status_code=422, detail="Enter an instruction before running the workflow.")
    api_key = request.api_key or os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        raise HTTPException(status_code=400, detail="Add a Groq API key in Settings or configure GROQ_API_KEY.")

    with get_session_lock(session_id):
        state = get_session_state(session_id)
        state["routing_trace"] = []
        state["tool_logs"] = []
        state["last_graph_state"] = {}
        state["final_summary"] = None
        initial_state: AdminGraphState = {
            "user_request": prompt,
            "ambient_context": "",
            "completed_agents": [],
            "agent_reports": [],
            "next_agent": "",
            "routing_reason": "",
            "final_summary": "",
        }

        try:
            with bind_state(state):
                initial_state["ambient_context"] = build_ambient_context()
                graph = build_admin_langgraph(Groq(api_key=api_key), request.model_id)
                for event in graph.stream(initial_state):
                    for node_update in event.values():
                        state["last_graph_state"].update(node_update)
                state["final_summary"] = state["last_graph_state"].get("final_summary")
                return {
                    "summary": state["final_summary"],
                    "routing_trace": state["routing_trace"],
                    "tool_logs": state["tool_logs"],
                }
        except Exception as exc:
            logger.exception("Workflow execution failed for session %s", session_id)
            raise HTTPException(
                status_code=502,
                detail=f"Workflow execution failed ({type(exc).__name__}). Check the server logs for details.",
            ) from exc


if FRONTEND_DIST.is_dir():
    assets_dir = FRONTEND_DIST / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def serve_frontend(path: str) -> FileResponse:
        requested_file = FRONTEND_DIST / path
        if path and requested_file.is_file() and FRONTEND_DIST in requested_file.resolve().parents:
            return FileResponse(requested_file)
        return FileResponse(FRONTEND_DIST / "index.html")
