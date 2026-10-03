"""
AEGIS-NET Security Proxy Exceptions.
Defines security interception, quarantine, and policy violation exception hierarchies.
"""

from typing import Optional, Dict, Any


class SecurityProxyException(Exception):
    """Base exception for all security proxy interception events."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class SecurityProxyBlockException(SecurityProxyException):
    """Raised when the security proxy unconditionally blocks a high-risk or prohibited tool invocation."""

    def __init__(
        self,
        message: str = "Tool invocation blocked by Zero-Trust Security Proxy.",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, details)


class SecurityProxyReviewException(SecurityProxyException):
    """Raised when an operation is suspended pending human-in-the-loop review."""

    def __init__(
        self,
        message: str = "Tool invocation held pending administrative review.",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, details)


class SessionQuarantinedException(SecurityProxyException):
    """Raised when an agent session is under active quarantine containment."""

    def __init__(
        self,
        message: str = "Agent session is quarantined. All tool operations prohibited.",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, details)


class SessionNotFoundException(SecurityProxyException):
    """Raised when an unrecognized session UUID is provided."""

    def __init__(
        self,
        message: str = "Session not found or invalid session token.",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, details)


class PolicyViolationException(SecurityProxyException):
    """Raised on strict RBAC boundary violations."""

    def __init__(
        self,
        message: str = "Operation violates role-based access policy.",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, details)
