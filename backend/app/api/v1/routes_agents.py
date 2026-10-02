"""
AEGIS-NET Agent & Session Management API Routes.
Exposes endpoints for session lifecycle, telemetry, and RBAC permission verification.
"""

from fastapi import APIRouter, HTTPException, status
from app.schemas.agent import (
    SessionStartRequest,
    SessionResponse,
    PermissionCheckRequest,
    PermissionCheckResponse,
)
from app.services.session_manager import session_manager
from app.services.rbac_engine import rbac_engine

router = APIRouter(prefix="/agents", tags=["Agents & Sessions"])


@router.post(
    "/session/start",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Initialize Agent Session",
    description="Creates a new tracked runtime session for an agent role, synchronizing with Supabase.",
)
async def start_session(payload: SessionStartRequest):
    """Start an agent session."""
    if not payload.agent_id or not payload.agent_id.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="agent_id must not be empty.",
        )
    if not payload.role or not payload.role.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="role must not be empty.",
        )

    session = session_manager.start_session(
        agent_id=payload.agent_id.strip(),
        role=payload.role.strip().upper(),
    )
    return session


@router.get(
    "/session/{session_id}",
    response_model=SessionResponse,
    summary="Get Agent Session Telemetry",
    description="Fetches current operational state, status, and telemetry for an active session.",
)
async def get_session(session_id: str):
    """Retrieve session by UUID."""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found.",
        )
    return session


@router.post(
    "/permissions/check",
    response_model=PermissionCheckResponse,
    summary="Evaluate RBAC Tool Permission",
    description="Executes sub-millisecond Zero-Trust RBAC policy evaluation for an agent role and tool.",
)
async def check_permissions(payload: PermissionCheckRequest):
    """Evaluate RBAC permission for a role and tool."""
    return rbac_engine.check_permission(
        role=payload.role,
        tool_name=payload.tool_name,
    )
