"""
AEGIS-NET Security Proxy API Routes.
Exposes endpoints for intercepted tool invocations and enforcement results.
"""

from fastapi import APIRouter, HTTPException, status, Query
from app.schemas.security import ToolCallEnvelope, ProxyInterceptionResult
from app.proxy.gateway import security_gateway
from app.proxy.exceptions import (
    SecurityProxyBlockException,
    SessionQuarantinedException,
    SessionNotFoundException,
)

router = APIRouter(prefix="/proxy", tags=["Security Proxy"])


@router.post(
    "/intercept",
    response_model=ProxyInterceptionResult,
    summary="Intercept and Authorize Tool Invocation",
    description="Primary ingress boundary for all runtime tool operations. Validates session, RBAC policy, and ML risk.",
)
async def intercept_tool_call(
    envelope: ToolCallEnvelope,
    raise_on_block: bool = Query(default=False, description="Whether to raise HTTP 403 on policy block"),
):
    """Intercept tool invocation before execution."""
    try:
        result = security_gateway.intercept_tool_call(
            envelope=envelope,
            raise_on_block=raise_on_block,
        )

        if raise_on_block and result.decision == "BLOCK":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "message": "Tool invocation blocked by Zero-Trust Security Proxy.",
                    "envelope_token": result.envelope_token,
                    "reason": result.reason,
                    "risk_assessment": result.risk_assessment,
                },
            )

        return result

    except SessionNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except SessionQuarantinedException as e:
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=str(e),
        )
    except SecurityProxyBlockException as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"message": e.message, "details": e.details},
        )
