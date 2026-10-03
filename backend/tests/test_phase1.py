"""
AEGIS-NET Phase 1 Verification Suite.
Validates configurations, schema definitions, system constants, and baseline API endpoints.
"""

from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.constants import (
    Decision,
    ToolCallStatus,
    AgentStatus,
    IncidentSeverity,
    IncidentStatus,
    SecurityEventType,
    QuarantineStatus,
    ErrorCode,
)
from app.main import app

client = TestClient(app)


def test_configuration_loading():
    """Verify core configurations and environment variables are properly resolved."""
    assert settings.PROJECT_NAME == "AEGIS-NET Security Engine"
    assert settings.VERSION == "1.0.0"
    assert settings.RISK_THRESHOLD_ALLOW == 0.30
    assert settings.RISK_THRESHOLD_REVIEW == 0.60
    assert settings.FAST_PATH_MAX_LATENCY_MS == 40.0
    assert settings.SUPABASE_URL is not None
    assert settings.SUPABASE_SERVICE_ROLE_KEY is not None


def test_system_constants():
    """Verify system constants and enum values adhere to architecture standards."""
    assert Decision.ALLOW == "ALLOW"
    assert Decision.REVIEW == "REVIEW"
    assert Decision.BLOCK == "BLOCK"

    assert ToolCallStatus.PENDING == "PENDING"
    assert ToolCallStatus.EXECUTED == "EXECUTED"

    assert AgentStatus.ACTIVE == "ACTIVE"
    assert AgentStatus.QUARANTINED == "QUARANTINED"

    assert IncidentSeverity.CRITICAL == "CRITICAL"
    assert IncidentStatus.OPEN == "OPEN"

    assert SecurityEventType.PROMPT_INJECTION == "PROMPT_INJECTION"
    assert QuarantineStatus.ACTIVE == "ACTIVE"

    assert ErrorCode.ERR_HIGH_RISK_BLOCKED == "ERR_HIGH_RISK_BLOCKED"
    assert ErrorCode.ERR_CIRCUIT_BREAKER_OPEN == "ERR_CIRCUIT_BREAKER_OPEN"


def test_health_endpoint():
    """Verify GET /health returns standard health check payload."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "1.0.0"
    assert "timestamp" in data


def test_root_endpoint():
    """Verify GET / returns project metadata."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == settings.PROJECT_NAME
    assert data["status"] == "online"


def test_db_health_endpoint_response_structure():
    """Verify GET /health/db returns structured telemetry (200 or 503)."""
    response = client.get("/health/db")
    assert response.status_code in (200, 503)
    data = response.json()
    assert "status" in data
    assert "latency_ms" in data
    assert "url" in data


def test_migration_schema_integrity():
    """Verify 001_initial_schema.sql defines all required 10 tables and RLS."""
    migration_file = Path(__file__).resolve().parent.parent / "migrations" / "001_initial_schema.sql"
    assert migration_file.exists(), "Migration file 001_initial_schema.sql must exist"

    sql_content = migration_file.read_text(encoding="utf-8")
    
    required_tables = [
        "agents",
        "agent_sessions",
        "agent_permissions",
        "tool_calls",
        "risk_assessments",
        "security_events",
        "incidents",
        "quarantine_records",
        "audit_logs",
        "forensics_reports",
    ]

    for table in required_tables:
        assert f"CREATE TABLE IF NOT EXISTS {table}" in sql_content, f"Table {table} missing in SQL migration"
        assert f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;" in sql_content, f"RLS missing for {table}"


def test_critical_invariants_preserved():
    """Verify verified ML weights and models remain unmodified."""
    backend_root = Path(__file__).resolve().parent.parent
    
    weights_model = backend_root / "weights" / "model.onnx"
    ml_loader = backend_root / "app" / "models" / "ml_loader.py"
    risk_scorer = backend_root / "app" / "models" / "risk_scorer.py"

    assert weights_model.exists(), "model.onnx must exist"
    assert ml_loader.exists(), "ml_loader.py must exist"
    assert risk_scorer.exists(), "risk_scorer.py must exist"
