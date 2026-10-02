"""
AEGIS-NET Incident Lifecycle Service.
Creates, manages, and resolves security incidents triggered by BLOCK decisions.
Severity is auto-assigned from risk_score.
"""
import logging
import threading
import asyncio
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.services.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)

# Severity ladder based on risk_score
SEVERITY_CRITICAL_MIN = 0.95
SEVERITY_HIGH_MIN = 0.80
SEVERITY_MEDIUM_MIN = 0.60


def _assign_severity(risk_score: float) -> str:
    if risk_score >= SEVERITY_CRITICAL_MIN:
        return "CRITICAL"
    if risk_score >= SEVERITY_HIGH_MIN:
        return "HIGH"
    return "MEDIUM"


class IncidentService:
    """
    Incident lifecycle manager.
    All incidents map 1-to-1 to BLOCK decisions from the Policy Engine.
    """

    def __init__(self):
        # In-memory registry for fast lookups before Supabase round-trip
        self._incidents: Dict[str, Dict[str, Any]] = {}

    def create_incident(
        self,
        agent_id: str,
        session_id: str,
        tool_call_id: str,
        risk_score: float,
        threat_score: float,
        decision: str,
        reasons: List[str],
        tool_name: str,
    ) -> Dict[str, Any]:
        """
        Creates a new OPEN incident, auto-assigning severity from risk_score.
        Writes to Supabase security_events (Realtime) + incidents table.
        """
        incident_id = str(uuid.uuid4())
        now_utc = datetime.now(timezone.utc).isoformat()
        severity = _assign_severity(risk_score)

        incident = {
            "id": incident_id,
            "agent_id": agent_id,
            "session_id": session_id,
            "tool_call_id": tool_call_id,
            "risk_score": risk_score,
            "decision": decision,
            "severity": severity,
            "status": "OPEN",
            "created_at": now_utc,
            "resolved_at": None,
        }
        self._incidents[incident_id] = {
            **incident,
            "threat_score": threat_score,
            "reasons": reasons,
            "tool_name": tool_name,
        }

        try:
            client = get_supabase_client()

            # 1. Write to incidents table
            client.table("incidents").insert(incident).execute()

            # 2. Emit real-time security event for dashboard subscribers
            security_event = {
                "id": str(uuid.uuid4()),
                "session_id": session_id,
                "event_type": "POLICY_BLOCK",
                "severity": severity,
                "details": {
                    "incident_id": incident_id,
                    "agent_id": agent_id,
                    "tool_name": tool_name,
                    "risk_score": risk_score,
                    "threat_score": threat_score,
                    "reasons": reasons,
                    "decision": decision,
                },
                "created_at": now_utc,
            }
            client.table("security_events").insert(security_event).execute()

            logger.warning(
                f"[INCIDENT CREATED] {incident_id} | Severity: {severity} | "
                f"Agent: {agent_id} | Tool: {tool_name} | Risk: {risk_score:.4f}"
            )
        except Exception as e:
            logger.error(f"[INCIDENT] Supabase write failed: {e}")

        # Trigger Gemini forensic analysis in background (Slow Path — never blocks fast path)
        incident_payload = dict(self._incidents[incident_id])
        t = threading.Thread(
            target=self._run_forensics_background,
            args=(incident_id, incident_payload),
            daemon=True,
        )
        t.start()

        return self._incidents[incident_id]

    def _run_forensics_background(self, incident_id: str, incident_payload: Dict[str, Any]) -> None:
        """Background daemon thread: runs async forensic analysis and saves result."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            report = loop.run_until_complete(self._analyze_forensics(incident_id, incident_payload))
            loop.close()

            # Persist to Supabase forensics_reports
            try:
                client = get_supabase_client()
                client.table("forensics_reports").insert({
                    "id": str(uuid.uuid4()),
                    "incident_id": incident_id,
                    "cwe_id": report.cwe_id,
                    "attack_vector": report.attack_vector,
                    "mitigation_rule": report.suggested_patch[:500],
                    "summary": report.threat_summary[:1000],
                    "raw_report": report.model_dump(),
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }).execute()
            except Exception as e:
                logger.debug(f"[FORENSICS] Supabase write note: {e}")

            # Register in-memory for fast API retrieval
            from app.api.v1.routes_forensics import register_forensic_report
            register_forensic_report(incident_id, report)
            logger.info(f"[FORENSICS] Report saved for incident {incident_id}: {report.cwe_id}")

        except Exception as e:
            logger.error(f"[FORENSICS] Background analysis failed: {e}")

    async def _analyze_forensics(self, incident_id: str, incident_payload: Dict[str, Any]):
        """Async wrapper that calls the Gemini CISO engine."""
        from app.forensics.gemini_ciso import generate_forensic_report
        return await generate_forensic_report(incident_payload)

    def get_incident(self, incident_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve incident by ID — memory-first, Supabase fallback."""
        if incident_id in self._incidents:
            return self._incidents[incident_id]

        try:
            client = get_supabase_client()
            result = client.table("incidents").select("*").eq("id", incident_id).single().execute()
            return result.data
        except Exception:
            return None

    def list_incidents(
        self,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """List incidents with optional status filter, ordered by newest first."""
        try:
            client = get_supabase_client()
            query = client.table("incidents").select("*").order("created_at", desc=True)
            if status:
                query = query.eq("status", status)
            result = query.range(offset, offset + limit - 1).execute()
            return {
                "incidents": result.data,
                "count": len(result.data),
                "offset": offset,
                "limit": limit,
            }
        except Exception as e:
            logger.error(f"[INCIDENT] List failed: {e}")
            return {"incidents": [], "count": 0, "offset": offset, "limit": limit, "error": str(e)}

    def update_status(
        self, incident_id: str, new_status: str
    ) -> Dict[str, Any]:
        """
        Transition incident status to RESOLVED or FALSE_POSITIVE.
        Records resolved_at timestamp on RESOLVED.
        """
        allowed = {"RESOLVED", "FALSE_POSITIVE", "INVESTIGATING"}
        if new_status not in allowed:
            raise ValueError(f"Invalid status '{new_status}'. Must be one of {allowed}.")

        now_utc = datetime.now(timezone.utc).isoformat()
        update_payload: Dict[str, Any] = {"status": new_status}
        if new_status == "RESOLVED":
            update_payload["resolved_at"] = now_utc

        if incident_id in self._incidents:
            self._incidents[incident_id]["status"] = new_status
            if new_status == "RESOLVED":
                self._incidents[incident_id]["resolved_at"] = now_utc

        try:
            client = get_supabase_client()
            client.table("incidents").update(update_payload).eq("id", incident_id).execute()
            logger.info(f"[INCIDENT] {incident_id} updated to {new_status}.")
        except Exception as e:
            logger.error(f"[INCIDENT] Status update failed: {e}")

        return {
            "incident_id": incident_id,
            "new_status": new_status,
            "updated_at": now_utc,
        }


# Global singleton
incident_service = IncidentService()
