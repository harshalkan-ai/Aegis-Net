"""
AEGIS-NET Policy API Routes.
Exposes policy evaluation as a standalone endpoint for diagnostics and audit.
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> 30aea8107e52fc279ef4176b187de31f143d2e0c
BLOCK and REVIEW decisions automatically create security incidents with Gemini forensic analysis.
"""
import uuid
import logging
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Union, Dict, Any, Optional
<<<<<<< HEAD
=======
=======
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Union, Dict, Any
>>>>>>> 269c4536791406ae7200b6f0aced48c638234a60
>>>>>>> 30aea8107e52fc279ef4176b187de31f143d2e0c

from app.schemas.policy import DecisionExplanation
from app.schemas.security import ContextEvaluationRequest
from app.context.context_engine import context_engine
from app.models.risk_scorer import calculate_risk
from app.policy.policy_engine import evaluate_policy, build_explanation
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> 30aea8107e52fc279ef4176b187de31f143d2e0c
from app.incidents.incident_service import incident_service

router = APIRouter(prefix="/policy", tags=["Policy Engine"])
logger = logging.getLogger(__name__)
<<<<<<< HEAD
=======
=======

router = APIRouter(prefix="/policy", tags=["Policy Engine"])
>>>>>>> 269c4536791406ae7200b6f0aced48c638234a60
>>>>>>> 30aea8107e52fc279ef4176b187de31f143d2e0c


class PolicyEvaluationRequest(BaseModel):
    role: str
    tool_name: str
    payload: Union[Dict[str, Any], str] = ""
    session_id: str = ""
<<<<<<< HEAD
    agent_id: str = "agent-gateway-01"
=======
<<<<<<< HEAD
    agent_id: str = "agent-gateway-01"
=======
>>>>>>> 269c4536791406ae7200b6f0aced48c638234a60
>>>>>>> 30aea8107e52fc279ef4176b187de31f143d2e0c


@router.post(
    "/evaluate",
    response_model=DecisionExplanation,
    summary="Full Policy Pipeline Evaluation",
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> 30aea8107e52fc279ef4176b187de31f143d2e0c
    description=(
        "Runs Context Engine → ML Threat Score → Risk Scorer → Policy Engine and returns a structured decision. "
        "BLOCK decisions automatically create a Security Incident with Gemini CISO forensic analysis. "
        "REVIEW decisions create an investigation record."
    ),
)
async def evaluate_policy_endpoint(req: PolicyEvaluationRequest):
    """End-to-end policy evaluation pipeline — incidents auto-created on BLOCK/REVIEW."""
<<<<<<< HEAD
=======
=======
    description="Runs Context Engine → ML Threat Score → Risk Scorer → Policy Engine and returns a structured decision.",
)
async def evaluate_policy_endpoint(req: PolicyEvaluationRequest):
    """End-to-end policy evaluation pipeline."""
>>>>>>> 269c4536791406ae7200b6f0aced48c638234a60
>>>>>>> 30aea8107e52fc279ef4176b187de31f143d2e0c
    ctx = context_engine.evaluate_context(
        role=req.role,
        tool_name=req.tool_name,
        payload=req.payload,
        session_id=req.session_id or None,
        preview_only=True,
    )

    payload_str = req.payload if isinstance(req.payload, str) else str(req.payload)

    risk_result = calculate_risk(
        payload=payload_str,
        permission_violation=ctx["permission_violation"],
        behavioral_dev=ctx["behavioral_dev"],
        resource_sens=ctx["resource_sens"],
        action_crit=ctx["action_crit"],
    )

    policy = evaluate_policy(risk_result, ctx)
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> 30aea8107e52fc279ef4176b187de31f143d2e0c
    explanation = build_explanation(policy, risk_result, ctx)

    decision = policy.decision

    # Auto-create incident for BLOCK and REVIEW decisions
    if decision in ("BLOCK", "REVIEW"):
        try:
            tool_call_id = str(uuid.uuid4())
            session_id = req.session_id or f"policy-eval-{tool_call_id[:8]}"

            incident_service.create_incident(
                agent_id=req.agent_id,
                session_id=session_id,
                tool_call_id=tool_call_id,
                risk_score=risk_result["total_risk"],
                threat_score=risk_result["threat_score"],
                decision=decision,
                reasons=policy.reasons,
                tool_name=req.tool_name,
                role=req.role,
                payload=req.payload,
                permission_score=ctx.get("permission_violation", 0.0),
                behavioral_score=ctx.get("behavioral_dev", 0.0),
                sensitivity_score=ctx.get("resource_sens", 0.0),
                criticality_score=ctx.get("action_crit", 0.0),
                circuit_breaker_triggered=False,
                prior_tool_calls=0,
            )
            logger.info(
                f"[POLICY] Incident auto-created for {decision} decision: "
                f"tool={req.tool_name}, role={req.role}, risk={risk_result['total_risk']:.4f}"
            )
        except Exception as e:
            logger.error(f"[POLICY] Incident creation failed: {e}")

    return explanation
<<<<<<< HEAD
=======
=======
    return build_explanation(policy, risk_result, ctx)
>>>>>>> 269c4536791406ae7200b6f0aced48c638234a60
>>>>>>> 30aea8107e52fc279ef4176b187de31f143d2e0c
