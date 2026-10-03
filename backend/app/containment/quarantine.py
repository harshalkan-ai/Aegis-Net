"""
AEGIS-NET Quarantine Engine.
Marks agent sessions as QUARANTINED in memory and synchronizes to Supabase.
"""
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Set

from app.services.session_manager import session_manager
from app.services.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)


class QuarantineEngine:
    """
    Manages quarantine state for agent sessions.
    Quarantined sessions are immediately blocked at the gateway.
    """

    def __init__(self):
        # In-memory fast lookup sets
        self._quarantined_sessions: Set[str] = set()
        self._quarantined_agents: Set[str] = set()
        # session_id → quarantine record
        self._records: Dict[str, Dict[str, Any]] = {}

    def is_quarantined(self, session_id: str) -> bool:
        return session_id in self._quarantined_sessions

    def is_agent_quarantined(self, agent_id: str) -> bool:
        return agent_id in self._quarantined_agents

    def quarantine(
        self,
        session_id: str,
        agent_id: str,
        reason: str = "Automated containment due to high-risk incident",
    ) -> Dict[str, Any]:
        """
        Mark session and agent as QUARANTINED in memory + Supabase.
        Returns the quarantine record.
        """
        if session_id in self._quarantined_sessions:
            logger.debug(f"Session {session_id} already quarantined.")
            return self._records.get(session_id, {})

        self._quarantined_sessions.add(session_id)
        self._quarantined_agents.add(agent_id)

        # Update session status
        session_manager.update_session_status(session_id, "QUARANTINED")

        record_id = str(uuid.uuid4())
        now_utc = datetime.now(timezone.utc).isoformat()
        record = {
            "id": record_id,
            "session_id": session_id,
            "agent_id": agent_id,
            "reason": reason,
            "status": "ACTIVE",
            "created_at": now_utc,
        }
        self._records[session_id] = record

        try:
            client = get_supabase_client()
            client.table("quarantine_records").insert(record).execute()
            logger.warning(f"[QUARANTINE] Session {session_id} / Agent {agent_id} quarantined. Reason: {reason}")
        except Exception as e:
            logger.debug(f"Quarantine telemetry note: {e}")

        return record

    def release(
        self, session_id: str, agent_id: str
    ) -> Dict[str, Any]:
        """
        Release a session from quarantine. Updates DB record status to RELEASED.
        """
        self._quarantined_sessions.discard(session_id)
        self._quarantined_agents.discard(agent_id)

        # Restore ACTIVE status
        session_manager.update_session_status(session_id, "ACTIVE")

        now_utc = datetime.now(timezone.utc).isoformat()
        if session_id in self._records:
            self._records[session_id]["status"] = "RELEASED"

        try:
            client = get_supabase_client()
            client.table("quarantine_records").update({
                "status": "RELEASED",
            }).eq("session_id", session_id).eq("status", "ACTIVE").execute()
            logger.info(f"[QUARANTINE RELEASED] Session {session_id} / Agent {agent_id}.")
        except Exception as e:
            logger.debug(f"Quarantine release telemetry note: {e}")

        return {
            "session_id": session_id,
            "agent_id": agent_id,
            "status": "RELEASED",
            "released_at": now_utc,
        }

    def get_status(self, session_id: str) -> Dict[str, Any]:
        """Returns current quarantine status for a session."""
        is_q = session_id in self._quarantined_sessions
        record = self._records.get(session_id, {})
        return {
            "session_id": session_id,
            "quarantined": is_q,
            "status": record.get("status", "CLEAN"),
            "reason": record.get("reason"),
            "agent_id": record.get("agent_id"),
            "created_at": record.get("created_at"),
        }


# Global singleton
quarantine_engine = QuarantineEngine()
