"""
AEGIS-NET Resource Sensitivity Evaluation (S).
Classifies data and resource targets across a 4-tier zero-trust sensitivity model.
Scale: S in [0.1, 1.0]
- PUBLIC (0.1): Documentation, README, public search indexes.
- INTERNAL (0.4): Application source code, local build artifacts, app configurations.
- SENSITIVE (0.7): Production database tables, credentials, customer data, runtime environment variables.
- CRITICAL (1.0): Cloud IAM, system private keys, OS root files (/etc/shadow, /etc/passwd, C:\\Windows\\System32).
"""

import json
from typing import Any, Dict, Union

CRITICAL_PATTERNS = [
    "/etc/shadow",
    "/etc/passwd",
    "system32",
    "id_rsa",
    "id_ed25519",
    ".aws/credentials",
    "private_key",
    "service_role",
    "master_key",
    "disk_root",
    "rm -rf /",
    "samdb",
    "ntds.dit",
]

SENSITIVE_PATTERNS = [
    ".env",
    "database",
    "supabase_key",
    "api_key",
    "token",
    "password",
    "secret",
    "credentials",
    "session_secret",
    "pg_dump",
    "user_table",
    "customers",
]

PUBLIC_PATTERNS = [
    "docs",
    "readme",
    "documentation",
    "public",
    "help",
    "search_docs",
    "guide",
    "tutorial",
]


def evaluate_resource_sensitivity(payload: Union[str, Dict[str, Any], Any]) -> float:
    """
    Evaluates target resource sensitivity S from the given payload / arguments.
    Returns float in range [0.1, 1.0].
    """
    if isinstance(payload, dict):
        text_content = json.dumps(payload).lower()
    else:
        text_content = str(payload).lower()

    # 1. Critical Tier (1.0)
    for pattern in CRITICAL_PATTERNS:
        if pattern in text_content:
            return 1.0

    # 2. Sensitive Tier (0.7)
    for pattern in SENSITIVE_PATTERNS:
        if pattern in text_content:
            return 0.7

    # 3. Public Tier (0.1)
    if any(pattern in text_content for pattern in PUBLIC_PATTERNS):
        return 0.1

    # 4. Internal Default (0.4) for standard workspace source files
    return 0.4
