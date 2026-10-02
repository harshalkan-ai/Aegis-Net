"""
AEGIS-NET Context Engine.
Collects and aggregates multi-factor zero-trust telemetry:
- Permission Violation (P in {0.0, 1.0})
- Behavioral Deviation (B in [0.0, 1.0])
- Resource Sensitivity (S in [0.1, 1.0])
- Action Criticality (C in [0.1, 1.0])

Latency target: < 5ms.
"""

import time
import logging
from typing import Dict, Any, Optional, Union

from app.services.rbac_engine import rbac_engine
from app.context.behavioral import behavioral_tracker
from app.context.resource_sensitivity import evaluate_resource_sensitivity
from app.context.action_criticality import evaluate_action_criticality

logger = logging.getLogger(__name__)


class ContextEngine:
    """Aggregates runtime contextual factors for composite zero-trust risk analysis."""

    def __init__(self):
        self.rbac = rbac_engine
        self.behavior = behavioral_tracker

    def evaluate_context(
        self,
        role: str,
        tool_name: str,
        payload: Union[str, Dict[str, Any], Any],
        session_id: Optional[str] = None,
        preview_only: bool = False,
    ) -> Dict[str, Any]:
        """
        Calculates P, B, S, and C factors in under 5ms.

        Returns:
            Dictionary containing:
            - permission_violation: float (0.0 or 1.0)
            - behavioral_dev: float (0.0 to 1.0)
            - resource_sens: float (0.1 to 1.0)
            - action_crit: float (0.1 to 1.0)
            - latency_ms: float
            - rbac_allowed: bool
            - rbac_review: bool
            - rbac_reason: str
        """
        start_time = time.perf_counter()

        # 1. Permission Violation (P): 0.0 if allowed/review, 1.0 if violation
        rbac_res = self.rbac.check_permission(role=role, tool_name=tool_name)
        p_val = 0.0 if rbac_res.is_allowed else 1.0

        # 2. Behavioral Deviation (B): Sliding window deviation
        b_val = self.behavior.calculate_deviation(
            session_id=session_id,
            role=role,
            current_tool=tool_name,
            preview_only=preview_only,
        )

        # 3. Resource Sensitivity (S): 0.1 to 1.0
        s_val = evaluate_resource_sensitivity(payload)

        # 4. Action Criticality (C): 0.1 to 1.0
        c_val = evaluate_action_criticality(tool_name)

        latency_ms = round((time.perf_counter() - start_time) * 1000, 4)

        return {
            "permission_violation": float(p_val),
            "behavioral_dev": float(b_val),
            "resource_sens": float(s_val),
            "action_crit": float(c_val),
            "latency_ms": latency_ms,
            "rbac_allowed": rbac_res.is_allowed,
            "rbac_review": rbac_res.requires_review,
            "rbac_reason": rbac_res.reason,
        }


# Global singleton instance
context_engine = ContextEngine()
