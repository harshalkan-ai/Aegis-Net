"""
AEGIS-NET Circuit Breaker.
Stateful circuit breaker with CLOSED → OPEN → HALF_OPEN states.
"""
import logging
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from enum import Enum

from app.services.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)


class BreakerState(str, Enum):
    CLOSED = "CLOSED"       # Normal operation
    OPEN = "OPEN"           # Tripped / Blocked
    HALF_OPEN = "HALF_OPEN" # Canary recovery probe


class CircuitBreaker:
    """
    Per-session circuit breaker. Tracks failure counts and manages state transitions.
    Calling trip() is idempotent — repeated calls are no-ops if already OPEN.
    """

    def __init__(self, failure_threshold: int = 3, reset_timeout_sec: int = 60):
        self.failure_threshold = failure_threshold
        self.reset_timeout_sec = reset_timeout_sec
        # session_id → {state, failures, tripped_at}
        self._state: Dict[str, Dict[str, Any]] = {}

    def _init_session(self, session_id: str) -> None:
        if session_id not in self._state:
            self._state[session_id] = {
                "state": BreakerState.CLOSED,
                "failures": 0,
                "tripped_at": None,
            }

    def get_state(self, session_id: str) -> BreakerState:
        self._init_session(session_id)
        entry = self._state[session_id]

        # Auto-transition OPEN → HALF_OPEN after timeout
        if (
            entry["state"] == BreakerState.OPEN
            and entry["tripped_at"] is not None
            and (time.time() - entry["tripped_at"]) >= self.reset_timeout_sec
        ):
            entry["state"] = BreakerState.HALF_OPEN
            logger.info(f"Circuit breaker for session {session_id} entering HALF_OPEN state.")

        return entry["state"]

    def trip(self, session_id: str, reason: str = "High-risk event detected", force: bool = False) -> bool:
        """
        Trip the circuit breaker. Idempotent — returns False if already OPEN.
        Returns True if this call caused the state change to OPEN.
        """
        self._init_session(session_id)
        entry = self._state[session_id]

        if entry["state"] == BreakerState.OPEN:
            logger.debug(f"Circuit breaker for {session_id} already OPEN — idempotent call ignored.")
            return False

        is_hard_trip = force or any(kw in reason for kw in ("BLOCKED", "Operator", "Manual", "administrative"))
        if is_hard_trip:
            entry["failures"] = self.failure_threshold
        else:
            entry["failures"] += 1

        if entry["failures"] >= self.failure_threshold or entry["state"] == BreakerState.HALF_OPEN:
            entry["state"] = BreakerState.OPEN
            entry["tripped_at"] = time.time()
            logger.warning(f"[CIRCUIT BREAKER] TRIPPED for session {session_id}. Reason: {reason}")
            self._flush_event(session_id, reason)
            return True

        logger.info(f"Circuit breaker failure recorded for {session_id}: {entry['failures']}/{self.failure_threshold}")
        return False

    def reset(self, session_id: str) -> None:
        """Manually reset circuit breaker to CLOSED state."""
        self._init_session(session_id)
        self._state[session_id] = {
            "state": BreakerState.CLOSED,
            "failures": 0,
            "tripped_at": None,
        }
        logger.info(f"Circuit breaker for session {session_id} reset to CLOSED.")

    def record_success(self, session_id: str) -> None:
        """Record a successful probe in HALF_OPEN state → reset to CLOSED."""
        self._init_session(session_id)
        entry = self._state[session_id]
        if entry["state"] == BreakerState.HALF_OPEN:
            self.reset(session_id)

    def get_status(self, session_id: str) -> Dict[str, Any]:
        state = self.get_state(session_id)
        entry = self._state.get(session_id, {})
        return {
            "session_id": session_id,
            "state": state.value,
            "failures": entry.get("failures", 0),
            "tripped_at": entry.get("tripped_at"),
            "threshold": self.failure_threshold,
        }

    def _flush_event(self, session_id: str, reason: str) -> None:
        """Persist circuit_breaker_triggered security event to Supabase."""
        try:
            client = get_supabase_client()
            client.table("security_events").insert({
                "session_id": session_id,
                "event_type": "CIRCUIT_BREAKER_TRIGGERED",
                "severity": "HIGH",
                "details": {
                    "reason": reason,
                    "state": BreakerState.OPEN.value,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
                "created_at": datetime.now(timezone.utc).isoformat(),
            }).execute()
        except Exception as e:
            logger.debug(f"Circuit breaker telemetry note: {e}")


# Global singleton
circuit_breaker = CircuitBreaker()
