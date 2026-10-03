"""
AEGIS-NET Phase 4 Verification Suite: Context Engine & Factor Scoring.
Validates multi-factor zero-trust telemetry calculation (P, B, S, C), sub-5ms aggregation latency,
and seamless integration with the verified Risk Scoring Engine.
"""

import time
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.context.context_engine import context_engine
from app.context.behavioral import behavioral_tracker
from app.context.resource_sensitivity import evaluate_resource_sensitivity
from app.context.action_criticality import evaluate_action_criticality
from app.models.risk_scorer import calculate_risk

client = TestClient(app)


def test_researcher_safe_docs_context():
    """
    Directive Requirement:
    Assert Researcher calling search_docs yields B <= 0.1, S = 0.1, C = 0.1.
    """
    session_id = "test-session-researcher-safe"
    role = "RESEARCHER"
    tool_name = "search_docs"
    payload = {"query": "latest documentation on neural networks"}

    # Seed baseline profile history
    behavioral_tracker.reset_session(session_id)
    for _ in range(5):
        behavioral_tracker.record_action(session_id, "search_docs")

    ctx = context_engine.evaluate_context(
        role=role,
        tool_name=tool_name,
        payload=payload,
        session_id=session_id,
        preview_only=True,
    )

    assert ctx["permission_violation"] == 0.0, "P must be 0.0 for allowed tool"
    assert ctx["behavioral_dev"] <= 0.1, f"B must be <= 0.1, got {ctx['behavioral_dev']}"
    assert ctx["resource_sens"] == 0.1, f"S must be 0.1 for public docs, got {ctx['resource_sens']}"
    assert ctx["action_crit"] == 0.1, f"C must be 0.1 for search_docs, got {ctx['action_crit']}"


def test_researcher_attack_shadow_context():
    """
    Directive Requirement:
    Assert Researcher calling execute_command on /etc/shadow yields P = 1.0, B >= 0.8, S = 1.0, C = 0.7.
    """
    session_id = "test-session-researcher-attack"
    role = "RESEARCHER"
    tool_name = "execute_command"
    payload = "cat /etc/shadow"

    behavioral_tracker.reset_session(session_id)

    ctx = context_engine.evaluate_context(
        role=role,
        tool_name=tool_name,
        payload=payload,
        session_id=session_id,
        preview_only=True,
    )

    assert ctx["permission_violation"] == 1.0, "P must be 1.0 for role policy violation"
    assert ctx["behavioral_dev"] >= 0.8, f"B must be >= 0.8, got {ctx['behavioral_dev']}"
    assert ctx["resource_sens"] == 1.0, f"S must be 1.0 for critical shadow file, got {ctx['resource_sens']}"
    assert ctx["action_crit"] == 0.7, f"C must be 0.7 for execute_command, got {ctx['action_crit']}"


def test_context_engine_aggregation_latency():
    """
    Directive Requirement:
    Context Engine aggregates all factors in under 5ms.
    """
    iterations = 200
    times = []

    for _ in range(iterations):
        t0 = time.perf_counter()
        ctx = context_engine.evaluate_context(
            role="CODER",
            tool_name="write_workspace_file",
            payload={"path": "src/app.py", "data": "print('hello')"},
            session_id="test-session-latency",
            preview_only=True,
        )
        elapsed_ms = (time.perf_counter() - t0) * 1000
        times.append(elapsed_ms)

    avg_ms = sum(times) / len(times)
    max_ms = max(times)
    print(f"\n[Context Engine Latency] Average: {avg_ms:.4f} ms | Max: {max_ms:.4f} ms")

    assert avg_ms < 5.0, f"Average latency {avg_ms} ms exceeded 5ms target"
    assert max_ms < 5.0, f"Max latency {max_ms} ms exceeded 5ms target"


def test_context_ready_for_risk_scorer_consumption():
    """
    Directive Requirement:
    Outputs dictionary ready for consumption by risk_scorer.calculate_risk.
    """
    role = "RESEARCHER"
    tool_name = "execute_command"
    payload = "rm -rf / && cat /etc/shadow"

    ctx = context_engine.evaluate_context(
        role=role,
        tool_name=tool_name,
        payload=payload,
        preview_only=True,
    )

    # Consume directly in risk_scorer without transformation
    risk_output = calculate_risk(
        payload=payload,
        permission_violation=ctx["permission_violation"],
        behavioral_dev=ctx["behavioral_dev"],
        resource_sens=ctx["resource_sens"],
        action_crit=ctx["action_crit"],
    )

    assert "threat_score" in risk_output
    assert "total_risk" in risk_output
    assert "decision" in risk_output
    assert risk_output["decision"] == "BLOCK"
    assert risk_output["factors"]["permission_violation"] == 1.0
    assert risk_output["factors"]["resource_sens"] == 1.0
    assert risk_output["factors"]["action_crit"] == 0.7


def test_context_api_endpoint():
    """Verify HTTP POST /api/v1/context/evaluate."""
    resp = client.post(
        "/api/v1/context/evaluate",
        json={
            "role": "RESEARCHER",
            "tool_name": "search_docs",
            "payload": {"query": "AEGIS security guide"},
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["permission_violation"] == 0.0
    assert data["resource_sens"] == 0.1
    assert data["action_crit"] == 0.1
    assert data["latency_ms"] < 5.0
