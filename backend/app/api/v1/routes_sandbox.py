"""
AEGIS-NET Sandbox & Isolation API Routes.
Exposes endpoints for sandbox isolation status, allowed/blocked tools, and quarantine management.
"""
import logging
from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any

from app.containment.sandbox import WORKSPACE_ROOT
from app.containment.circuit_breaker import circuit_breaker
from app.containment.quarantine import quarantine_engine
from app.services.session_manager import session_manager
from app.services.rbac_engine import rbac_engine

router = APIRouter(prefix="/sandbox", tags=["Sandbox"])
logger = logging.getLogger(__name__)


@router.get(
    "/{session_id}",
    summary="Get Session Sandbox Details",
    description="Returns sandbox isolation status, workspace path, allowed/blocked tool permissions, and quarantine state.",
)
async def get_sandbox_details(session_id: str) -> Dict[str, Any]:
    """Retrieve sandbox telemetry for session."""
    session = session_manager.get_session(session_id)

    role = session.role if session else "CODER"
    breaker_status = circuit_breaker.get_status(session_id)
    is_quarantined = quarantine_engine.is_quarantined(session_id)

    # Determine allowed and blocked tools based on role RBAC
    all_tools = ["search_docs", "write_workspace_file", "read_file", "deploy_service", "read_system_secrets", "arbitrary_shell"]
    allowed_tools = []
    blocked_tools = []

    for t in all_tools:
        perm = rbac_engine.check_permission(role, t)
        if getattr(perm, "is_allowed", False):
            allowed_tools.append(t)
        else:
            blocked_tools.append(t)

    status_str = "QUARANTINED" if is_quarantined else ("BREAKER_TRIPPED" if breaker_status.get("state") == "OPEN" else "ISOLATED")

    return {
        "session_id": session_id,
        "agent_role": role,
        "workspace_root": str(WORKSPACE_ROOT / session_id),
        "status": status_str,
        "isolation_status": "QUARANTINED" if is_quarantined else "PROTECTED_SANDBOX",
        "circuit_breaker_state": breaker_status.get("state", "CLOSED"),
        "allowed_tools": allowed_tools,
        "blocked_tools": blocked_tools,
        "active_session": session.model_dump() if session else None,
    }
