"""
AEGIS-NET Forensic Analysis Schemas.
Structured Pydantic model for Gemini CISO forensic output.
"""
from typing import List
from pydantic import BaseModel, Field


class ForensicAnalysisReport(BaseModel):
    """
    Structured CVE post-mortem produced by the Gemini CISO engine.
    Maps directly to forensics_reports Supabase table schema.
    """
    cwe_id: str = Field(..., description="CWE identifier (e.g. CWE-77, CWE-89)")
    attack_vector: str = Field(..., description="Attack vector description (e.g. NETWORK, LOCAL)")
    threat_summary: str = Field(..., description="Human-readable threat analysis summary")
    affected_components: List[str] = Field(..., description="List of impacted system components")
    suggested_patch: str = Field(..., description="Concrete mitigation or patch recommendation")
    forensic_confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Model confidence in this forensic assessment [0.0–1.0]"
    )
