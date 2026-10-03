"""
AEGIS-NET Graph Execution API Routes.
Executes the multi-agent Researcher → Coder → Deployer LangGraph workflow.
"""
import logging
import uuid
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Optional

from app.agents.graph import aegis_graph
from app.agents.state import AgentExecutionState
from app.services.session_manager import session_manager

router = APIRouter(prefix="/graph", tags=["Multi-Agent Workflow"])
logger = logging.getLogger(__name__)


class GraphRunRequest(BaseModel):
    input_query: str
    agent_id_researcher: str = "agent-researcher-01"
    agent_id_coder: str = "agent-coder-01"
    agent_id_deployer: str = "agent-deployer-01"


class GraphRunResponse(BaseModel):
    session_id: str
    status: str
    input_query: str
    research_notes: Optional[str] = None
    generated_code: Optional[str] = None
    deployment_receipt: Optional[str] = None
    cancellation_token: Optional[str] = None
    cancellation_reason: Optional[str] = None
    gateway_results: Optional[dict] = None


@router.post(
    "/run",
    response_model=GraphRunResponse,
    summary="Execute Multi-Agent Workflow",
    description=(
        "Runs the full Researcher → Coder → Deployer LangGraph pipeline. "
        "If the security gateway blocks any step, the graph cleanly cancels all "
        "downstream nodes via the cancellation token and returns status=CANCELLED."
    ),
)
async def run_graph(req: GraphRunRequest):
    """
    Full multi-agent execution endpoint.
    1. Opens a single session shared across all three agents.
    2. Invokes the LangGraph compiled graph.
    3. Returns final workflow state including gateway audit trail.
    """
    # Create a shared session for this run (RESEARCHER role — least privileged entry)
    session = session_manager.start_session(req.agent_id_researcher, "RESEARCHER")
    session_id = session.session_id

    # Also register coder and deployer agent sessions
    try:
        from app.services.supabase_client import get_supabase_client
        from datetime import datetime, timezone
        client = get_supabase_client()
        for agent_id, role in [
            (req.agent_id_coder, "CODER"),
            (req.agent_id_deployer, "DEPLOYER"),
        ]:
            client.table("agents").upsert({"id": agent_id, "role": role}, on_conflict="id").execute()
    except Exception:
        pass  # Non-fatal — sessions are still usable

    initial_state: AgentExecutionState = {
        "session_id": session_id,
        "agent_id_researcher": req.agent_id_researcher,
        "agent_id_coder": req.agent_id_coder,
        "agent_id_deployer": req.agent_id_deployer,
        "input_query": req.input_query,
        "research_notes": None,
        "generated_code": None,
        "deployment_receipt": None,
        "cancellation_token": None,
        "cancellation_reason": None,
        "status": "RUNNING",
        "gateway_results": {},
    }

    logger.info(f"[GRAPH] Starting workflow | session={session_id} | query={req.input_query[:80]!r}")

    try:
        final_state = aegis_graph.invoke(initial_state)
    except Exception as e:
        logger.error(f"[GRAPH] Unexpected execution error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Workflow execution failed: {str(e)}",
        )

    terminal_status = final_state.get("status", "UNKNOWN")
    logger.info(f"[GRAPH] Workflow complete | session={session_id} | status={terminal_status}")

    return GraphRunResponse(
        session_id=session_id,
        status=terminal_status,
        input_query=req.input_query,
        research_notes=final_state.get("research_notes"),
        generated_code=final_state.get("generated_code"),
        deployment_receipt=final_state.get("deployment_receipt"),
        cancellation_token=final_state.get("cancellation_token"),
        cancellation_reason=final_state.get("cancellation_reason"),
        gateway_results=final_state.get("gateway_results"),
    )
