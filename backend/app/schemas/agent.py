"""
Pydantic Schemas for Agents, Sessions, and Permissions.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field


class AgentCreate(BaseModel):
    id: str = Field(..., description="Unique agent identifier", examples=["agent-researcher-01"])
    role: str = Field(..., description="Agent operational role (RESEARCHER, CODER, DEPLOYER)", examples=["RESEARCHER"])


class AgentResponse(BaseModel):
    id: str
    role: str
    created_at: Optional[datetime] = None


class SessionStartRequest(BaseModel):
    agent_id: str = Field(..., description="Unique agent identifier", examples=["agent-coder-01"])
    role: str = Field(..., description="Role assumed for this session", examples=["CODER"])


class SessionResponse(BaseModel):
    session_id: str = Field(..., description="Unique UUID for this session")
    agent_id: str = Field(..., description="Agent bound to this session")
    role: str = Field(..., description="Agent role")
    status: str = Field(default="ACTIVE", description="Session state (ACTIVE, QUARANTINED, TERMINATED)")
    created_at: str = Field(..., description="Session creation UTC timestamp")
    telemetry: Dict[str, Any] = Field(default_factory=dict, description="Session runtime metrics")


class PermissionCheckRequest(BaseModel):
    role: str = Field(..., description="Agent role to check against", examples=["RESEARCHER"])
    tool_name: str = Field(..., description="Name of tool being invoked", examples=["write_workspace_file"])


class PermissionCheckResponse(BaseModel):
    role: str
    tool_name: str
    is_allowed: bool
    requires_review: bool
    evaluation_latency_ms: float
    reason: str
