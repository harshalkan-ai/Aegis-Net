"""
AEGIS-NET Research API Routes.
Exposes endpoints for Tavily web research, session creation, and security evaluation.
"""
import logging
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Dict, Any, Optional, List

from app.agents.researcher import researcher_node
from app.services.session_manager import session_manager

router = APIRouter(prefix="/research", tags=["Research"])
logger = logging.getLogger(__name__)


class ResearchStartRequest(BaseModel):
    query: str
    agent_id: str = "agent-researcher-01"


# In-memory store for research session state
_research_sessions: Dict[str, Dict[str, Any]] = {}


@router.post(
    "/start",
    summary="Start Web Research Session",
    description="Creates a research session, invokes Researcher Agent with Tavily web search, and evaluates security risk.",
)
async def start_research(req: ResearchStartRequest) -> Dict[str, Any]:
    """Start research task and run through AGENTSHIELD gateway."""
    if not req.query or not req.query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Research query must not be empty.",
        )

    # 1. Start agent session
    session = session_manager.start_session(req.agent_id, "RESEARCHER")
    session_id = session.session_id

    # 2. Build execution state
    initial_state = {
        "session_id": session_id,
        "agent_id_researcher": req.agent_id,
        "agent_id_coder": "agent-coder-01",
        "agent_id_deployer": "agent-deployer-01",
        "input_query": req.query,
        "research_notes": None,
        "generated_code": None,
        "deployment_receipt": None,
        "cancellation_token": None,
        "cancellation_reason": None,
        "status": "RUNNING",
        "gateway_results": {},
    }

    # 3. Run Researcher Node (invokes Tavily + Security Gateway + ONNX ML)
    final_state = researcher_node(initial_state)

    gw_res = final_state.get("gateway_results", {}).get("researcher", {})

    record = {
        "session_id": session_id,
        "agent_id": req.agent_id,
        "query": req.query,
        "status": final_state.get("status"),
        "research_notes": final_state.get("research_notes"),
        "tavily_sources": final_state.get("tavily_sources", []),
        "cancellation_token": final_state.get("cancellation_token"),
        "cancellation_reason": final_state.get("cancellation_reason"),
        "security": {
            "decision": gw_res.get("decision", "ALLOW"),
            "reason": gw_res.get("reason", ""),
            "latency_ms": gw_res.get("latency_ms", 0.0),
            "envelope_token": gw_res.get("envelope_token", ""),
            "risk_assessment": gw_res.get("risk_assessment", {}),
        },
    }

    _research_sessions[session_id] = record
    return record


@router.get(
    "/{session_id}",
    summary="Get Research Session Details",
    description="Retrieves research findings, Tavily sources, and security evaluation for a session.",
)
async def get_research_session(session_id: str) -> Dict[str, Any]:
    """Get research session info."""
    if session_id in _research_sessions:
        return _research_sessions[session_id]

    # Fallback lookup in session_manager
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Research session '{session_id}' not found.",
        )

    return {
        "session_id": session_id,
        "agent_id": session.agent_id,
        "status": session.status,
        "query": "Restored session query",
        "research_notes": None,
        "tavily_sources": [],
        "security": {},
    }
