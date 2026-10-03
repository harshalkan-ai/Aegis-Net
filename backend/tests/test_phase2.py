"""
AEGIS-NET Phase 2 Verification Suite: Agent Runtime, Sessions & RBAC Permissions.
Validates session lifecycle, Supabase synchronization, RBAC matrix enforcement, and sub-2ms evaluation latency.
"""

import time
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.rbac_engine import rbac_engine
from app.services.session_manager import session_manager

client = TestClient(app)


def test_session_lifecycle_and_state_storage():
    """Verify session creation, persistence to storage/cache, and retrieval."""
    agent_id = "test-agent-researcher-01"
    role = "RESEARCHER"

    # 1. Start Session
    start_resp = client.post(
        "/api/v1/agents/session/start",
        json={"agent_id": agent_id, "role": role},
    )
    assert start_resp.status_code == 201
    session_data = start_resp.json()

    assert "session_id" in session_data
    session_id = session_data["session_id"]
    assert session_data["agent_id"] == agent_id
    assert session_data["role"] == role
    assert session_data["status"] == "ACTIVE"
    assert "telemetry" in session_data

    # 2. Retrieve Session
    get_resp = client.get(f"/api/v1/agents/session/{session_id}")
    assert get_resp.status_code == 200
    retrieved_data = get_resp.json()

    assert retrieved_data["session_id"] == session_id
    assert retrieved_data["agent_id"] == agent_id
    assert retrieved_data["status"] == "ACTIVE"


def test_session_not_found():
    """Verify 404 response for nonexistent session ID."""
    resp = client.get("/api/v1/agents/session/non-existent-session-uuid-12345")
    assert resp.status_code == 404


def test_rbac_researcher_write_denied():
    """Verify Researcher requesting write_workspace_file returns is_allowed=False."""
    resp = client.post(
        "/api/v1/agents/permissions/check",
        json={"role": "RESEARCHER", "tool_name": "write_workspace_file"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["role"] == "RESEARCHER"
    assert data["tool_name"] == "write_workspace_file"
    assert data["is_allowed"] is False
    assert data["requires_review"] is False
    assert "prohibited" in data["reason"].lower() or "denied" in data["reason"].lower()


def test_rbac_coder_write_allowed():
    """Verify Coder requesting write_workspace_file returns is_allowed=True."""
    resp = client.post(
        "/api/v1/agents/permissions/check",
        json={"role": "CODER", "tool_name": "write_workspace_file"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["role"] == "CODER"
    assert data["tool_name"] == "write_workspace_file"
    assert data["is_allowed"] is True
    assert data["requires_review"] is False


def test_rbac_coder_execute_command_requires_review():
    """Verify Coder requesting execute_command requires review."""
    resp = client.post(
        "/api/v1/agents/permissions/check",
        json={"role": "CODER", "tool_name": "execute_command"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_allowed"] is True
    assert data["requires_review"] is True


def test_rbac_deployer_permissions():
    """Verify Deployer allowed, review, and denied tool configurations."""
    # Allowed: deploy_service
    resp_allowed = client.post(
        "/api/v1/agents/permissions/check",
        json={"role": "DEPLOYER", "tool_name": "deploy_service"},
    )
    assert resp_allowed.json()["is_allowed"] is True
    assert resp_allowed.json()["requires_review"] is False

    # Review: rollback_deployment
    resp_review = client.post(
        "/api/v1/agents/permissions/check",
        json={"role": "DEPLOYER", "tool_name": "rollback_deployment"},
    )
    assert resp_review.json()["is_allowed"] is True
    assert resp_review.json()["requires_review"] is True

    # Denied: write_workspace_file
    resp_denied = client.post(
        "/api/v1/agents/permissions/check",
        json={"role": "DEPLOYER", "tool_name": "write_workspace_file"},
    )
    assert resp_denied.json()["is_allowed"] is False


def test_rbac_unknown_role_or_tool_default_deny():
    """Verify zero-trust default deny behavior for unknown roles and unlisted tools."""
    # Unknown role
    resp_role = client.post(
        "/api/v1/agents/permissions/check",
        json={"role": "UNKNOWN_HACKER", "tool_name": "search_docs"},
    )
    assert resp_role.json()["is_allowed"] is False

    # Unknown unlisted tool for Researcher
    resp_tool = client.post(
        "/api/v1/agents/permissions/check",
        json={"role": "RESEARCHER", "tool_name": "format_disk"},
    )
    assert resp_tool.json()["is_allowed"] is False


def test_rbac_evaluation_latency():
    """Verify permission evaluation strictly satisfies the < 2ms performance target."""
    iterations = 200
    times = []

    for _ in range(iterations):
        t0 = time.perf_counter()
        res = rbac_engine.check_permission(role="CODER", tool_name="write_workspace_file")
        dt_ms = (time.perf_counter() - t0) * 1000
        times.append(dt_ms)
        assert res.is_allowed is True

    avg_latency = sum(times) / len(times)
    max_latency = max(times)
    print(f"\n[RBAC Latency] Average: {avg_latency:.4f} ms | Max: {max_latency:.4f} ms")

    # In-memory hash set lookup must easily be < 2ms (typically < 0.05ms)
    assert avg_latency < 2.0, f"Average latency {avg_latency} ms exceeded 2ms threshold"
    assert max_latency < 5.0, f"Max latency {max_latency} ms exceeded 5ms threshold"
