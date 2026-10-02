"""
AEGIS-NET Filesystem Tool.
Safe file operations strictly sandboxed within backend/agent_workspace.
All path resolution enforces sandbox containment via sandbox.py.
"""
from pathlib import Path
from typing import Any, Dict, Optional

from app.containment.sandbox import (
    sandbox_read_file,
    sandbox_write_file,
    sandbox_list_directory,
    WORKSPACE_ROOT,
    _safe_resolve,
)


def read_workspace_file(path: str) -> Dict[str, Any]:
    """Read a file from the sandboxed agent_workspace."""
    return sandbox_read_file(path)


def write_workspace_file(path: str, content: str) -> Dict[str, Any]:
    """Write a file to the sandboxed agent_workspace."""
    return sandbox_write_file(path, content)


def list_workspace_directory(path: str = ".") -> Dict[str, Any]:
    """List directory contents within the sandboxed agent_workspace."""
    return sandbox_list_directory(path)


def validate_path(path: str) -> Dict[str, Any]:
    """
    Validate a path for workspace containment without performing I/O.
    Returns containment status and resolved path.
    """
    try:
        resolved = _safe_resolve(path)
        return {
            "safe": True,
            "resolved_path": str(resolved),
            "workspace_root": str(WORKSPACE_ROOT),
        }
    except PermissionError as e:
        return {
            "safe": False,
            "error": str(e),
            "workspace_root": str(WORKSPACE_ROOT),
        }
