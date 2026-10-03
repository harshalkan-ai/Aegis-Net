"""
AEGIS-NET Deployer Agent Node.
Deploys code artifacts through the AEGIS security gateway.
This node must NEVER execute if cancellation_token is set.
"""
import logging
from app.agents.state import AgentExecutionState, CANCEL_TOKEN
from app.schemas.security import ToolCallEnvelope
from app.proxy.gateway import security_gateway
from app.core.constants import Decision

logger = logging.getLogger(__name__)

DEPLOYER_TOOL = "deploy_service"


def deployer_node(state: AgentExecutionState) -> AgentExecutionState:
    """
    Deployer agent node.
    Executes 'deploy_service' for the generated code artifact.
    Upstream cancellation token check is the primary guard.
    """
    # Hard gate: cancellation_token must abort deployment with zero side-effects
    if state.get("cancellation_token") == CANCEL_TOKEN:
        logger.warning("[DEPLOYER] Cancellation token detected — deployment SKIPPED. Zero deadlock.")
        return state

    if not state.get("generated_code"):
        logger.error("[DEPLOYER] No generated_code available — aborting.")
        return {
            **state,
            "cancellation_token": CANCEL_TOKEN,
            "cancellation_reason": "Deployer: missing generated_code from Coder.",
            "status": "CANCELLED",
        }

    logger.info("[DEPLOYER] Initiating deployment through AEGIS gateway...")

    from app.services.session_manager import session_manager
    session_manager.update_session_role(state["session_id"], "DEPLOYER")
    envelope = ToolCallEnvelope(
        session_id=state["session_id"],
        agent_id=state["agent_id_deployer"],
        tool_name=DEPLOYER_TOOL,
        payload={
            "artifact": "generated_solution.py",
            "target": "production",
            "content_preview": state["generated_code"][:200],
        },
    )

    result = security_gateway.intercept_tool_call(envelope, raise_on_block=False)

    gw_results = dict(state.get("gateway_results") or {})
    gw_results["deployer"] = {
        "decision": result.decision,
        "reason": result.reason,
        "latency_ms": result.execution_latency_ms,
        "envelope_token": result.envelope_token,
    }

    if result.decision == Decision.BLOCK.value:
        logger.warning(f"[DEPLOYER] Gateway BLOCKED. Tripping circuit breaker. Reason: {result.reason}")
        from app.containment.circuit_breaker import circuit_breaker
        circuit_breaker.trip(
            session_id=state["session_id"],
            reason=f"Deployer BLOCKED by gateway: {result.reason}",
        )
        return {
            **state,
            "cancellation_token": CANCEL_TOKEN,
            "cancellation_reason": f"Deployer blocked — circuit breaker tripped: {result.reason}",
            "status": "CANCELLED",
            "gateway_results": gw_results,
        }

    # Simulate deployment receipt
    deployment_receipt = (
        f"[DEPLOYMENT RECEIPT]\n"
        f"Status: SUCCESS\n"
        f"Artifact: generated_solution.py\n"
        f"Target: production\n"
        f"Agent: {state['agent_id_deployer']}\n"
        f"Gateway token: {result.envelope_token}"
    )

    logger.info("[DEPLOYER] Deployment completed successfully.")
    return {
        **state,
        "deployment_receipt": deployment_receipt,
        "status": "COMPLETED",
        "gateway_results": gw_results,
    }
