"""
AEGIS-NET Forensics API Routes.
Retrieves Gemini CISO forensic reports for blocked incidents.
"""
import logging
from fastapi import APIRouter, HTTPException, status

from app.schemas.forensics import ForensicAnalysisReport
from app.services.supabase_client import get_supabase_client

router = APIRouter(prefix="/forensics", tags=["Forensics"])
logger = logging.getLogger(__name__)

# In-memory forensic registry (populated by incident_service background thread)
_forensic_registry: dict = {}


def register_forensic_report(incident_id: str, report: ForensicAnalysisReport) -> None:
    """Called by incident_service background thread to register completed reports."""
    _forensic_registry[incident_id] = report.model_dump()


@router.get(
    "/{incident_id}",
    response_model=ForensicAnalysisReport,
    summary="Get Forensic Report",
    description=(
        "Retrieves the Gemini CISO forensic analysis for a blocked incident. "
        "Reports are generated asynchronously after incident creation and may not be "
        "immediately available (typically within 3 seconds)."
    ),
)
async def get_forensic_report(incident_id: str):
    """Retrieve forensic report — memory first, Supabase fallback."""
    # Fast path: in-memory registry
    if incident_id in _forensic_registry:
        return _forensic_registry[incident_id]

    # Supabase fallback
    try:
        client = get_supabase_client()
        result = (
            client.table("forensics_reports")
            .select("*")
            .eq("incident_id", incident_id)
            .single()
            .execute()
        )
        if result.data:
            raw = result.data.get("raw_report", {})
            return ForensicAnalysisReport(**raw)
    except Exception as e:
        logger.debug(f"Forensics Supabase lookup note: {e}")

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=(
            f"Forensic report for incident '{incident_id}' not found. "
            "It may still be generating (allow up to 3 seconds after block)."
        ),
    )
