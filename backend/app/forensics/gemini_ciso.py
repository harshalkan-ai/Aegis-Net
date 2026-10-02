"""
AEGIS-NET Gemini CISO Forensics Engine.
Generates structured CVE post-mortems via Gemini 2.5 Flash for blocked incidents.

Architectural Contract:
 - SLOW PATH ONLY: Gemini is NEVER invoked on ALLOW decisions.
 - Execution is always async/background — never blocks the fast-path evaluation pipeline.
 - Robust offline fallback: returns a deterministic heuristic report when API key absent or offline.
"""
import json
import logging
import re
from typing import Dict, Any, Optional

from app.core.config import settings
from app.schemas.forensics import ForensicAnalysisReport

logger = logging.getLogger(__name__)

# Heuristic CWE mapping: keywords found in tool names or payload → CWE classification
_CWE_HEURISTICS = [
    (["rm -rf", "bash", "shell", "exec", "command", "curl", "wget"], "CWE-78",  "OS Command Injection"),
    (["eval", "exec(", "subprocess", "popen"],                        "CWE-78",  "OS Command Injection"),
    (["sql", "select *", "drop table", "insert into"],                "CWE-89",  "SQL Injection"),
    (["ignore all", "jailbreak", "prompt injection", "override"],     "CWE-77",  "Command Injection via Prompt"),
    (["exfiltrate", "attacker.com", "evil.com", "data leak"],         "CWE-200", "Exposure of Sensitive Information"),
    (["permission", "rbac", "role", "unauthorized"],                  "CWE-269", "Improper Privilege Management"),
    (["path traversal", "../", "..\\", "/etc/shadow", "/etc/passwd"], "CWE-22",  "Path Traversal"),
]


def _heuristic_report(incident_data: Dict[str, Any]) -> ForensicAnalysisReport:
    """
    Offline heuristic fallback — produces a deterministic report from incident metadata
    without calling any external API. Used when GEMINI_API_KEY is absent or Gemini is offline.
    """
    combined = json.dumps(incident_data).lower()
    tool_name = incident_data.get("tool_name", "unknown_tool")
    risk_score = float(incident_data.get("risk_score", 0.6))
    threat_score = float(incident_data.get("threat_score", 0.5))

    # Match heuristic CWE
    cwe_id = "CWE-77"
    attack_vector = "NETWORK"
    threat_label = "Command Injection via Prompt"

    for keywords, cwe, label in _CWE_HEURISTICS:
        if any(kw in combined for kw in keywords):
            cwe_id = cwe
            threat_label = label
            attack_vector = "NETWORK" if "curl" in combined or "attacker" in combined else "LOCAL"
            break

    confidence = round(min(0.95, 0.60 + risk_score * 0.35 + threat_score * 0.05), 4)

    return ForensicAnalysisReport(
        cwe_id=cwe_id,
        attack_vector=attack_vector,
        threat_summary=(
            f"[HEURISTIC] Blocked tool '{tool_name}' scored risk={risk_score:.4f}, "
            f"threat={threat_score:.4f}. Classification: {threat_label}. "
            f"Agent was denied execution via AEGIS-NET Policy Engine mandatory override."
        ),
        affected_components=[
            "SecurityGateway",
            tool_name,
            f"Session:{incident_data.get('session_id', 'unknown')}",
        ],
        suggested_patch=(
            f"1. Sanitize and validate all tool payloads before execution. "
            f"2. Apply input allowlisting for '{tool_name}'. "
            f"3. Enforce principle of least privilege for agent roles. "
            f"4. Enable Supabase Realtime alerting for {cwe_id} pattern matches."
        ),
        forensic_confidence=confidence,
    )


async def generate_forensic_report(incident_data: Dict[str, Any]) -> ForensicAnalysisReport:
    """
    Primary forensic analysis function. Slow path — always async.

    Strategy:
      1. If GEMINI_API_KEY is set: call gemini-2.5-flash with structured JSON output.
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

        prompt = (
            f"You are a CISO security analyst performing a CVE post-mortem. "
            f"A multi-agent AI system blocked the following attack envelope. "
            f"Analyze the incident and produce a structured forensic report.\n\n"
            f"Incident Data:\n{json.dumps(incident_data, indent=2)}\n\n"
            f"Provide: CWE ID, attack vector, threat summary, affected components, "
            f"suggested patch, and confidence score (0.0-1.0)."
        )

        model_to_use = getattr(settings, "GEMINI_MODEL", "gemini-3.8-flash")
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
            # Fallback model attempt if primary is unavailable
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
