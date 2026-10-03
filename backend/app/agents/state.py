"""
AEGIS-NET LangGraph Agent State Schema.
Shared TypedDict passed through every node of the multi-agent workflow.
"""
from typing import Optional
from typing_extensions import TypedDict

CANCEL_TOKEN = "__AEGIS_CANCEL__"


class AgentExecutionState(TypedDict):
    """
    Shared workflow state passed between Researcher → Coder → Deployer nodes.

    Fields:
        session_id          : Active AEGIS session UUID bound to this run.
        agent_id_researcher : Agent ID for the Researcher role.
        agent_id_coder      : Agent ID for the Coder role.
        agent_id_deployer   : Agent ID for the Deployer role.
        input_query         : Original user prompt driving the workflow.
        research_notes      : Output from the Researcher node.
        generated_code      : Output from the Coder node.
        deployment_receipt  : Output from the Deployer node.
        cancellation_token  : Set to CANCEL_TOKEN ("__AEGIS_CANCEL__") when gateway blocks.
        cancellation_reason : Human-readable reason for cancellation.
        status              : Workflow terminal status: COMPLETED | CANCELLED | RUNNING.
        gateway_results     : Per-node gateway interception results (for audit trail).
    """
    session_id: str
    agent_id_researcher: str
    agent_id_coder: str
    agent_id_deployer: str
    input_query: str
    research_notes: Optional[str]
    generated_code: Optional[str]
    deployment_receipt: Optional[str]
    cancellation_token: Optional[str]
    cancellation_reason: Optional[str]
    status: str
    gateway_results: Optional[dict]
