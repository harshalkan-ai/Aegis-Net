"""
AEGIS-NET Audit Service.
Asynchronously writes all security telemetry to the audit_logs Supabase table
without blocking the fast-path (<45ms) evaluation pipeline.
"""
import logging
import threading
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.services.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)


class AuditService:
    """
    Non-blocking structured audit logger.
    Every call to log() is fire-and-forget — it dispatches a daemon thread
    so the gateway fast-path is never stalled by Supabase I/O.
    """

    def log(
        self,
        event_name: str,
        actor: str,
        payload: Dict[str, Any],
        session_id: Optional[str] = None,
    ) -> None:
        """
        Enqueue an audit entry for async Supabase persistence.
        Returns immediately — never blocks the caller.
        """
        record = {
            "id": str(uuid.uuid4()),
            "event_name": event_name,
            "actor": actor,
            "payload": payload,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        t = threading.Thread(target=self._persist, args=(record,), daemon=True)
        t.start()

    def _persist(self, record: Dict[str, Any]) -> None:
        """Background worker — persists record to Supabase audit_logs."""
        try:
            client = get_supabase_client()
            client.table("audit_logs").insert(record).execute()
        except Exception as e:
            # Audit failures are logged locally — never propagate to caller
            logger.warning(f"[AUDIT] Supabase write failed (degraded mode): {e}")

    def get_logs(
        self,
        limit: int = 50,
        offset: int = 0,
        event_name: Optional[str] = None,
        actor: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Retrieve paginated audit log entries."""
        try:
            client = get_supabase_client()
            query = client.table("audit_logs").select("*").order("created_at", desc=True)

            if event_name:
                query = query.eq("event_name", event_name)
            if actor:
                query = query.eq("actor", actor)

            result = query.range(offset, offset + limit - 1).execute()
            return {"logs": result.data, "count": len(result.data), "offset": offset, "limit": limit}
        except Exception as e:
            logger.error(f"[AUDIT] Failed to retrieve logs: {e}")
            return {"logs": [], "count": 0, "offset": offset, "limit": limit, "error": str(e)}


# Global singleton
audit_service = AuditService()
