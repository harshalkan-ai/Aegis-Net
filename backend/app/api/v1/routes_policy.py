"""
AEGIS-NET Policy API Routes.
Exposes policy evaluation as a standalone endpoint for diagnostics and audit.
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Union, Dict, Any

from app.schemas.policy import DecisionExplanation
from app.schemas.security import ContextEvaluationRequest
from app.context.context_engine import context_engine
from app.models.risk_scorer import calculate_risk
from app.policy.policy_engine import evaluate_policy, build_explanation

router = APIRouter(prefix="/policy", tags=["Policy Engine"])


class PolicyEvaluationRequest(BaseModel):
    role: str
    tool_name: str
    payload: Union[Dict[str, Any], str] = ""
    session_id: str = ""


@router.post(
    "/evaluate",
    response_model=DecisionExplanation,
    summary="Full Policy Pipeline Evaluation",
    description="Runs Context Engine → ML Threat Score → Risk Scorer → Policy Engine and returns a structured decision.",
)
async def evaluate_policy_endpoint(req: PolicyEvaluationRequest):
    """End-to-end policy evaluation pipeline."""
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
    return build_explanation(policy, risk_result, ctx)
