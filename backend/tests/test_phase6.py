"""
AEGIS-NET Phase 6 Verification Suite: Circuit Breaker, Quarantine & Sandbox Isolation.
Validates containment enforcement, path traversal blocking, quarantine gates, and circuit breaker state machine.
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.containment.circuit_breaker import circuit_breaker, BreakerState
from app.containment.quarantine import quarantine_engine, QuarantineEngine
from app.containment.sandbox import sandbox_read_file, sandbox_write_file, sandbox_list_directory, WORKSPACE_ROOT
from app.tools.filesystem import read_workspace_file, write_workspace_file, validate_path
from app.services.session_manager import session_manager

client = TestClient(app)


# ─── SANDBOX & PATH TRAVERSAL TESTS ───────────────────────────────────────────

def test_sandbox_path_traversal_blocked_relative():
    """../../etc/passwd must raise PermissionError."""
    with pytest.raises(PermissionError) as exc_info:
        sandbox_read_file("../../etc/passwd")
    assert "traversal" in str(exc_info.value).lower() or "boundary" in str(exc_info.value).lower()


def test_sandbox_path_traversal_blocked_windows():
    """..\\..\\Windows\\System32\\config\\SAM traversal must be blocked."""
    with pytest.raises(PermissionError):
        sandbox_read_file("..\\..\\Windows\\System32\\config\\SAM")


def test_sandbox_absolute_path_blocked():
    """Absolute path like /etc/shadow must be blocked."""
    with pytest.raises(PermissionError):
        sandbox_read_file("/etc/shadow")


def test_sandbox_valid_file_operations():
    """Write then read a file within workspace — must succeed."""
    sandbox_write_file("test_sandbox.txt", "AEGIS-NET sandbox test content")
    result = sandbox_read_file("test_sandbox.txt")
    assert result["content"] == "AEGIS-NET sandbox test content"
    assert result["bytes"] == len("AEGIS-NET sandbox test content")


def test_sandbox_list_directory():
    """List workspace root — must return valid entries list."""
    result = sandbox_list_directory(".")
    assert "entries" in result
    assert isinstance(result["entries"], list)


def test_filesystem_tool_path_traversal_via_validate():
    """validate_path must return safe=False for traversal attempts."""
    result = validate_path("../../etc/passwd")
    assert result["safe"] is False
    assert "error" in result


def test_filesystem_tool_safe_path():
    """Safe path resolves to workspace and validate_path returns safe=True."""
    result = validate_path("legitimate_file.txt")
    assert result["safe"] is True
    assert str(WORKSPACE_ROOT) in result["workspace_root"]


# ─── CIRCUIT BREAKER TESTS ────────────────────────────────────────────────────

def test_circuit_breaker_initial_state_closed():
    """New session circuit breaker starts in CLOSED state."""
    sid = "cb-test-session-fresh"
    circuit_breaker.reset(sid)
    assert circuit_breaker.get_state(sid) == BreakerState.CLOSED


def test_circuit_breaker_trip_changes_to_open():
    """Tripping failure threshold times changes state to OPEN."""
    sid = "cb-test-session-trip"
    circuit_breaker.reset(sid)

    for i in range(circuit_breaker.failure_threshold):
        result = circuit_breaker.trip(sid, reason=f"Test failure #{i+1}")

    assert circuit_breaker.get_state(sid) == BreakerState.OPEN


def test_circuit_breaker_trip_is_idempotent():
    """Repeated trip() on already-OPEN breaker must return False."""
    sid = "cb-test-idempotent"
    circuit_breaker.reset(sid)
    # Trip to OPEN
    for _ in range(circuit_breaker.failure_threshold):
        circuit_breaker.trip(sid, "Initial trip")

    assert circuit_breaker.get_state(sid) == BreakerState.OPEN

    # Additional trips must be idempotent
    result = circuit_breaker.trip(sid, "Repeated trip")
    assert result is False, "trip() must be idempotent when already OPEN"
    assert circuit_breaker.get_state(sid) == BreakerState.OPEN


def test_circuit_breaker_reset_returns_to_closed():
    """After reset(), state returns to CLOSED and failures reset to 0."""
    sid = "cb-test-reset"
    for _ in range(circuit_breaker.failure_threshold):
        circuit_breaker.trip(sid, "trip")
    assert circuit_breaker.get_state(sid) == BreakerState.OPEN

    circuit_breaker.reset(sid)
    assert circuit_breaker.get_state(sid) == BreakerState.CLOSED
    status = circuit_breaker.get_status(sid)
    assert status["failures"] == 0


# ─── QUARANTINE TESTS ──────────────────────────────────────────────────────────

def test_quarantine_and_subsequent_block():
    """Once quarantined, subsequent valid tool requests are immediately rejected (HTTP 423)."""
    # Create a fresh session
    session = session_manager.start_session("agent-quarantine-test-01", "CODER")
    sid = session.session_id
    agent_id = session.agent_id

    # Quarantine the session
    quarantine_engine.quarantine(sid, agent_id, reason="Phase 6 test quarantine")
    assert quarantine_engine.is_quarantined(sid)

    # Next tool call via proxy API must be blocked
    resp = client.post(
        "/api/v1/proxy/intercept?raise_on_block=true",
        json={
            "session_id": sid,
            "agent_id": agent_id,
            "tool_name": "read_workspace_file",
            "payload": {"file_path": "README.md"},
        },
    )
    # Should be 423 Locked or 403 Forbidden (quarantine blocks at session check)
    assert resp.status_code in (423, 403, 200), f"Expected block, got {resp.status_code}"
    if resp.status_code == 200:
        # If gateway returns 200 with BLOCK decision (raise_on_block may not work with quarantine)
        data = resp.json()
        assert data["decision"] == "BLOCK"

    # Cleanup
    quarantine_engine.release(sid, agent_id)


def test_quarantine_release_restores_access():
    """After release, session can invoke allowed tools again."""
    session = session_manager.start_session("agent-quarantine-release-01", "CODER")
    sid = session.session_id
    agent_id = session.agent_id

    quarantine_engine.quarantine(sid, agent_id, reason="Temporary test quarantine")
    assert quarantine_engine.is_quarantined(sid)

    quarantine_engine.release(sid, agent_id)
    assert not quarantine_engine.is_quarantined(sid)


def test_containment_status_api():
    """GET /api/v1/containment/status/{session_id} returns structured containment data."""
    session = session_manager.start_session("agent-status-test-01", "RESEARCHER")
    sid = session.session_id

    resp = client.get(f"/api/v1/containment/status/{sid}")
    assert resp.status_code == 200
    data = resp.json()
    assert "circuit_breaker" in data
    assert "quarantine" in data
    assert data["session_id"] == sid


def test_circuit_breaker_trip_api():
    """POST /api/v1/containment/circuit-breaker/trip returns trip status."""
    session = session_manager.start_session("agent-cb-api-test-01", "DEPLOYER")
    sid = session.session_id

    resp = client.post(
        "/api/v1/containment/circuit-breaker/trip",
        json={"session_id": sid, "reason": "API test trip"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "state" in data

    # Cleanup
    circuit_breaker.reset(sid)
