"""
AEGIS-NET Phase 3 Verification Suite: Security Proxy & Tool-Call Gateway.
Validates boundary enforcement, tri-state decisions, execution interception, and envelope issuance.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.security import ToolCallEnvelope
from app.proxy.gateway import security_gateway
from app.proxy.exceptions import (
    SecurityProxyBlockException,
    SessionQuarantinedException,
    SessionNotFoundException,
)
from app.services.session_manager import session_manager
from app.core.constants import Decision, ToolCallStatus, AgentStatus

client = TestClient(app)


@pytest.fixture(scope="module")
def active_sessions():
    """Sets up test sessions for Researcher and Coder."""
    researcher_sess = session_manager.start_session("agent-res-01", "RESEARCHER")
    coder_sess = session_manager.start_session("agent-cod-01", "CODER")
    return {
        "researcher": researcher_sess,
        "coder": coder_sess,
    }


def test_authorized_tool_call_execution(active_sessions):
    """Verify safe authorized tool call is permitted, executed, and receives an envelope token."""
    coder = active_sessions["coder"]
    envelope = ToolCallEnvelope(
        session_id=coder.session_id,
        agent_id=coder.agent_id,
        tool_name="read_workspace_file",
        payload={"file_path": "README.md"},
    )

    executed = False

    def mock_executor(args):
        nonlocal executed
        executed = True
        return {"content": "AEGIS-NET Readme Content"}

    result = security_gateway.intercept_tool_call(envelope, tool_executor=mock_executor)

    assert result.decision == Decision.ALLOW.value
    assert result.is_executed is True
    assert executed is True
    assert result.envelope_token.startswith("tok-")
    assert result.status == ToolCallStatus.EXECUTED.value
    assert result.execution_latency_ms > 0
    assert result.execution_result == {"content": "AEGIS-NET Readme Content"}


def test_unauthorized_call_raises_security_proxy_block(active_sessions):
    """Ensure direct unauthorized tool call raises SecurityProxyBlockException when requested."""
    researcher = active_sessions["researcher"]
    # Researcher attempting to execute arbitrary command
    envelope = ToolCallEnvelope(
        session_id=researcher.session_id,
        agent_id=researcher.agent_id,
        tool_name="execute_command",
        payload={"command": "rm -rf /"},
    )

    with pytest.raises(SecurityProxyBlockException) as exc_info:
        security_gateway.intercept_tool_call(envelope, raise_on_block=True)

    assert "Access Denied" in str(exc_info.value)
    assert exc_info.value.details["tool_name"] == "execute_command"


def test_executor_never_called_on_block(active_sessions):
    """CRITICAL: Verify tool execution logic is NEVER invoked if the proxy blocks."""
    researcher = active_sessions["researcher"]
    envelope = ToolCallEnvelope(
        session_id=researcher.session_id,
        agent_id=researcher.agent_id,
        tool_name="write_workspace_file",
        payload={"path": "/app/config.py", "content": "malicious code"},
    )

    executor_invoked = False

    def dangerous_tool(args):
        nonlocal executor_invoked
        executor_invoked = True
        return {"status": "overwritten"}

    result = security_gateway.intercept_tool_call(
        envelope, tool_executor=dangerous_tool, raise_on_block=False
    )

    assert result.decision == Decision.BLOCK.value
    assert result.is_executed is False
    assert executor_invoked is False, "Tool executor must NEVER be called when proxy blocks!"
    assert result.status == ToolCallStatus.REJECTED.value
    assert result.envelope_token.startswith("tok-")


def test_quarantined_session_blocks_all_tools(active_sessions):
    """Verify quarantined session cannot invoke even read-only safe tools."""
    coder = active_sessions["coder"]
    # Quarantine coder session
    session_manager.update_session_status(coder.session_id, AgentStatus.QUARANTINED.value)

    envelope = ToolCallEnvelope(
        session_id=coder.session_id,
        agent_id=coder.agent_id,
        tool_name="read_workspace_file",
        payload={"file_path": "README.md"},
    )

    with pytest.raises(SessionQuarantinedException):
        security_gateway.intercept_tool_call(envelope, raise_on_block=True)

    # Restore session status for clean state
    session_manager.update_session_status(coder.session_id, AgentStatus.ACTIVE.value)


def test_proxy_api_endpoint_allow(active_sessions):
    """Verify HTTP POST /api/v1/proxy/intercept allows permitted call."""
    coder = active_sessions["coder"]
    resp = client.post(
        "/api/v1/proxy/intercept",
        json={
            "session_id": coder.session_id,
            "agent_id": coder.agent_id,
            "tool_name": "read_workspace_file",
            "payload": {"file_path": "docs.txt"},
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["decision"] == "ALLOW"
    assert data["is_executed"] is True
    assert "envelope_token" in data
    assert data["execution_latency_ms"] > 0


def test_proxy_api_endpoint_block_with_raise(active_sessions):
    """Verify HTTP POST /api/v1/proxy/intercept?raise_on_block=true returns 403."""
    researcher = active_sessions["researcher"]
    resp = client.post(
        "/api/v1/proxy/intercept?raise_on_block=true",
        json={
            "session_id": researcher.session_id,
            "agent_id": researcher.agent_id,
            "tool_name": "execute_command",
            "payload": {"command": "cat /etc/shadow"},
        },
    )
    assert resp.status_code == 403
    error_body = resp.json()
    assert "detail" in error_body
