"""
AEGIS-NET Gemini CISO Forensics Engine.
Generates structured 7-section forensic post-mortems via Gemini 2.5 Flash for blocked incidents.

Architectural Contract:
 - SLOW PATH ONLY: Gemini is NEVER invoked on ALLOW decisions.
 - Execution is always async/background — never blocks the fast-path evaluation pipeline.
 - Robust offline fallback: returns a deterministic heuristic report when API key absent or offline.
"""
import json
import logging
import re
from typing import Dict, Any, List

from app.core.config import settings
from app.schemas.forensics import ForensicAnalysisReport

logger = logging.getLogger(__name__)

# Heuristic CWE mapping: keywords found in tool names or payload → CWE classification
_CWE_HEURISTICS = [
    (["rm -rf", "bash", "shell", "exec", "command", "curl", "wget"], "CWE-78",  "OS Command Injection"),
    (["eval", "exec(", "subprocess", "popen"],                        "CWE-78",  "OS Command Injection"),
    (["sql", "select *", "drop table", "insert into"],                "CWE-89",  "SQL Injection"),
    (["ignore all", "jailbreak", "prompt injection", "override"],     "CWE-77",  "Command Injection via Prompt"),
    (["exfiltrate", "attacker.com", "evil.com", "data leak", "external destination", "send", "export"],
                                                                      "CWE-200", "Exposure of Sensitive Information"),
    (["permission", "rbac", "role", "unauthorized"],                  "CWE-269", "Improper Privilege Management"),
    (["path traversal", "../", "..\\", "/etc/shadow", "/etc/passwd"], "CWE-22",  "Path Traversal"),
    (["secret", ".env", "aws_", "api_key", "token", "credential"],   "CWE-312", "Cleartext Storage of Sensitive Info"),
]


def _heuristic_report(incident_data: Dict[str, Any]) -> ForensicAnalysisReport:
    """
    Offline heuristic fallback — produces a deterministic 7-section report from incident metadata
    without calling any external API. Used when GEMINI_API_KEY is absent or Gemini is offline.
    """
    combined = json.dumps(incident_data).lower()
    tool_name = incident_data.get("tool_name", "unknown_tool")
    risk_score = float(incident_data.get("risk_score", 0.6))
    threat_score = float(incident_data.get("threat_score", 0.5))
    decision = incident_data.get("decision", "BLOCK")
    agent_id = incident_data.get("agent_id", "unknown-agent")
    session_id = incident_data.get("session_id", "unknown-session")
    payload_preview = str(incident_data.get("payload", ""))[:300]
    circuit_breaker = incident_data.get("circuit_breaker_triggered", False)

    # Match heuristic CWE
    cwe_id = "CWE-77"
    attack_vector = "NETWORK"
    threat_label = "Command Injection via Prompt"

    for keywords, cwe, label in _CWE_HEURISTICS:
        if any(kw in combined for kw in keywords):
            cwe_id = cwe
            threat_label = label
            attack_vector = "NETWORK" if any(k in combined for k in ["curl", "attacker", "external", "send"]) else "LOCAL"
            break

    confidence = round(min(0.95, 0.60 + risk_score * 0.35 + threat_score * 0.05), 4)
    circuit_note = " Circuit breaker was TRIGGERED — agent session quarantined." if circuit_breaker else ""

    threat_indicators: List[str] = []
    if threat_score > 0.5:
        threat_indicators.append(f"High ONNX ML threat score: {threat_score:.4f} (threshold: 0.50)")
    if risk_score > 0.6:
        threat_indicators.append(f"Composite risk score: {risk_score:.4f} exceeded BLOCK threshold (0.60)")
    if "permission_violation" in combined:
        threat_indicators.append("RBAC permission violation detected — tool not authorized for agent role")
    if any(k in combined for k in ["export", "send", "external", "customer"]):
        threat_indicators.append("Data exfiltration pattern detected: sensitive data transfer to external target")
    if not threat_indicators:
        threat_indicators.append(f"Blocked by AEGIS-NET Policy Engine: {threat_label}")

    return ForensicAnalysisReport(
        cwe_id=cwe_id,
        attack_vector=attack_vector,
        incident_summary=(
            f"[HEURISTIC ANALYSIS] Agent '{agent_id}' attempted to invoke tool '{tool_name}' "
            f"which was intercepted and blocked by the AEGIS-NET Security Gateway. "
            f"The action received a composite risk score of {risk_score:.4f} and an ML threat score "
            f"of {threat_score:.4f}, triggering a {decision} decision.{circuit_note}"
        ),
        suspicion_reasoning=(
            f"The tool invocation '{tool_name}' raised multiple security flags: "
            f"(1) The ONNX DeBERTa-v3 model assigned a threat score of {threat_score:.4f}. "
            f"(2) The composite risk engine scored {risk_score:.4f} against a block threshold of 0.60. "
            f"Classification: {threat_label}. "
            f"The payload pattern '{payload_preview[:100]}...' contains indicators consistent with "
            f"unauthorized data access or manipulation intent."
        ),
        threat_indicators=threat_indicators,
        behavioral_anomalies=(
            f"Agent '{agent_id}' (session: {session_id}) deviated from expected behavioral baseline. "
            f"The tool '{tool_name}' is either not authorized for the agent's role or the payload "
            f"contains patterns inconsistent with legitimate operational use. "
            f"Behavioral deviation score contributed to elevated composite risk."
        ),
        potential_impact=(
            f"If the blocked action '{tool_name}' had been executed, potential impact includes: "
            f"unauthorized access to sensitive resources, data exfiltration to external endpoints, "
            f"privilege escalation beyond the agent's authorized scope, or system compromise. "
            f"Classification {cwe_id} ({threat_label}) indicates {attack_vector.lower()} attack surface exposure."
        ),
        recommended_response=(
            f"1. Immediately investigate agent '{agent_id}' session '{session_id}' for signs of compromise.\n"
            f"2. Review all prior tool calls in this session for lateral movement indicators.\n"
            f"3. Apply input allowlisting for tool '{tool_name}' — reject payloads matching {cwe_id} patterns.\n"
            f"4. Enforce least-privilege RBAC: verify the agent role is correct and appropriately scoped.\n"
            f"5. Enable real-time alerting for future {cwe_id} pattern matches in this deployment.\n"
            f"6. If circuit breaker was not triggered, consider manually quarantining this session."
        ),
        forensic_confidence=confidence,
        confidence_notes=(
            f"This is a heuristic analysis (no Gemini API key configured). Confidence {confidence:.2f} is "
            f"derived from risk score ({risk_score:.4f}) and ML threat score ({threat_score:.4f}). "
            f"Configure GEMINI_API_KEY for full LLM-powered forensic analysis."
        ),
        threat_summary=(
            f"[HEURISTIC] Blocked tool '{tool_name}' scored risk={risk_score:.4f}, "
            f"threat={threat_score:.4f}. Classification: {threat_label}. "
            f"Agent was denied execution via AEGIS-NET Policy Engine mandatory override."
        ),
        affected_components=[
            "SecurityGateway",
            tool_name,
            f"Session:{session_id}",
            f"Agent:{agent_id}",
        ],
        suggested_patch=(
            f"1. Sanitize and validate all tool payloads before execution. "
            f"2. Apply input allowlisting for '{tool_name}'. "
            f"3. Enforce principle of least privilege for agent roles. "
            f"4. Enable Supabase Realtime alerting for {cwe_id} pattern matches."
        ),
    )


async def generate_forensic_report(incident_data: Dict[str, Any]) -> ForensicAnalysisReport:
    """
    Primary forensic analysis function. Slow path — always async.

    Strategy:
      1. If GEMINI_API_KEY is set: call gemini-2.5-flash with structured JSON output requesting all 7 sections.
      2. On any API failure (network, quota, parse error): fall through to heuristic.
      3. Heuristic is always available as a guaranteed fallback.

    Returns:
        ForensicAnalysisReport — never raises, never returns None.
    """
    api_key = settings.GEMINI_API_KEY.strip() if settings.GEMINI_API_KEY else ""

    if not api_key:
        logger.info("[GEMINI CISO] No API key configured — using heuristic fallback.")
        return _heuristic_report(incident_data)

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)

        prompt = f"""You are a Senior CISO and security forensics analyst performing a structured incident post-mortem.
A zero-trust multi-agent AI security system (AEGIS-NET) blocked the following agent action.
Analyze this incident and produce a comprehensive 7-section forensic report.

INCIDENT DATA:
{json.dumps(incident_data, indent=2)}

Produce a structured JSON forensic report with ALL of the following fields:

1. cwe_id: The most applicable CWE identifier (e.g. "CWE-200", "CWE-77", "CWE-78")
2. attack_vector: Attack surface ("NETWORK", "LOCAL", "PHYSICAL", or "ADJACENT")
3. incident_summary: Executive summary of what happened, who the agent is, what they tried to do (2-3 sentences)
4. suspicion_reasoning: Detailed analysis of WHY this action was flagged as suspicious — reference specific scores and payload indicators (3-5 sentences)
5. threat_indicators: JSON array of 3-6 specific observable indicators of compromise or attack intent (strings)
6. behavioral_anomalies: Description of how the agent's behavior deviated from expected baseline (2-3 sentences)
7. potential_impact: If not blocked, what could have happened? Include data/system/financial risk (2-3 sentences)
8. recommended_response: Numbered list of 4-6 concrete security response actions
9. forensic_confidence: Float 0.0-1.0 representing your confidence in this analysis
10. confidence_notes: Brief explanation of confidence level and any uncertainty (1-2 sentences)
11. threat_summary: Single-paragraph concise threat summary for the incident dashboard
12. affected_components: JSON array of impacted system components (strings)
13. suggested_patch: Numbered mitigation steps for the specific tool/action that was blocked

Be specific, technical, and base your analysis entirely on the provided incident data."""

        model_to_use = getattr(settings, "GEMINI_MODEL", "gemini-2.5-flash")
        try:
            response = client.models.generate_content(
                model=model_to_use,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=ForensicAnalysisReport,
                    temperature=0.1,
                ),
            )
        except Exception:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=ForensicAnalysisReport,
                    temperature=0.1,
                ),
            )

        report = ForensicAnalysisReport.model_validate_json(response.text)
        logger.info(
            f"[GEMINI CISO] Forensic report generated: {report.cwe_id} | "
            f"Confidence: {report.forensic_confidence:.2f}"
        )
        return report

    except Exception as e:
        logger.warning(f"[GEMINI CISO] API call failed ({type(e).__name__}: {e}) — falling back to heuristic.")
        return _heuristic_report(incident_data)
