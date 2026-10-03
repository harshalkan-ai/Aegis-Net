"""
AEGIS-NET Coder Agent Node.
<<<<<<< HEAD
Generates code artifacts through the AEGIS security gateway and writes them to the sandboxed workspace.
All tool invocations pass through SecurityGateway.intercept_tool_call().
"""
import json
=======
Generates code from research notes through the AEGIS security gateway.
On BLOCK: trips the circuit breaker, sets cancellation token.
"""
>>>>>>> 30aea8107e52fc279ef4176b187de31f143d2e0c
import logging
from app.agents.state import AgentExecutionState, CANCEL_TOKEN
from app.schemas.security import ToolCallEnvelope
from app.proxy.gateway import security_gateway
<<<<<<< HEAD
from app.core.constants import Decision
from app.containment.circuit_breaker import circuit_breaker
=======
from app.containment.circuit_breaker import circuit_breaker
from app.core.constants import Decision
>>>>>>> 30aea8107e52fc279ef4176b187de31f143d2e0c

logger = logging.getLogger(__name__)

CODER_TOOL = "write_workspace_file"


def coder_node(state: AgentExecutionState) -> AgentExecutionState:
    """
    Coder agent node.
<<<<<<< HEAD
    Calls 'write_workspace_file' through the security gateway.
    On BLOCK: trips circuit breaker, sets cancellation_token, aborts downstream.
    """
    # Propagate any upstream cancellation immediately
    if state.get("cancellation_token") == CANCEL_TOKEN:
        logger.warning("[CODER] Cancellation token detected — node SKIPPED. Zero deadlock.")
=======
    Uses research_notes to generate code via 'write_workspace_file'.
    On BLOCK: trips circuit breaker + cancels downstream Deployer.
    """
    # Propagate upstream cancellation
    if state.get("cancellation_token") == CANCEL_TOKEN:
>>>>>>> 30aea8107e52fc279ef4176b187de31f143d2e0c
        return state

    if not state.get("research_notes"):
        logger.error("[CODER] No research_notes available — aborting.")
        return {
            **state,
            "cancellation_token": CANCEL_TOKEN,
            "cancellation_reason": "Coder: missing research_notes from Researcher.",
            "status": "CANCELLED",
        }

    logger.info("[CODER] Generating code from research notes...")

<<<<<<< HEAD
    from app.services.session_manager import session_manager
    session_manager.update_session_role(state["session_id"], "CODER")

=======
<<<<<<< HEAD
    from app.services.session_manager import session_manager
    session_manager.update_session_role(state["session_id"], "CODER")

=======
>>>>>>> 269c4536791406ae7200b6f0aced48c638234a60
>>>>>>> 30aea8107e52fc279ef4176b187de31f143d2e0c
    envelope = ToolCallEnvelope(
        session_id=state["session_id"],
        agent_id=state["agent_id_coder"],
        tool_name=CODER_TOOL,
        payload={
            "file_path": "generated_solution.py",
            "content": state["input_query"],  # payload includes user input for ML analysis
        },
    )

    result = security_gateway.intercept_tool_call(envelope, raise_on_block=False)

    gw_results = dict(state.get("gateway_results") or {})
    gw_results["coder"] = {
        "decision": result.decision,
        "reason": result.reason,
        "latency_ms": result.execution_latency_ms,
        "envelope_token": result.envelope_token,
    }

    if result.decision == Decision.BLOCK.value:
        logger.warning(f"[CODER] Gateway BLOCKED. Tripping circuit breaker. Reason: {result.reason}")

        # Trip circuit breaker — Deployer must not run
        circuit_breaker.trip(
            session_id=state["session_id"],
            reason=f"Coder BLOCKED by gateway: {result.reason}",
        )
        from app.containment.quarantine import quarantine_engine
        quarantine_engine.quarantine(
            session_id=state["session_id"],
            agent_id=state["agent_id_coder"],
            reason=f"Coder BLOCKED: {result.reason}",
        )

        return {
            **state,
            "cancellation_token": CANCEL_TOKEN,
            "cancellation_reason": f"Coder blocked — circuit breaker tripped: {result.reason}",
            "status": "CANCELLED",
            "gateway_results": gw_results,
        }

<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> 30aea8107e52fc279ef4176b187de31f143d2e0c
    # Write actual files into the sandboxed session workspace upon ALLOW
    from app.containment.sandbox import sandbox_write_file

    session_id = state["session_id"]
    code_content = (
        f"# Auto-generated solution for session {session_id}\n"
        f"# Based on input query: {state['input_query']}\n\n"
        f"def authenticate_user(username: str, token: str) -> bool:\n"
        f"    \"\"\"Enforce zero-trust token validation.\"\"\"\n"
        f"    if not username or not token:\n"
        f"        return False\n"
        f"    return token.startswith('bearer-valid-')\n\n"
        f"if __name__ == '__main__':\n"
        f"    print('Auth service ready. Session token: {result.envelope_token}')\n"
    )

    readme_content = (
        f"# Workspace Artifacts — Session {session_id}\n\n"
        f"**User Requirement**: {state['input_query']}\n\n"
        f"## Structure\n"
        f"- `project/main.py`: Primary application entrypoint.\n"
        f"- `research/findings.md`: Research findings compiled from Tavily.\n"
        f"- `security/security-report.json`: Gatekeeper security audit.\n"
    )

    findings_content = state.get("research_notes", "No research notes generated.")

<<<<<<< HEAD
=======
    import json
>>>>>>> 30aea8107e52fc279ef4176b187de31f143d2e0c
    security_report = json.dumps({
        "session_id": session_id,
        "agent": "CODER",
        "decision": result.decision,
        "token": result.envelope_token,
        "latency_ms": result.execution_latency_ms,
        "risk": result.risk_assessment,
    }, indent=2)

    sandbox_write_file("README.md", readme_content, session_id=session_id)
    sandbox_write_file("project/main.py", code_content, session_id=session_id)
    sandbox_write_file("research/findings.md", findings_content, session_id=session_id)
    sandbox_write_file("security/security-report.json", security_report, session_id=session_id)

    logger.info(f"[CODER] Completed. Generated workspace files for session {session_id}.")
    return {
        **state,
        "generated_code": code_content,
<<<<<<< HEAD
=======
=======
    # Simulate code generation output
    generated_code = (
        f"# Generated by AEGIS-NET Coder Agent\n"
        f"# Based on research: {state['research_notes'][:120]}...\n\n"
        f"def solution():\n"
        f"    \"\"\"Auto-generated solution implementing zero-trust security patterns.\"\"\"\n"
        f"    pass  # Implementation expanded from research findings\n\n"
        f"# Gateway token: {result.envelope_token}"
    )

    logger.info("[CODER] Completed. Code artifact generated.")
    return {
        **state,
        "generated_code": generated_code,
>>>>>>> 269c4536791406ae7200b6f0aced48c638234a60
>>>>>>> 30aea8107e52fc279ef4176b187de31f143d2e0c
        "status": "RUNNING",
        "gateway_results": gw_results,
    }
