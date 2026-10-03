"""
AEGIS-NET Deployer API Routes.
Exposes staging deployment execution through AGENTSHIELD gate controls.
"""
import logging
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Dict, Any, Optional

from app.agents.deployer import deployer_node
from app.services.session_manager import session_manager

router = APIRouter(prefix="/deployer", tags=["Deployer"])
logger = logging.getLogger(__name__)


class DeployRunRequest(BaseModel):
    generated_code: Optional[str] = None
    target_environment: str = "staging"


@router.post(
    "/{session_id}/run",
    summary="Trigger Deployer Agent for Staging Deployment",
    description="Executes Deployer Agent node, running build validation, security check, and sandbox staging.",
)
async def run_deployer_agent(session_id: str, req: DeployRunRequest) -> Dict[str, Any]:
    """Execute Deployer Agent node for session."""
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
        "input_query": "Staging Deployment Task",
        "research_notes": f"Research notes for session {session_id}",
        "generated_code": req.generated_code or f"# Code for session {session_id}",
        "deployment_receipt": None,
        "cancellation_token": None,
        "cancellation_reason": None,
        "status": "RUNNING",
        "gateway_results": {},
    }

    final_state = deployer_node(initial_state)
    return {
        "session_id": session_id,
        "status": final_state.get("status"),
        "deployment_receipt": final_state.get("deployment_receipt"),
        "cancellation_token": final_state.get("cancellation_token"),
        "cancellation_reason": final_state.get("cancellation_reason"),
        "gateway_results": final_state.get("gateway_results"),
    }
