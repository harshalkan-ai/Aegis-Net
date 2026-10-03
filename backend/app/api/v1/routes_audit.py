"""
AEGIS-NET Audit Log API Routes.
"""
import logging
from fastapi import APIRouter, Query
from typing import Optional

from app.audit.audit_service import audit_service

router = APIRouter(prefix="/audit", tags=["Audit Logs"])
logger = logging.getLogger(__name__)


@router.get(
    "/logs",
    summary="Paginated Audit Log Trail",
    description="Returns chronologically ordered audit log entries with optional filtering by event_name or actor.",
)
async def get_audit_logs(
    event_name: Optional[str] = Query(default=None, description="Filter by event name"),
    actor: Optional[str] = Query(default=None, description="Filter by actor (agent_id or system)"),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    return audit_service.get_logs(
        limit=limit,
        offset=offset,
        event_name=event_name,
        actor=actor,
    )
