"""
AEGIS-NET Forensic Analysis Schemas.
Structured Pydantic model for Gemini CISO forensic output.
All seven analysis sections required by the incident investigation contract.
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class ForensicAnalysisReport(BaseModel):
    """
    Structured CVE post-mortem produced by the Gemini CISO engine.
    Maps directly to forensics_reports Supabase table schema.
    """
    cwe_id: str = Field(..., description="CWE identifier (e.g. CWE-77, CWE-89)")
    attack_vector: str = Field(..., description="Attack vector description (e.g. NETWORK, LOCAL)")

    # Section 1: Incident Summary
    incident_summary: str = Field(
        default="", description="High-level executive summary of what happened"
    )

    # Section 2: Why the action was suspicious
    suspicion_reasoning: str = Field(
        default="", description="Detailed explanation of why the agent action raised alarms"
    )

    # Section 3: Attack / threat indicators
    threat_indicators: List[str] = Field(
        default_factory=list, description="Specific observable indicators of compromise or attack intent"
    )

    # Section 4: Context and behavioral anomalies
    behavioral_anomalies: str = Field(
        default="", description="Description of behavioral deviations from the expected agent baseline"
    )

    # Section 5: Potential impact
    potential_impact: str = Field(
        default="", description="Assessment of the potential damage if the action had not been blocked"
    )

    # Section 6: Recommended response
    recommended_response: str = Field(
        default="", description="Concrete, actionable security response recommendations"
    )

    # Section 7: Confidence / uncertainty
    forensic_confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Model confidence in this forensic assessment [0.0–1.0]"
    )
    confidence_notes: str = Field(
        default="", description="Explanation of confidence level and areas of uncertainty"
    )

    # Legacy fields retained for backward compat with Supabase schema
    threat_summary: str = Field(default="", description="Human-readable threat analysis summary")
    affected_components: List[str] = Field(
        default_factory=list, description="List of impacted system components"
    )
    suggested_patch: str = Field(
        default="", description="Concrete mitigation or patch recommendation"
    )
