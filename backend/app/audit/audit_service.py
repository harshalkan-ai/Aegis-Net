"""
AEGIS-NET Audit Service.
Asynchronously writes all security telemetry to the audit_logs Supabase table
without blocking the fast-path (<45ms) evaluation pipeline.
<<<<<<< HEAD
Maintains in-memory buffer so audit trail functions even when Supabase is disconnected.
=======
>>>>>>> 30aea8107e52fc279ef4176b187de31f143d2e0c
"""
import logging
import threading
import uuid
from datetime import datetime, timezone
<<<<<<< HEAD
from typing import Any, Dict, List, Optional
=======
from typing import Any, Dict, Optional
>>>>>>> 30aea8107e52fc279ef4176b187de31f143d2e0c

from app.services.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)


class AuditService:
    """
    Non-blocking structured audit logger.
    Every call to log() is fire-and-forget — it dispatches a daemon thread
    so the gateway fast-path is never stalled by Supabase I/O.
    """

<<<<<<< HEAD
    def __init__(self):
        self._local_logs: List[Dict[str, Any]] = []

=======
<<<<<<< HEAD
    def __init__(self):
        self._local_logs: list[Dict[str, Any]] = []

=======
>>>>>>> 269c4536791406ae7200b6f0aced48c638234a60
>>>>>>> 30aea8107e52fc279ef4176b187de31f143d2e0c
    def log(
        self,
        event_name: str,
        actor: str,
        payload: Dict[str, Any],
        session_id: Optional[str] = None,
    ) -> None:
        """
<<<<<<< HEAD
        Enqueue an audit entry for async Supabase persistence and cache locally.
=======
        Enqueue an audit entry for async Supabase persistence.
>>>>>>> 30aea8107e52fc279ef4176b187de31f143d2e0c
        Returns immediately — never blocks the caller.
        """
        record = {
            "id": str(uuid.uuid4()),
            "event_name": event_name,
            "actor": actor,
            "payload": payload,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
<<<<<<< HEAD
        if session_id:
            record["payload"] = {**payload, "session_id": session_id}

=======

<<<<<<< HEAD
>>>>>>> 30aea8107e52fc279ef4176b187de31f143d2e0c
        self._local_logs.insert(0, record)
        if len(self._local_logs) > 500:
            self._local_logs = self._local_logs[:500]

<<<<<<< HEAD
=======
=======
>>>>>>> 269c4536791406ae7200b6f0aced48c638234a60
>>>>>>> 30aea8107e52fc279ef4176b187de31f143d2e0c
        t = threading.Thread(target=self._persist, args=(record,), daemon=True)
        t.start()

    def _persist(self, record: Dict[str, Any]) -> None:
        """Background worker — persists record to Supabase audit_logs."""
        try:
            client = get_supabase_client()
            client.table("audit_logs").insert(record).execute()
        except Exception as e:
            # Audit failures are logged locally — never propagate to caller
<<<<<<< HEAD
            logger.debug(f"[AUDIT] Supabase write failed (cached in local memory): {e}")
=======
            logger.warning(f"[AUDIT] Supabase write failed (degraded mode): {e}")
>>>>>>> 30aea8107e52fc279ef4176b187de31f143d2e0c

    def get_logs(
        self,
        limit: int = 50,
        offset: int = 0,
        event_name: Optional[str] = None,
        actor: Optional[str] = None,
<<<<<<< HEAD
    ) -> List[Dict[str, Any]]:
        """Retrieve paginated audit log entries."""
        db_logs = []
=======
<<<<<<< HEAD
    ) -> list[Dict[str, Any]]:
        """Retrieve paginated audit log entries."""
        db_logs = []
=======
    ) -> Dict[str, Any]:
        """Retrieve paginated audit log entries."""
>>>>>>> 269c4536791406ae7200b6f0aced48c638234a60
>>>>>>> 30aea8107e52fc279ef4176b187de31f143d2e0c
        try:
            client = get_supabase_client()
            query = client.table("audit_logs").select("*").order("created_at", desc=True)

            if event_name:
                query = query.eq("event_name", event_name)
            if actor:
                query = query.eq("actor", actor)

            result = query.range(offset, offset + limit - 1).execute()
<<<<<<< HEAD
            if result.data:
                db_logs = result.data
        except Exception as e:
            logger.debug(f"[AUDIT] Supabase read note: {e}")

        # Combine memory logs with db logs (deduplicate by id)
=======
<<<<<<< HEAD
            if result.data:
                db_logs = result.data
        except Exception as e:
            logger.debug(f"[AUDIT] Supabase note: {e}")

        # Combine memory logs with db logs
>>>>>>> 30aea8107e52fc279ef4176b187de31f143d2e0c
        combined_map = {item["id"]: item for item in (db_logs + self._local_logs)}
        all_logs = list(combined_map.values())

        if event_name:
            all_logs = [l for l in all_logs if l.get("event_name") == event_name]
        if actor:
            all_logs = [l for l in all_logs if l.get("actor") == actor]

        all_logs.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return all_logs[offset : offset + limit]
<<<<<<< HEAD
=======
=======
            return {"logs": result.data, "count": len(result.data), "offset": offset, "limit": limit}
        except Exception as e:
            logger.error(f"[AUDIT] Failed to retrieve logs: {e}")
            return {"logs": [], "count": 0, "offset": offset, "limit": limit, "error": str(e)}
>>>>>>> 269c4536791406ae7200b6f0aced48c638234a60
>>>>>>> 30aea8107e52fc279ef4176b187de31f143d2e0c


# Global singleton
audit_service = AuditService()
