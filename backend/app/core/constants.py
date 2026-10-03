"""
AEGIS-NET System Constants, Enums, and Error Codes.
Defines system states, security decision classifications, incident severities, and error codes.
"""

from enum import Enum


class Decision(str, Enum):
    """Tri-state policy access decision."""
    ALLOW = "ALLOW"
    REVIEW = "REVIEW"
    BLOCK = "BLOCK"


class ToolCallStatus(str, Enum):
    """Status lifecycle of a tool call under proxy control."""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXECUTED = "EXECUTED"
    FAILED = "FAILED"


class AgentStatus(str, Enum):
    """Operational status of an autonomous agent."""
    ACTIVE = "ACTIVE"
    QUARANTINED = "QUARANTINED"
    TERMINATED = "TERMINATED"
    SUSPENDED = "SUSPENDED"


class IncidentSeverity(str, Enum):
    """Severity classification for security incidents."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class IncidentStatus(str, Enum):
    """Status tracking for security incidents."""
    OPEN = "OPEN"
    INVESTIGATING = "INVESTIGATING"
    RESOLVED = "RESOLVED"
    FALSE_POSITIVE = "FALSE_POSITIVE"


class SecurityEventType(str, Enum):
    """Categories of security telemetry events."""
    POLICY_VIOLATION = "POLICY_VIOLATION"
    PROMPT_INJECTION = "PROMPT_INJECTION"
    CIRCUIT_BREAKER_TRIGGERED = "CIRCUIT_BREAKER_TRIGGERED"
    UNAUTHORIZED_ACCESS = "UNAUTHORIZED_ACCESS"
    ANOMALOUS_BEHAVIOR = "ANOMALOUS_BEHAVIOR"
    QUARANTINE_ACTION = "QUARANTINE_ACTION"


class QuarantineStatus(str, Enum):
    """Status of an agent quarantine record."""
    ACTIVE = "ACTIVE"
    RELEASED = "RELEASED"
    EXPIRED = "EXPIRED"


# Standardized System Error Codes
class ErrorCode:
    ERR_UNAUTHORIZED = "ERR_UNAUTHORIZED"
    ERR_PERMISSION_DENIED = "ERR_PERMISSION_DENIED"
    ERR_AGENT_QUARANTINED = "ERR_AGENT_QUARANTINED"
    ERR_HIGH_RISK_BLOCKED = "ERR_HIGH_RISK_BLOCKED"
    ERR_TOOL_NOT_FOUND = "ERR_TOOL_NOT_FOUND"
    ERR_DATABASE_CONNECTION = "ERR_DATABASE_CONNECTION"
    ERR_INVALID_PAYLOAD = "ERR_INVALID_PAYLOAD"
    ERR_CIRCUIT_BREAKER_OPEN = "ERR_CIRCUIT_BREAKER_OPEN"
    ERR_INTERNAL_SERVER = "ERR_INTERNAL_SERVER"
