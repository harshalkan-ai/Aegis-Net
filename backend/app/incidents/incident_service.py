"""
AEGIS-NET Incident Lifecycle Service.
Creates, manages, and resolves security incidents triggered by BLOCK/REVIEW decisions.
Severity is auto-assigned from risk_score.
Includes filesystem persistence so incidents survive backend restarts when Supabase is unconfigured.
"""
import json
import logging
import threading
import asyncio
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.services.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)

# Severity ladder based on risk_score
SEVERITY_CRITICAL_MIN = 0.95
SEVERITY_HIGH_MIN = 0.80
SEVERITY_MEDIUM_MIN = 0.60

# Filesystem fallback: store incidents as JSON files in backend/data/incidents/
_INCIDENTS_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "incidents"
_INCIDENTS_DIR.mkdir(parents=True, exist_ok=True)

_FORENSICS_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "forensics"
_FORENSICS_DIR.mkdir(parents=True, exist_ok=True)


def _assign_severity(risk_score: float) -> str:
    if risk_score >= SEVERITY_CRITICAL_MIN:
        return "CRITICAL"
    if risk_score >= SEVERITY_HIGH_MIN:
        return "HIGH"
    return "MEDIUM"


def _save_incident_to_disk(incident: Dict[str, Any]) -> None:
    """Persist incident to filesystem as JSON for cross-restart durability."""
    try:
        path = _INCIDENTS_DIR / f"{incident['id']}.json"
        with open(path, "w") as f:
            json.dump(incident, f, indent=2, default=str)
    except Exception as e:
        logger.debug(f"[INCIDENT] Filesystem write note: {e}")


def _load_incidents_from_disk() -> List[Dict[str, Any]]:
    """Load all incident JSON files from filesystem."""
    items = []
    try:
        for path in sorted(_INCIDENTS_DIR.glob("*.json"), reverse=True):
            try:
                with open(path) as f:
                    items.append(json.load(f))
            except Exception:
                pass
    except Exception as e:
        logger.debug(f"[INCIDENT] Filesystem read note: {e}")
    return items


def _save_forensics_to_disk(incident_id: str, report_dict: Dict[str, Any]) -> None:
    """Persist Gemini forensic report to filesystem."""
    try:
        path = _FORENSICS_DIR / f"{incident_id}.json"
        with open(path, "w") as f:
            json.dump(report_dict, f, indent=2, default=str)
    except Exception as e:
        logger.debug(f"[FORENSICS] Filesystem write note: {e}")


def _load_forensics_from_disk(incident_id: str) -> Optional[Dict[str, Any]]:
    """Load Gemini forensic report from filesystem."""
    try:
        path = _FORENSICS_DIR / f"{incident_id}.json"
        if path.exists():
            with open(path) as f:
                return json.load(f)
    except Exception:
        pass
    return None


class IncidentService:
    """
    Incident lifecycle manager.
    Incidents are created for BLOCK decisions (and REVIEW if high-risk).
    Supports filesystem persistence as primary fallback when Supabase is unconfigured.
    """

    def __init__(self):
        # In-memory registry for fast lookups
        self._incidents: Dict[str, Dict[str, Any]] = {}
        # Load any persisted incidents from disk on startup
        self._bootstrap_from_disk()

    def _bootstrap_from_disk(self) -> None:
        """Load persisted incidents from disk into memory on startup."""
        items = _load_incidents_from_disk()
        for item in items:
            if "id" in item:
                self._incidents[item["id"]] = item
        if items:
            logger.info(f"[INCIDENT] Bootstrapped {len(items)} incidents from filesystem persistence.")

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
        # Rich context fields for Gemini forensics
        role: str = "UNKNOWN",
        payload: Any = None,
        permission_score: float = 0.0,
        behavioral_score: float = 0.0,
        sensitivity_score: float = 0.0,
        criticality_score: float = 0.0,
        circuit_breaker_triggered: bool = False,
        prior_tool_calls: int = 0,
    ) -> Dict[str, Any]:
        """
        Creates a new OPEN incident, auto-assigning severity from risk_score.
        Writes to filesystem (primary), Supabase (if configured), and in-memory cache.
        Triggers Gemini forensic analysis in background.
        """
        incident_id = str(uuid.uuid4())
        now_utc = datetime.now(timezone.utc).isoformat()
        severity = _assign_severity(risk_score)

        incident = {
            "id": incident_id,
            "agent_id": agent_id,
            "session_id": session_id,
            "tool_call_id": tool_call_id,
            "tool_name": tool_name,
            "role": role,
            "risk_score": risk_score,
            "threat_score": threat_score,
            "permission_score": permission_score,
            "behavioral_score": behavioral_score,
            "sensitivity_score": sensitivity_score,
            "criticality_score": criticality_score,
            "decision": decision,
            "severity": severity,
            "status": "OPEN",
            "reasons": reasons,
            "payload_preview": str(payload)[:500] if payload else "",
            "circuit_breaker_triggered": circuit_breaker_triggered,
            "prior_tool_calls": prior_tool_calls,
            "created_at": now_utc,
            "resolved_at": None,
        }

        self._incidents[incident_id] = incident

        # Persist to filesystem (primary durability layer)
        _save_incident_to_disk(incident)

        # Attempt Supabase (non-blocking on failure)
        try:
            client = get_supabase_client()
            # Insert only DB-compatible fields into Supabase
            db_record = {
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
            client.table("incidents").insert(db_record).execute()

            # Emit real-time security event
            security_event = {
                "id": str(uuid.uuid4()),
                "session_id": session_id,
                "event_type": f"POLICY_{decision}",
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
        except Exception as e:
            logger.debug(f"[INCIDENT] Supabase write note: {e} — incident persisted to filesystem.")

        logger.warning(
            f"[INCIDENT CREATED] {incident_id} | Severity: {severity} | "
            f"Decision: {decision} | Agent: {agent_id} | Tool: {tool_name} | Risk: {risk_score:.4f}"
        )

        # Trigger Gemini forensic analysis in background (Slow Path — never blocks fast path)
        incident_payload = dict(incident)
        t = threading.Thread(
            target=self._run_forensics_background,
            args=(incident_id, incident_payload),
            daemon=True,
        )
        t.start()

        return incident

    def _run_forensics_background(self, incident_id: str, incident_payload: Dict[str, Any]) -> None:
        """Background daemon thread: runs async forensic analysis and saves result."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            report = loop.run_until_complete(self._analyze_forensics(incident_id, incident_payload))
            loop.close()

            report_dict = report.model_dump()

            # 1. Persist to filesystem
            _save_forensics_to_disk(incident_id, report_dict)

            # 2. Persist to Supabase forensics_reports
            try:
                client = get_supabase_client()
                client.table("forensics_reports").insert({
                    "id": str(uuid.uuid4()),
                    "incident_id": incident_id,
                    "cwe_id": report.cwe_id,
                    "attack_vector": report.attack_vector,
                    "mitigation_rule": report.suggested_patch[:500],
                    "summary": report.threat_summary[:1000],
                    "raw_report": report_dict,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }).execute()
            except Exception as e:
                logger.debug(f"[FORENSICS] Supabase write note: {e}")

            # 3. Register in-memory for fast API retrieval
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
        """Retrieve incident by ID — memory-first, filesystem, Supabase fallback."""
        if incident_id in self._incidents:
            return self._incidents[incident_id]

        # Filesystem fallback
        items = _load_incidents_from_disk()
        for item in items:
            if item.get("id") == incident_id:
                self._incidents[incident_id] = item
                return item

        # Supabase fallback
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
        # Primary source: in-memory (already bootstrapped from disk)
        memory_items = list(self._incidents.values())

        # Also scan disk for any incidents added since last bootstrap
        disk_items = _load_incidents_from_disk()
        combined_map = {i["id"]: i for i in disk_items}
        combined_map.update({i["id"]: i for i in memory_items})

        # Try Supabase as additional source
        try:
            client = get_supabase_client()
            query = client.table("incidents").select("*").order("created_at", desc=True)
            if status:
                query = query.eq("status", status)
            result = query.range(offset, offset + limit - 1).execute()
            if result.data:
                for item in result.data:
                    combined_map[item["id"]] = item
        except Exception as e:
            logger.debug(f"[INCIDENT] List Supabase note: {e}")

        all_incidents = list(combined_map.values())
        if status:
            all_incidents = [i for i in all_incidents if i.get("status") == status]

        all_incidents.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        sliced = all_incidents[offset: offset + limit]

        return {
            "incidents": sliced,
            "count": len(all_incidents),
            "offset": offset,
            "limit": limit,
        }

    def update_status(
        self, incident_id: str, new_status: str
    ) -> Dict[str, Any]:
        """
        Transition incident status to RESOLVED, FALSE_POSITIVE, or INVESTIGATING.
        Updates filesystem, memory, and Supabase.
        """
        allowed = {"RESOLVED", "FALSE_POSITIVE", "INVESTIGATING", "OPEN"}
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
            # Persist updated incident to disk
            _save_incident_to_disk(self._incidents[incident_id])

        try:
            client = get_supabase_client()
            client.table("incidents").update(update_payload).eq("id", incident_id).execute()
            logger.info(f"[INCIDENT] {incident_id} updated to {new_status}.")
        except Exception as e:
            logger.error(f"[INCIDENT] Status update Supabase note: {e}")

        return {
            "incident_id": incident_id,
            "new_status": new_status,
            "updated_at": now_utc,
        }


# Global singleton
incident_service = IncidentService()
