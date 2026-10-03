"""
AEGIS-NET LangGraph Multi-Agent Workflow.
Compiles the Researcher → Coder → Deployer StateGraph with:
 - Conditional cancellation edges after each node
 - Hard guard preventing Deployer execution if cancellation_token is set
"""
import logging
from langgraph.graph import StateGraph, END

from app.agents.state import AgentExecutionState, CANCEL_TOKEN
from app.agents.researcher import researcher_node
from app.agents.coder import coder_node
from app.agents.deployer import deployer_node

logger = logging.getLogger(__name__)


def _should_cancel(state: AgentExecutionState) -> str:
    """
    Conditional edge router.
    Returns "cancel" if the cancellation token is set, else "continue".
    This is evaluated after EVERY agent node to prevent deadlocks.
    """
    if state.get("cancellation_token") == CANCEL_TOKEN:
        logger.info(f"[GRAPH ROUTER] Cancellation token detected — routing to END. Reason: {state.get('cancellation_reason')}")
        return "cancel"
    return "continue"


def build_graph() -> StateGraph:
    """Construct and compile the AEGIS-NET multi-agent StateGraph."""
    workflow = StateGraph(AgentExecutionState)

    # Register agent nodes
    workflow.add_node("researcher", researcher_node)
    workflow.add_node("coder", coder_node)
    workflow.add_node("deployer", deployer_node)

    # Entry point
    workflow.set_entry_point("researcher")

    # Researcher → [cancel → END | continue → Coder]
    workflow.add_conditional_edges(
        "researcher",
        _should_cancel,
        {
            "cancel": END,
            "continue": "coder",
        },
    )

    # Coder → [cancel → END | continue → Deployer]
    workflow.add_conditional_edges(
        "coder",
        _should_cancel,
        {
            "cancel": END,
            "continue": "deployer",
        },
    )

    # Deployer → END (always terminates)
    workflow.add_edge("deployer", END)

    return workflow.compile()


# Compiled graph singleton — instantiated once at module load
aegis_graph = build_graph()
