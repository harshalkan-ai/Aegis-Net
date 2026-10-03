"""
AEGIS-NET Behavioral History & Deviation Tracker (B).
Tracks a rolling window of the last 10 tool invocations per session and computes deviation:
Deviation = 1.0 - (Count of Actions In Profile Actions / Total Actions in Window)
Scale: B in [0.0, 1.0]
"""

from collections import deque
from typing import Dict, List, Set, Optional

# Standard profile actions per agent role
ROLE_PROFILES: Dict[str, Set[str]] = {
    "RESEARCHER": {"search_docs", "fetch_web_content", "read_workspace_file"},
    "CODER": {"read_workspace_file", "write_workspace_file", "run_local_tests"},
    "DEPLOYER": {"build_artifact", "deploy_service", "get_deploy_status"},
}

WINDOW_SIZE = 10


class BehavioralTracker:
    """Maintains sliding-window behavioral history per session."""

    def __init__(self, window_size: int = WINDOW_SIZE):
        self.window_size = window_size
        # session_id -> deque of tool_names
        self._history: Dict[str, deque] = {}

    def get_profile_actions(self, role: str) -> Set[str]:
        """Returns the set of expected profile actions for a given role."""
        return ROLE_PROFILES.get(role.strip().upper(), set())

    def record_action(self, session_id: str, tool_name: str) -> None:
        """Appends an executed tool action into the session's sliding history window."""
        if not session_id:
            return
        if session_id not in self._history:
            self._history[session_id] = deque(maxlen=self.window_size)
        self._history[session_id].append(tool_name.strip())

    def calculate_deviation(
        self,
        session_id: Optional[str],
        role: str,
        current_tool: str,
        preview_only: bool = False,
    ) -> float:
        """
        Calculates the behavioral deviation B in [0.0, 1.0].
        Formula: 1.0 - (Count of Actions in Profile / Total Actions in Window)
        """
        profile = self.get_profile_actions(role)
        clean_tool = current_tool.strip()

        # Gather actions in window including the current action being evaluated
        if session_id and session_id in self._history and len(self._history[session_id]) > 0:
            actions = list(self._history[session_id])
            if clean_tool:
                actions.append(clean_tool)
            # Retain only the most recent WINDOW_SIZE actions
            actions = actions[-self.window_size :]
        else:
            actions = [clean_tool] if clean_tool else []

        if not actions:
            return 0.0

        profile_count = sum(1 for action in actions if action in profile)
        ratio = profile_count / len(actions)
        deviation = round(1.0 - ratio, 4)

        if not preview_only and session_id:
            self.record_action(session_id, clean_tool)

        return float(deviation)

    def reset_session(self, session_id: str) -> None:
        """Resets the history for a given session."""
        if session_id in self._history:
            del self._history[session_id]


# Global singleton instance
behavioral_tracker = BehavioralTracker()
