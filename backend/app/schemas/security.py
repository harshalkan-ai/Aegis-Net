"""
AEGIS-NET Security & Proxy Schemas.
Defines envelopes, interception results, and contextual evaluation structures.
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any, Union
from pydantic import BaseModel, Field


class ToolCallEnvelope(BaseModel):
    """Secure wrapper encapsulating an agent tool invocation request."""
    session_id: str = Field(..., description="UUID of active agent session", examples=["3fa85f64-5717-4562-b3fc-2c963f66afa6"])
    agent_id: str = Field(..., description="Agent identifier", examples=["agent-coder-01"])
    tool_name: str = Field(..., description="Target tool to invoke", examples=["read_workspace_file"])
    payload: Union[Dict[str, Any], str] = Field(..., description="Invocation arguments or payload string")
    timestamp: Optional[str] = Field(default=None, description="Request UTC ISO timestamp")


class ProxyInterceptionResult(BaseModel):
    """Enforcement result returned by the Security Proxy Gateway."""
    envelope_token: str = Field(..., description="Cryptographic/unique token issued by the security gateway")
    session_id: str
    agent_id: str
    tool_name: str
    decision: str = Field(..., description="Tri-state policy decision: ALLOW, REVIEW, BLOCK")
    risk_assessment: Optional[Dict[str, Any]] = Field(default=None, description="Detailed ML risk assessment and factors")
    is_executed: bool = Field(default=False, description="Whether tool execution ran")
    execution_result: Optional[Any] = Field(default=None, description="Output returned from tool execution (if executed)")
    execution_latency_ms: float = Field(default=0.0, description="End-to-end gateway & execution latency in milliseconds")
    status: str = Field(default="PENDING", description="Lifecycle state of the tool call")
    reason: Optional[str] = Field(default=None, description="Security rationale or error justification")


class ContextEvaluationRequest(BaseModel):
    """Payload to request raw contextual telemetry factors."""
    role: str = Field(..., description="Agent role (RESEARCHER, CODER, DEPLOYER)", examples=["RESEARCHER"])
    tool_name: str = Field(..., description="Tool being invoked", examples=["search_docs"])
    payload: Union[Dict[str, Any], str] = Field(default="", description="Arguments or prompt to analyze")
    session_id: Optional[str] = Field(default=None, description="Optional session UUID for sliding window history")


class ContextEvaluationResponse(BaseModel):
    """Context factors response."""
    permission_violation: float = Field(..., description="P factor in {0.0, 1.0}")
    behavioral_dev: float = Field(..., description="B factor in [0.0, 1.0]")
    resource_sens: float = Field(..., description="S factor in [0.1, 1.0]")
    action_crit: float = Field(..., description="C factor in [0.1, 1.0]")
    latency_ms: float = Field(..., description="Aggregation latency in milliseconds")
    rbac_allowed: bool
    rbac_review: bool
    rbac_reason: str
