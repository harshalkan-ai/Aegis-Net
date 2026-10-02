"""
AEGIS-NET Containment Management API Routes.
Exposes circuit breaker, quarantine, and containment status endpoints.
"""
import logging
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Optional

from app.containment.circuit_breaker import circuit_breaker, BreakerState
from app.containment.quarantine import quarantine_engine
from app.services.session_manager import session_manager

router = APIRouter(prefix="/containment", tags=["Containment"])
logger = logging.getLogger(__name__)


class TripRequest(BaseModel):
    session_id: str
    reason: str = "Manual administrative trip"


class QuarantineReleaseRequest(BaseModel):
    session_id: str
    agent_id: str


@router.post(
    "/circuit-breaker/trip",
    summary="Trip Circuit Breaker",
    description="Manually trip the circuit breaker for a session. Idempotent.",
)
async def trip_circuit_breaker(req: TripRequest):
    tripped = circuit_breaker.trip(session_id=req.session_id, reason=req.reason)
    if tripped:
        session_manager.update_session_status(req.session_id, "QUARANTINED")
    status_info = circuit_breaker.get_status(req.session_id)
    return {
        "tripped": tripped,
        "message": "Circuit breaker tripped." if tripped else "Circuit breaker already OPEN — idempotent call.",
        **status_info,
    }


@router.post(
    "/circuit-breaker/reset",
    summary="Reset Circuit Breaker",
    description="Manually reset a circuit breaker to CLOSED state.",
)
async def reset_circuit_breaker(req: TripRequest):
    circuit_breaker.reset(req.session_id)
    return {
        "reset": True,
        "message": f"Circuit breaker for session {req.session_id} reset to CLOSED.",
        **circuit_breaker.get_status(req.session_id),
    }


@router.post(
    "/quarantine/release",
    summary="Release Agent from Quarantine",
    description="Releases a quarantined session, restoring ACTIVE status.",
)
async def release_quarantine(req: QuarantineReleaseRequest):
    if not quarantine_engine.is_quarantined(req.session_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {req.session_id} is not currently quarantined.",
        )
    result = quarantine_engine.release(req.session_id, req.agent_id)
    circuit_breaker.reset(req.session_id)
    return result


@router.get(
    "/status/{session_id}",
    summary="Get Session Containment Status",
    description="Returns circuit breaker state and quarantine status for a session.",
)
async def get_containment_status(session_id: str):
    breaker = circuit_breaker.get_status(session_id)
    quarantine = quarantine_engine.get_status(session_id)
    session = session_manager.get_session(session_id)

    return {
        "session_id": session_id,
        "session_status": session.status if session else "NOT_FOUND",
        "circuit_breaker": breaker,
        "quarantine": quarantine,
    }
