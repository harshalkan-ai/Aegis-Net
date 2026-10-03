"""
AEGIS-NET Researcher Agent Node.
<<<<<<< HEAD
Performs real web research (web search / doc retrieval) via Tavily through the AEGIS gateway.
=======
Performs simulated research (web search / doc retrieval) through the AEGIS gateway.
>>>>>>> 30aea8107e52fc279ef4176b187de31f143d2e0c
All tool invocations pass through SecurityGateway.intercept_tool_call().
"""
import logging
from app.agents.state import AgentExecutionState, CANCEL_TOKEN
from app.schemas.security import ToolCallEnvelope
from app.proxy.gateway import security_gateway
from app.core.constants import Decision

logger = logging.getLogger(__name__)

RESEARCHER_TOOL = "search_docs"


def researcher_node(state: AgentExecutionState) -> AgentExecutionState:
    """
    Researcher agent node.
    Calls 'search_docs' through the security gateway.
    On BLOCK: sets cancellation_token and short-circuits the graph.
    """
    # Propagate any upstream cancellation immediately
    if state.get("cancellation_token") == CANCEL_TOKEN:
        return state

<<<<<<< HEAD
    logger.info(f"[RESEARCHER] Processing research task: {state['input_query'][:80]!r}")
=======
<<<<<<< HEAD
    logger.info(f"[RESEARCHER] Processing research task: {state['input_query'][:80]!r}")
=======
    logger.info(f"[RESEARCHER] Processing query: {state['input_query'][:80]!r}")
>>>>>>> 269c4536791406ae7200b6f0aced48c638234a60
>>>>>>> 30aea8107e52fc279ef4176b187de31f143d2e0c

    envelope = ToolCallEnvelope(
        session_id=state["session_id"],
        agent_id=state["agent_id_researcher"],
        tool_name=RESEARCHER_TOOL,
        payload={"query": state["input_query"]},
    )

    result = security_gateway.intercept_tool_call(envelope, raise_on_block=False)

    # Record gateway result
    gw_results = dict(state.get("gateway_results") or {})
    gw_results["researcher"] = {
        "decision": result.decision,
        "reason": result.reason,
        "latency_ms": result.execution_latency_ms,
        "envelope_token": result.envelope_token,
<<<<<<< HEAD
        "risk_assessment": result.risk_assessment,
=======
<<<<<<< HEAD
        "risk_assessment": result.risk_assessment,
=======
>>>>>>> 269c4536791406ae7200b6f0aced48c638234a60
>>>>>>> 30aea8107e52fc279ef4176b187de31f143d2e0c
    }

    if result.decision == Decision.BLOCK.value:
        logger.warning(f"[RESEARCHER] Gateway BLOCKED. Tripping circuit breaker. Reason: {result.reason}")
        from app.containment.circuit_breaker import circuit_breaker
        from app.containment.quarantine import quarantine_engine
        circuit_breaker.trip(
            session_id=state["session_id"],
            reason=f"Researcher BLOCKED by gateway: {result.reason}",
        )
        quarantine_engine.quarantine(
            session_id=state["session_id"],
            agent_id=state["agent_id_researcher"],
            reason=f"Researcher BLOCKED: {result.reason}",
        )
        return {
            **state,
            "cancellation_token": CANCEL_TOKEN,
            "cancellation_reason": f"Researcher blocked — circuit breaker tripped: {result.reason}",
            "status": "CANCELLED",
            "gateway_results": gw_results,
        }

<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> 30aea8107e52fc279ef4176b187de31f143d2e0c
    # Execute real Tavily web research
    from app.services.tavily_client import perform_tavily_search
    tavily_res = perform_tavily_search(state["input_query"])
    
    summary = tavily_res.get("summary", "")
    sources = tavily_res.get("sources", [])

    sources_formatted = "\n".join([
        f"- [{s.get('title', 'Source')}]({s.get('url', '')}): {s.get('content', '')[:150]}"
        for s in sources
    ]) if sources else "No external web sources retrieved."

    research_notes = (
        f"# RESEARCH FINDINGS & SPECIFICATION\n\n"
        f"**Task**: {state['input_query']}\n\n"
        f"**Summary**:\n{summary}\n\n"
        f"**Verified Sources ({len(sources)})**:\n{sources_formatted}\n\n"
        f"**Security Evaluation**: Decision = {result.decision} | Token = {result.envelope_token}"
    )

    logger.info(f"[RESEARCHER] Completed. Retrieved {len(sources)} sources from Tavily.")
<<<<<<< HEAD
=======
=======
    # Simulate research output when allowed
    research_notes = (
        f"[RESEARCHER OUTPUT]\n"
        f"Query: {state['input_query']}\n"
        f"Summary: Retrieved 12 relevant documents on the topic. "
        f"Key findings: security best practices, zero-trust architecture patterns, "
        f"and regulatory compliance frameworks identified.\n"
        f"Gateway token: {result.envelope_token}"
    )

    logger.info("[RESEARCHER] Completed. Research notes generated.")
>>>>>>> 269c4536791406ae7200b6f0aced48c638234a60
>>>>>>> 30aea8107e52fc279ef4176b187de31f143d2e0c
    return {
        **state,
        "research_notes": research_notes,
        "status": "RUNNING",
        "gateway_results": gw_results,
<<<<<<< HEAD
        "tavily_sources": sources,
=======
<<<<<<< HEAD
        "tavily_sources": sources,
=======
>>>>>>> 269c4536791406ae7200b6f0aced48c638234a60
>>>>>>> 30aea8107e52fc279ef4176b187de31f143d2e0c
    }
