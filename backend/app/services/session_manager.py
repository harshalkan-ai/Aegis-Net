"""
AEGIS-NET Agent Session Manager.
Manages lifecycle, telemetry, and Supabase persistence for autonomous agent sessions.
"""

from datetime import datetime, timezone
import logging
from typing import Optional, Dict, Any
import uuid

from app.core.constants import AgentStatus
from app.schemas.agent import SessionResponse
from app.services.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages active agent sessions with Supabase synchronization and local memory caching."""

    def __init__(self):
        # In-memory session registry: session_id -> dict
        self._local_sessions: Dict[str, Dict[str, Any]] = {}

    def start_session(self, agent_id: str, role: str) -> SessionResponse:
        """
        Initializes a new session for an agent, persists it to Supabase, and caches locally.
        """
        session_id = str(uuid.uuid4())
        now_utc = datetime.now(timezone.utc).isoformat()
        clean_role = role.strip().upper()

        session_record = {
            "id": session_id,
            "agent_id": agent_id,
            "status": AgentStatus.ACTIVE.value,
            "created_at": now_utc,
        }

        # Cache locally
        self._local_sessions[session_id] = {
            "session_id": session_id,
            "agent_id": agent_id,
            "role": clean_role,
            "status": AgentStatus.ACTIVE.value,
            "created_at": now_utc,
            "tool_calls_count": 0,
            "incidents_count": 0,
        }

        # Persist to Supabase
        try:
            client = get_supabase_client()
            # Ensure agent exists in agents table first to respect foreign key constraint
            client.table("agents").upsert(
                {"id": agent_id, "role": clean_role},
                on_conflict="id"
            ).execute()

            # Insert session
            client.table("agent_sessions").insert(session_record).execute()
            logger.info(f"Session {session_id} successfully created and synchronized to Supabase.")
        except Exception as e:
            logger.warning(f"Failed to synchronize session {session_id} to Supabase: {e}. Active in local cache.")

        return SessionResponse(
            session_id=session_id,
            agent_id=agent_id,
            role=clean_role,
            status=AgentStatus.ACTIVE.value,
            created_at=now_utc,
            telemetry={
                "tool_calls_count": 0,
                "incidents_count": 0,
                "synced_db": True,
            },
        )

    def get_session(self, session_id: str) -> Optional[SessionResponse]:
        """
        Retrieves current session state and telemetry from cache or Supabase.
        """
        # Check local cache first
        if session_id in self._local_sessions:
            sess = self._local_sessions[session_id]
            return SessionResponse(
                session_id=sess["session_id"],
                agent_id=sess["agent_id"],
                role=sess["role"],
                status=sess["status"],
                created_at=sess["created_at"],
                telemetry={
                    "tool_calls_count": sess.get("tool_calls_count", 0),
                    "incidents_count": sess.get("incidents_count", 0),
                },
            )

        # Fallback to Supabase
        try:
            client = get_supabase_client()
            res = client.table("agent_sessions").select("*, agents(role)").eq("id", session_id).execute()
            if res.data and len(res.data) > 0:
                row = res.data[0]
                agent_data = row.get("agents", {})
                role = agent_data.get("role", "CODER") if isinstance(agent_data, dict) else "CODER"

                session_obj = SessionResponse(
                    session_id=row["id"],
                    agent_id=row["agent_id"],
                    role=role,
                    status=row.get("status", AgentStatus.ACTIVE.value),
                    created_at=row.get("created_at", ""),
                    telemetry={
                        "tool_calls_count": 0,
                        "incidents_count": 0,
                    },
                )
                # Cache locally for future fast lookups
                self._local_sessions[session_id] = {
                    "session_id": session_obj.session_id,
                    "agent_id": session_obj.agent_id,
                    "role": session_obj.role,
                    "status": session_obj.status,
                    "created_at": session_obj.created_at,
                    "tool_calls_count": 0,
                    "incidents_count": 0,
                }
                return session_obj
        except Exception as e:
            logger.warning(f"Error retrieving session {session_id} from Supabase: {e}")

        return None

    def update_session_status(self, session_id: str, new_status: str) -> bool:
        """Updates session status in both local cache and Supabase."""
        if session_id in self._local_sessions:
            self._local_sessions[session_id]["status"] = new_status

        try:
            client = get_supabase_client()
            client.table("agent_sessions").update({"status": new_status}).eq("id", session_id).execute()
            return True
        except Exception as e:
            logger.warning(f"Failed to update session status in Supabase: {e}")
            return session_id in self._local_sessions

    def record_tool_call(self, session_id: str) -> None:
        """Increments tool call count for telemetry."""
        if session_id in self._local_sessions:
            self._local_sessions[session_id]["tool_calls_count"] = (
                self._local_sessions[session_id].get("tool_calls_count", 0) + 1
            )


# Global singleton instance
session_manager = SessionManager()
