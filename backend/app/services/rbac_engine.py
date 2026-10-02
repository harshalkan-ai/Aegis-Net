"""
AEGIS-NET RBAC Policy Engine.
Executes sub-millisecond, memory-cached Zero-Trust permission evaluations based on declarative RBAC matrices.
"""

import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional, Set

from app.schemas.agent import PermissionCheckResponse

logger = logging.getLogger(__name__)

RBAC_MATRIX_PATH = Path(__file__).resolve().parent.parent / "core" / "rbac_matrix.json"


class RBACEngine:
    """High-performance Role-Based Access Control evaluator."""

    def __init__(self, matrix_path: Optional[Path] = None):
        self.matrix_path = matrix_path or RBAC_MATRIX_PATH
        self._matrix: Dict[str, Dict[str, Set[str]]] = {}
        self.load_matrix()

    def load_matrix(self) -> None:
        """Loads and pre-indexes the RBAC policy matrix into O(1) hash sets."""
        if not self.matrix_path.exists():
            logger.error(f"RBAC Matrix file not found at {self.matrix_path}")
            self._matrix = {}
            return

        try:
            with open(self.matrix_path, "r", encoding="utf-8") as f:
                raw_matrix = json.load(f)

            processed = {}
            for role, rules in raw_matrix.items():
                role_key = role.strip().upper()
                processed[role_key] = {
                    "allowed": set(rules.get("allowed_tools", [])),
                    "denied": set(rules.get("denied_tools", [])),
                    "review": set(rules.get("review_tools", [])),
                }

            self._matrix = processed
            logger.info(f"RBAC Engine initialized with {len(self._matrix)} roles.")
        except Exception as e:
            logger.error(f"Failed to parse RBAC matrix: {e}")
            self._matrix = {}

    def check_permission(self, role: str, tool_name: str) -> PermissionCheckResponse:
        """
        Evaluates tool access permission for a given role in sub-millisecond time.

        Zero-Trust Evaluation Order:
        1. Role existence check
        2. Explicit denial check
        3. Review requirement check
        4. Explicit allowance check
        5. Default-deny fallback
        """
        start_time = time.perf_counter()
        normalized_role = role.strip().upper()
        clean_tool = tool_name.strip()

        if normalized_role not in self._matrix:
            latency_ms = round((time.perf_counter() - start_time) * 1000, 4)
            return PermissionCheckResponse(
                role=role,
                tool_name=tool_name,
                is_allowed=False,
                requires_review=False,
                evaluation_latency_ms=latency_ms,
                reason=f"Role '{role}' is not recognized in RBAC policy.",
            )

        role_rules = self._matrix[normalized_role]

        # 1. Denied tools
        if clean_tool in role_rules["denied"]:
            latency_ms = round((time.perf_counter() - start_time) * 1000, 4)
            return PermissionCheckResponse(
                role=role,
                tool_name=tool_name,
                is_allowed=False,
                requires_review=False,
                evaluation_latency_ms=latency_ms,
                reason=f"Tool '{clean_tool}' is explicitly prohibited for role '{role}'.",
            )

        # 2. Review tools
        if clean_tool in role_rules["review"]:
            latency_ms = round((time.perf_counter() - start_time) * 1000, 4)
            return PermissionCheckResponse(
                role=role,
                tool_name=tool_name,
                is_allowed=True,
                requires_review=True,
                evaluation_latency_ms=latency_ms,
                reason=f"Tool '{clean_tool}' requires approval review for role '{role}'.",
            )

        # 3. Allowed tools
        if clean_tool in role_rules["allowed"]:
            latency_ms = round((time.perf_counter() - start_time) * 1000, 4)
            return PermissionCheckResponse(
                role=role,
                tool_name=tool_name,
                is_allowed=True,
                requires_review=False,
                evaluation_latency_ms=latency_ms,
                reason=f"Tool '{clean_tool}' is permitted for role '{role}'.",
            )

        # 4. Default-deny
        latency_ms = round((time.perf_counter() - start_time) * 1000, 4)
        return PermissionCheckResponse(
            role=role,
            tool_name=tool_name,
            is_allowed=False,
            requires_review=False,
            evaluation_latency_ms=latency_ms,
            reason=f"Tool '{clean_tool}' is not registered in allowed policy for role '{role}'.",
        )


# Global singleton instance
rbac_engine = RBACEngine()
