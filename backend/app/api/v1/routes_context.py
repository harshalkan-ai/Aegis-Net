"""
AEGIS-NET Context Engine API Routes.
Exposes endpoints to compute runtime contextual factors (P, B, S, C).
"""

from fastapi import APIRouter, status
from app.schemas.security import ContextEvaluationRequest, ContextEvaluationResponse
from app.context.context_engine import context_engine

router = APIRouter(prefix="/context", tags=["Context Engine"])


@router.post(
    "/evaluate",
    response_model=ContextEvaluationResponse,
    summary="Evaluate Runtime Context Factors",
    description="Aggregates Permission Violation (P), Behavioral Deviation (B), Resource Sensitivity (S), and Action Criticality (C).",
)
async def evaluate_context(payload: ContextEvaluationRequest):
    """Calculates P, B, S, and C factors for a role and tool invocation."""
    res = context_engine.evaluate_context(
        role=payload.role,
        tool_name=payload.tool_name,
        payload=payload.payload,
        session_id=payload.session_id,
        preview_only=True,
    )
    return ContextEvaluationResponse(**res)
