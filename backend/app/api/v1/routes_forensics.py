"""
AEGIS-NET Forensics API Routes.
Retrieves Gemini CISO forensic reports for blocked incidents.
Falls back to filesystem, then triggers on-demand analysis if no report yet exists.
"""
import logging
import asyncio
import threading
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
        "Falls back to filesystem, Supabase, then triggers on-demand generation if needed."
    ),
)
async def get_forensic_report(incident_id: str):
    """Retrieve forensic report — memory → filesystem → Supabase → on-demand generation."""

    # 1. Fast path: in-memory registry
    if incident_id in _forensic_registry:
        return _forensic_registry[incident_id]

    # 2. Filesystem fallback (survives restarts)
    from app.incidents.incident_service import _load_forensics_from_disk
    disk_report = _load_forensics_from_disk(incident_id)
    if disk_report:
        _forensic_registry[incident_id] = disk_report
        return disk_report

    # 3. Supabase fallback
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
            report = ForensicAnalysisReport(**raw)
            _forensic_registry[incident_id] = report.model_dump()
            return report
    except Exception as e:
        logger.debug(f"Forensics Supabase lookup note: {e}")

    # 4. On-demand generation: if incident exists but forensics haven't finished yet, generate now
    from app.incidents.incident_service import incident_service
    incident = incident_service.get_incident(incident_id)
    if incident:
        logger.info(f"[FORENSICS] Generating on-demand report for incident {incident_id}")
        try:
            from app.forensics.gemini_ciso import generate_forensic_report
            from app.incidents.incident_service import _save_forensics_to_disk
            report = await generate_forensic_report(incident)
            report_dict = report.model_dump()
            _forensic_registry[incident_id] = report_dict
            _save_forensics_to_disk(incident_id, report_dict)
            return report_dict
        except Exception as e:
            logger.error(f"[FORENSICS] On-demand generation failed: {e}")

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=(
            f"Forensic report for incident '{incident_id}' not found. "
            "The incident may not exist or analysis failed."
        ),
    )
