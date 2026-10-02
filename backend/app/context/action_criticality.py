"""
AEGIS-NET Action Criticality Evaluation (C).
Scores operational criticality and irreversibility of requested actions.
Scale: C in [0.1, 1.0]
"""

from typing import Dict

# Explicit mappings of known tool actions to criticality scores
ACTION_CRITICALITY_MAP: Dict[str, float] = {
    # READ: 0.1
    "search_docs": 0.1,
    "fetch_web_content": 0.1,
    "read_workspace_file": 0.1,
    "get_deploy_status": 0.1,
    "list_directory": 0.1,
    "status_check": 0.1,

    # WRITE_LOCAL: 0.4
    "write_workspace_file": 0.4,
    "create_file": 0.4,
    "modify_file": 0.4,
    "delete_file": 0.4,

    # EXECUTE_COMMAND: 0.7
    "execute_command": 0.7,
    "run_local_tests": 0.7,
    "run_script": 0.7,
    "shell_exec": 0.7,

    # DEPLOY_PRODUCTION: 0.9
    "deploy_service": 0.9,
    "build_artifact": 0.9,
    "publish_package": 0.9,

    # SECRET_ACCESS / DROP: 1.0
    "read_system_secrets": 1.0,
    "rollback_deployment": 1.0,
    "drop_database": 1.0,
    "format_disk": 1.0,
    "grant_permission": 1.0,
}


def evaluate_action_criticality(tool_name: str) -> float:
    """
    Returns the action criticality score C in [0.1, 1.0] for the specified tool.
    Defaults to 0.7 for unrecognized active tools and 0.1 for read-only patterns.
    """
    clean_tool = tool_name.strip().lower()
    
    if clean_tool in ACTION_CRITICALITY_MAP:
        return ACTION_CRITICALITY_MAP[clean_tool]

    # Heuristic fallback
    if any(keyword in clean_tool for keyword in ["read", "get", "fetch", "search", "list"]):
        return 0.1
    if any(keyword in clean_tool for keyword in ["write", "update", "create"]):
        return 0.4
    if any(keyword in clean_tool for keyword in ["exec", "command", "run", "bash"]):
        return 0.7
    if any(keyword in clean_tool for keyword in ["deploy", "build", "release"]):
        return 0.9
    if any(keyword in clean_tool for keyword in ["secret", "key", "drop", "purge", "root"]):
        return 1.0

    return 0.5
