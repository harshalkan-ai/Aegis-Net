"""
AEGIS-NET Security Proxy Gateway.
The authoritative synchronous enforcement boundary that intercepts and assesses all tool invocations
before runtime execution.
"""

from datetime import datetime, timezone
import json
import logging
import time
from typing import Optional, Dict, Any, Callable
import uuid

from app.core.constants import Decision, ToolCallStatus, SecurityEventType, IncidentSeverity
from app.schemas.security import ToolCallEnvelope, ProxyInterceptionResult
from app.proxy.exceptions import (
    SecurityProxyBlockException,
    SecurityProxyReviewException,
    SessionQuarantinedException,
    SessionNotFoundException,
    PolicyViolationException,
)
from app.services.session_manager import session_manager
from app.context.context_engine import context_engine
from app.models.risk_scorer import calculate_risk
from app.policy.policy_engine import evaluate_policy, build_explanation
from app.services.supabase_client import get_supabase_client
from app.audit.audit_service import audit_service
from app.incidents.incident_service import incident_service

logger = logging.getLogger(__name__)


class SecurityGateway:
    """Zero-Trust Security Gateway and Tool-Call Interceptor."""

    def __init__(self):
        self.context = context_engine
        self.sessions = session_manager

    def intercept_tool_call(
        self,
        envelope: ToolCallEnvelope,
        tool_executor: Optional[Callable[[Dict[str, Any]], Any]] = None,
        raise_on_block: bool = False,
    ) -> ProxyInterceptionResult:
        """
        Main gatekeeper method.
        Intercepts tool call, evaluates session, context, and ML risk, enforcing tri-state policy.

        Returns:
            ProxyInterceptionResult containing envelope token, decision, latency, and status.
        """
        start_time = time.perf_counter()
        envelope_token = f"tok-{uuid.uuid4()}"
        tool_call_id = str(uuid.uuid4())
        now_utc = datetime.now(timezone.utc).isoformat()

        # Step 1: Session Validation & State Check
        session = self.sessions.get_session(envelope.session_id)
        if not session:
            err_msg = f"Session '{envelope.session_id}' not found or invalid."
            logger.warning(err_msg)
            if raise_on_block:
                raise SessionNotFoundException(err_msg)
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return ProxyInterceptionResult(
                envelope_token=envelope_token,
                session_id=envelope.session_id,
                agent_id=envelope.agent_id,
                tool_name=envelope.tool_name,
                decision=Decision.BLOCK.value,
                is_executed=False,
                execution_latency_ms=latency_ms,
                status=ToolCallStatus.REJECTED.value,
                reason=err_msg,
            )

        if session.status == "QUARANTINED":
            err_msg = f"Agent '{envelope.agent_id}' is QUARANTINED. All tool invocations are prohibited."
            logger.warning(err_msg)
            if raise_on_block:
                raise SessionQuarantinedException(err_msg)
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return ProxyInterceptionResult(
                envelope_token=envelope_token,
                session_id=envelope.session_id,
                agent_id=envelope.agent_id,
                tool_name=envelope.tool_name,
                decision=Decision.BLOCK.value,
                is_executed=False,
                execution_latency_ms=latency_ms,
                status=ToolCallStatus.REJECTED.value,
                reason=err_msg,
            )

        role = session.role

        # Step 2: Extract payload text for ML threat analysis
        payload_str = (
            json.dumps(envelope.payload)
            if isinstance(envelope.payload, dict)
            else str(envelope.payload)
        )

        # Step 3: Forward to Context Engine (P, B, S, C)
        ctx = self.context.evaluate_context(
            role=role,
            tool_name=envelope.tool_name,
            payload=envelope.payload,
            session_id=envelope.session_id,
        )

        # Step 4: ML Threat Analysis & Multi-factor Composite Risk
        risk_result = calculate_risk(
            payload=payload_str,
            permission_violation=ctx["permission_violation"],
            behavioral_dev=ctx["behavioral_dev"],
            resource_sens=ctx["resource_sens"],
            action_crit=ctx["action_crit"],
        )

        # Step 4b: Route through Policy Engine for structured decision + mandatory overrides
        policy = evaluate_policy(risk_result, ctx)
        explanation = build_explanation(policy, risk_result, ctx)
        decision = policy.decision
        decision_reason = " | ".join(policy.reasons)

        # Step 5: Tri-State Routing
        is_executed = False
        execution_output = None
        call_status = ToolCallStatus.PENDING.value

        if decision == Decision.ALLOW.value:
            call_status = ToolCallStatus.APPROVED.value
            # Execute tool safely
            if tool_executor is not None:
                try:
                    execution_output = tool_executor(envelope.payload)
                    is_executed = True
                    call_status = ToolCallStatus.EXECUTED.value
                except Exception as ex:
                    logger.error(f"Error executing tool '{envelope.tool_name}': {ex}")
                    execution_output = {"error": str(ex)}
                    call_status = ToolCallStatus.FAILED.value
            else:
                # Default success when no external runner is supplied
                is_executed = True
                execution_output = {"status": "success", "tool": envelope.tool_name, "token": envelope_token}
                call_status = ToolCallStatus.EXECUTED.value

            self.sessions.record_tool_call(envelope.session_id)

        elif decision == Decision.REVIEW.value:
            call_status = ToolCallStatus.PENDING.value
            is_executed = False
            logger.info(f"Tool invocation '{envelope.tool_name}' held for administrative review.")

        else:  # BLOCK
            call_status = ToolCallStatus.REJECTED.value
            is_executed = False
            logger.warning(
                f"[SECURITY BLOCK] Tool '{envelope.tool_name}' for agent '{envelope.agent_id}' BLOCKED. Reason: {decision_reason}"
            )
            if raise_on_block:
                raise SecurityProxyBlockException(
                    message=f"Access Denied: {decision_reason}",
                    details={
                        "envelope_token": envelope_token,
                        "session_id": envelope.session_id,
                        "tool_name": envelope.tool_name,
                        "risk_assessment": risk_result,
                    },
                )

        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

        # Step 6: Telemetry & Asynchronous Supabase Persistence
        self._record_telemetry(
            tool_call_id=tool_call_id,
            envelope=envelope,
            decision=decision,
            status=call_status,
            risk_result=risk_result,
            now_utc=now_utc,
            envelope_token=envelope_token,
        )

        return ProxyInterceptionResult(
            envelope_token=envelope_token,
            session_id=envelope.session_id,
            agent_id=envelope.agent_id,
            tool_name=envelope.tool_name,
            decision=decision,
            risk_assessment=risk_result,
            is_executed=is_executed,
            execution_result=execution_output,
            execution_latency_ms=latency_ms,
            status=call_status,
            reason=decision_reason,
        )

    def _record_telemetry(
        self,
        tool_call_id: str,
        envelope: ToolCallEnvelope,
        decision: str,
        status: str,
        risk_result: Dict[str, Any],
        now_utc: str,
        envelope_token: str,
    ) -> None:
        """Persists raw tool_call + risk_assessment synchronously, delegates incident/audit to services."""
        try:
            client = get_supabase_client()

            # 1. Insert Tool Call record
            client.table("tool_calls").insert({
                "id": tool_call_id,
                "session_id": envelope.session_id,
                "agent_id": envelope.agent_id,
                "tool_name": envelope.tool_name,
                "payload": envelope.payload if isinstance(envelope.payload, dict) else {"content": str(envelope.payload)},
                "status": status,
                "created_at": now_utc,
            }).execute()

            # 2. Insert Risk Assessment
            client.table("risk_assessments").insert({
                "tool_call_id": tool_call_id,
                "threat_score": risk_result["threat_score"],
                "total_risk": risk_result["total_risk"],
                "decision": decision,
                "factors": risk_result.get("factors", {}),
                "created_at": now_utc,
            }).execute()

        except Exception as e:
            logger.debug(f"Telemetry raw write note: {e}")

        # 3. If BLOCKED — delegate to IncidentService (auto-severity ladder + Realtime emit)
        if decision == Decision.BLOCK.value:
            try:
                incident_service.create_incident(
                    agent_id=envelope.agent_id,
                    session_id=envelope.session_id,
                    tool_call_id=tool_call_id,
                    risk_score=risk_result["total_risk"],
                    threat_score=risk_result["threat_score"],
                    decision=decision,
                    reasons=[f"Blocked by AEGIS policy — risk={risk_result['total_risk']:.4f}"],
                    tool_name=envelope.tool_name,
                    role=session.role if session else "UNKNOWN",
                    payload=envelope.payload,
                    permission_score=risk_result.get("factors", {}).get("permission_violation", 0.0),
                    behavioral_score=risk_result.get("factors", {}).get("behavioral_dev", 0.0),
                    sensitivity_score=risk_result.get("factors", {}).get("resource_sens", 0.0),
                    criticality_score=risk_result.get("factors", {}).get("action_crit", 0.0),
                    circuit_breaker_triggered=False,
                )
            except Exception as e:
                logger.debug(f"Incident creation note: {e}")

        # 4. Non-blocking audit log (fire-and-forget daemon thread)
        audit_service.log(
            event_name=f"TOOL_INTERCEPT_{decision}",
            actor=envelope.agent_id,
            payload={
                "envelope_token": envelope_token,
                "session_id": envelope.session_id,
                "tool_name": envelope.tool_name,
                "tool_call_id": tool_call_id,
                "decision": decision,
                "status": status,
                "risk_score": risk_result["total_risk"],
                "threat_score": risk_result["threat_score"],
            },
        )


# Global singleton instance
security_gateway = SecurityGateway()
