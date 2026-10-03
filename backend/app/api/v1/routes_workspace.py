"""
AEGIS-NET Workspace API Routes.
Exposes endpoints to view real files created by Coder Agent in sandboxed session workspaces.
"""
import logging
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel
from typing import Dict, Any, Optional

from app.containment.sandbox import sandbox_list_directory, sandbox_read_file, sandbox_write_file
from app.agents.coder import coder_node
from app.services.session_manager import session_manager

router = APIRouter(prefix="/workspace", tags=["Workspace"])
logger = logging.getLogger(__name__)


class CoderRunRequest(BaseModel):
    research_notes: Optional[str] = None
    input_query: Optional[str] = None


@router.get(
    "/{session_id}/tree",
    summary="Get Workspace Directory Tree",
    description="Returns real file tree for session-scoped workspace inside agent_workspace/{session_id}.",
)
async def get_workspace_tree(session_id: str, path: str = Query(default=".", description="Relative path within workspace")) -> Dict[str, Any]:
    """Retrieve directory tree for session workspace."""
    result = sandbox_list_directory(relative_path=path, session_id=session_id)
    if "error" in result and not result.get("entries"):
        # If workspace dir does not exist yet, return empty list cleanly
        return {"session_id": session_id, "path": path, "entries": []}
    return result


@router.get(
    "/{session_id}/file",
    summary="Read Real Workspace File Content",
    description="Reads content of a specific file in the sandboxed session workspace. Prevents path traversal.",
)
async def get_workspace_file(session_id: str, path: str = Query(..., description="Relative file path within session workspace")) -> Dict[str, Any]:
    """Retrieve real file content."""
    res = sandbox_read_file(relative_path=path, session_id=session_id)
    if "error" in res:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND if "not found" in res["error"].lower() else status.HTTP_403_FORBIDDEN,
            detail=res["error"],
        )
    return res


@router.post(
    "/{session_id}/coder/run",
    summary="Trigger Coder Agent for Workspace Generation",
    description="Sends research notes to Coder Agent, which generates implementation files through AGENTSHIELD gateway.",
)
async def run_coder_agent(session_id: str, req: CoderRunRequest) -> Dict[str, Any]:
    """Execute Coder Agent node for session."""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found.",
        )

    initial_state = {
        "session_id": session_id,
        "agent_id_researcher": "agent-researcher-01",
        "agent_id_coder": "agent-coder-01",
        "agent_id_deployer": "agent-deployer-01",
        "input_query": req.input_query or "Build python solution",
        "research_notes": req.research_notes or f"Research notes for session {session_id}",
        "generated_code": None,
        "deployment_receipt": None,
        "cancellation_token": None,
        "cancellation_reason": None,
        "status": "RUNNING",
        "gateway_results": {},
    }

    final_state = coder_node(initial_state)
    return {
        "session_id": session_id,
        "status": final_state.get("status"),
        "generated_code": final_state.get("generated_code"),
        "cancellation_token": final_state.get("cancellation_token"),
        "cancellation_reason": final_state.get("cancellation_reason"),
        "gateway_results": final_state.get("gateway_results"),
    }
