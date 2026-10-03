"""
AEGIS-NET Policy Decision Schemas.
"""
from typing import List, Optional
from pydantic import BaseModel


class PolicyDecision(BaseModel):
    decision: str  # ALLOW | REVIEW | BLOCK
    reasons: List[str]
    risk_score: float = 0.0
    threat_score: float = 0.0
    mandatory_override: bool = False


class DecisionExplanation(BaseModel):
    decision: str
    reasons: List[str]
    risk_score: float
    threat_score: float
    mandatory_override: bool
    factors: dict
    context: Optional[dict] = None
