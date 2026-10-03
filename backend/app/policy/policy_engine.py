"""
AEGIS-NET Policy Decision Engine.
Evaluates composite risk from risk_scorer.py against context factors
and enforces mandatory override rules.
"""
import logging
from typing import Dict, Any
from app.schemas.policy import PolicyDecision, DecisionExplanation

logger = logging.getLogger(__name__)


def evaluate_policy(risk_result: Dict[str, Any], context: Dict[str, Any]) -> PolicyDecision:
    """
    Evaluate policy decision from risk_result and context factors.

    Mandatory override order:
    1. Hard permission violation (P=1.0) → immediate BLOCK
    2. Neural threat score >= 0.80 → immediate BLOCK
    3. Aggregate risk >= 0.60 → BLOCK
    4. 0.30 <= risk < 0.60 → REVIEW
    5. Default → ALLOW
    """
    score = risk_result["total_risk"]
    threat = risk_result.get("threat_score", 0.0)
    reasons: list[str] = []
    mandatory_override = False

    # --- Mandatory Override 1: Hard RBAC permission violation ---
    if context.get("permission_violation", 0.0) == 1.0:
        reasons.append("Unauthorized tool access for current role.")
        mandatory_override = True
        return PolicyDecision(
            decision="BLOCK",
            reasons=reasons,
            risk_score=score,
            threat_score=threat,
            mandatory_override=mandatory_override,
        )

    # --- Mandatory Override 2: High-confidence prompt injection ---
    if threat >= 0.80:
        reasons.append(
            f"High-confidence prompt injection vector detected (threat={threat:.4f})."
        )
        mandatory_override = True
        return PolicyDecision(
            decision="BLOCK",
            reasons=reasons,
            risk_score=score,
            threat_score=threat,
            mandatory_override=mandatory_override,
        )

    # --- Risk Threshold Evaluation ---
    if score >= 0.60:
        reasons.append(
            f"Aggregate risk score ({score:.4f}) exceeds block threshold (0.60)."
        )
        return PolicyDecision(
            decision="BLOCK",
            reasons=reasons,
            risk_score=score,
            threat_score=threat,
            mandatory_override=False,
        )

    if 0.30 <= score < 0.60:
        reasons.append(
            f"Elevated risk score ({score:.4f}) requires security analyst review."
        )
        if context.get("rbac_review", False):
            reasons.append("Tool is additionally flagged as requiring supervised execution.")
        return PolicyDecision(
            decision="REVIEW",
            reasons=reasons,
            risk_score=score,
            threat_score=threat,
            mandatory_override=False,
        )

    # --- Default ALLOW ---
    reasons.append("Risk parameters within acceptable limits.")
    if context.get("rbac_review", False):
        reasons.append("Note: Tool requires review flag per role policy — elevated monitoring active.")
        return PolicyDecision(
            decision="REVIEW",
            reasons=reasons,
            risk_score=score,
            threat_score=threat,
            mandatory_override=False,
        )

    return PolicyDecision(
        decision="ALLOW",
        reasons=reasons,
        risk_score=score,
        threat_score=threat,
        mandatory_override=False,
    )


def build_explanation(
    policy: PolicyDecision,
    risk_result: Dict[str, Any],
    context: Dict[str, Any],
) -> DecisionExplanation:
    """Builds a structured DecisionExplanation from policy + raw data."""
    return DecisionExplanation(
        decision=policy.decision,
        reasons=policy.reasons,
        risk_score=policy.risk_score,
        threat_score=policy.threat_score,
        mandatory_override=policy.mandatory_override,
        factors=risk_result.get("factors", {}),
        context={
            "permission_violation": context.get("permission_violation", 0.0),
            "behavioral_dev": context.get("behavioral_dev", 0.0),
            "resource_sens": context.get("resource_sens", 0.0),
            "action_crit": context.get("action_crit", 0.0),
            "rbac_allowed": context.get("rbac_allowed", True),
            "rbac_review": context.get("rbac_review", False),
        },
    )
