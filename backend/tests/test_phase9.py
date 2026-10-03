"""
Phase 9 Tests: Gemini Autonomous Forensics Engine.
Validates structured forensic generation, heuristic fallbacks, and API retrieval.
"""
import pytest
import time
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.forensics import ForensicAnalysisReport
from app.forensics.gemini_ciso import generate_forensic_report, _heuristic_report
from app.api.v1.routes_forensics import register_forensic_report, _forensic_registry
from app.incidents.incident_service import incident_service


client = TestClient(app)


def test_heuristic_report_structure():
    """Verify heuristic fallback creates a valid ForensicAnalysisReport."""
    incident_data = {
        "incident_id": "inc-test-heuristic",
        "tool_name": "bash",
        "session_id": "sess-test-001",
        "risk_score": 0.88,
        "threat_score": 0.92,
        "arguments": {"command": "rm -rf /"},
    }
    report = _heuristic_report(incident_data)
    assert isinstance(report, ForensicAnalysisReport)
    assert report.cwe_id == "CWE-78"
    assert "Command Injection" in report.threat_summary
    assert report.attack_vector in ("LOCAL", "NETWORK")
    assert len(report.affected_components) > 0
    assert len(report.suggested_patch) > 0
    assert 0.0 <= report.forensic_confidence <= 1.0


def test_heuristic_cwe_sql_injection():
    """Verify SQL injection heuristics identify CWE-89."""
    incident_data = {
        "incident_id": "inc-sql-001",
        "tool_name": "query_database",
        "session_id": "sess-sql",
        "risk_score": 0.95,
        "threat_score": 0.90,
        "arguments": {"query": "SELECT * FROM users WHERE '1'='1'; DROP TABLE users;"},
    }
    report = _heuristic_report(incident_data)
    assert report.cwe_id == "CWE-89"
    assert report.forensic_confidence >= 0.80


@pytest.mark.asyncio
async def test_generate_forensic_report_offline():
    """Verify generate_forensic_report falls back cleanly when offline or without API key."""
    incident_data = {
        "incident_id": "inc-offline-01",
        "tool_name": "python_eval",
        "session_id": "sess-offline",
        "risk_score": 0.75,
        "threat_score": 0.80,
    }
    report = await generate_forensic_report(incident_data)
    assert isinstance(report, ForensicAnalysisReport)
    assert report.cwe_id is not None
    assert report.threat_summary is not None
    assert report.forensic_confidence > 0.0


def test_forensics_api_registry_retrieval():
    """Verify GET /api/v1/forensics/{incident_id} retrieves registered report."""
    test_id = "inc-api-test-123"
    report = ForensicAnalysisReport(
        cwe_id="CWE-200",
        attack_vector="NETWORK",
        threat_summary="Data exfiltration attempt blocked by AEGIS-NET.",
        affected_components=["SecurityGateway", "network_call"],
        suggested_patch="Block egress traffic to untrusted domains.",
        forensic_confidence=0.91,
    )
    register_forensic_report(test_id, report)

    response = client.get(f"/api/v1/forensics/{test_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["cwe_id"] == "CWE-200"
    assert data["forensic_confidence"] == 0.91
    assert data["attack_vector"] == "NETWORK"


def test_forensics_api_not_found():
    """Verify GET /api/v1/forensics/{unknown_id} returns 404."""
    response = client.get("/api/v1/forensics/nonexistent-incident-uuid")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_incident_block_triggers_forensics(monkeypatch):
    """Verify creating a BLOCK incident triggers async forensics registration."""
    mock_client = pytest.importorskip("unittest.mock").MagicMock()
    mock_client.table.return_value.insert.return_value.execute.return_value = mock_client
    monkeypatch.setattr("app.incidents.incident_service.get_supabase_client", lambda: mock_client)

    # Deterministic fast async mock for unit test
    async def mock_forensics(payload):
        return _heuristic_report(payload)

    monkeypatch.setattr(
        "app.incidents.incident_service.IncidentService._analyze_forensics",
        lambda self, inc_id, payload: mock_forensics(payload),
    )

    incident = incident_service.create_incident(
        agent_id="agent-researcher",
        session_id="sess-block-forensic",
        tool_call_id="tool-call-101",
        risk_score=0.95,
        threat_score=0.90,
        decision="BLOCK",
        reasons=["Hard override: high neural threat score."],
        tool_name="bash_exec",
    )
    assert incident["decision"] == "BLOCK"
    incident_id = incident["id"]

    # Poll briefly for async background thread to complete
    for _ in range(20):
        if incident_id in _forensic_registry:
            break
        time.sleep(0.05)

    assert incident_id in _forensic_registry
    registered = _forensic_registry[incident_id]
    assert registered["cwe_id"] in ("CWE-78", "CWE-200", "CWE-77")
    assert registered["forensic_confidence"] > 0.5
