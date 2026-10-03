"""
AEGIS-NET Incidents API Routes.
"""
import logging
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel
from typing import Optional

from app.incidents.incident_service import incident_service

router = APIRouter(prefix="/incidents", tags=["Incidents"])
logger = logging.getLogger(__name__)


class StatusUpdateRequest(BaseModel):
    new_status: str  # RESOLVED | FALSE_POSITIVE | INVESTIGATING


@router.get(
    "",
    summary="List Incidents",
    description="Returns paginated list of security incidents. Filter by status: OPEN, RESOLVED, FALSE_POSITIVE.",
)
async def list_incidents(
    status: Optional[str] = Query(default=None, description="Filter by status (OPEN, RESOLVED, FALSE_POSITIVE, INVESTIGATING)"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    return incident_service.list_incidents(status=status, limit=limit, offset=offset)


@router.get(
    "/{incident_id}",
    summary="Get Incident Details",
    description="Returns full breakdown of a specific incident by ID.",
)
async def get_incident(incident_id: str):
    record = incident_service.get_incident(incident_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident '{incident_id}' not found.",
        )
    return record


@router.patch(
    "/{incident_id}/status",
    summary="Update Incident Status",
    description="Transition an incident to RESOLVED, FALSE_POSITIVE, or INVESTIGATING.",
)
async def update_incident_status(incident_id: str, req: StatusUpdateRequest):
    try:
        return incident_service.update_status(incident_id, req.new_status)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
