"""
AEGIS-NET Tool Sandbox.
Strictly confines all tool operations inside backend/agent_workspace.
Prevents path traversal and enforces execution timeouts.
"""
import logging
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, Optional, Union

logger = logging.getLogger(__name__)

# Strict workspace root — all paths must resolve to within this directory
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
WORKSPACE_ROOT = (BACKEND_DIR / "agent_workspace").resolve()

# Ensure workspace exists
WORKSPACE_ROOT.mkdir(parents=True, exist_ok=True)

EXEC_TIMEOUT_SEC = 5


<<<<<<< HEAD
def _safe_resolve(relative_path: str, session_id: Optional[str] = None) -> Path:
    """
    Resolve a relative path against WORKSPACE_ROOT (or workspace/session_id) and validate containment.
    Raises PermissionError on any traversal attempt.
    """
    base_dir = WORKSPACE_ROOT
    if session_id and session_id.strip():
        # Sanitize session_id to prevent traversal in session name
        safe_session_name = Path(session_id.strip()).name
        base_dir = WORKSPACE_ROOT / safe_session_name
        base_dir.mkdir(parents=True, exist_ok=True)

    # Sanitize leading slashes
    clean_rel = relative_path.lstrip("/\\")
    candidate = (base_dir / clean_rel).resolve()

    # Block absolute paths pointing outside workspace boundary
=======
def _safe_resolve(relative_path: str) -> Path:
    """
    Resolve a relative path against WORKSPACE_ROOT and validate containment.
    Raises PermissionError on any traversal attempt.
    """
    candidate = (WORKSPACE_ROOT / relative_path).resolve()

    # Block absolute paths pointing outside workspace
>>>>>>> 269c4536791406ae7200b6f0aced48c638234a60
    try:
        candidate.relative_to(WORKSPACE_ROOT)
    except ValueError:
        raise PermissionError(
<<<<<<< HEAD
            f"Path traversal blocked: '{relative_path}' resolves outside workspace boundary ({WORKSPACE_ROOT})."
=======
            f"Path traversal blocked: '{relative_path}' resolves outside workspace boundary. "
            f"All operations must stay within '{WORKSPACE_ROOT}'."
>>>>>>> 269c4536791406ae7200b6f0aced48c638234a60
        )

    return candidate


<<<<<<< HEAD
def sandbox_read_file(relative_path: str, session_id: Optional[str] = None) -> Dict[str, Any]:
    """Read a file strictly within the sandboxed agent_workspace."""
    try:
        safe_path = _safe_resolve(relative_path, session_id=session_id)
    except PermissionError as pe:
        return {"error": str(pe), "path": relative_path}
=======
def sandbox_read_file(relative_path: str) -> Dict[str, Any]:
    """Read a file strictly within the agent_workspace sandbox."""
    safe_path = _safe_resolve(relative_path)
>>>>>>> 269c4536791406ae7200b6f0aced48c638234a60

    if not safe_path.exists():
        return {"error": f"File not found: {relative_path}", "path": str(safe_path)}

    if not safe_path.is_file():
        return {"error": f"Path is not a file: {relative_path}"}

    content = safe_path.read_text(encoding="utf-8", errors="replace")
<<<<<<< HEAD
    stat = safe_path.stat()
    return {
        "content": content,
        "path": relative_path,
        "bytes": len(content),
        "created_at": time.ctime(stat.st_ctime),
        "modified_at": time.ctime(stat.st_mtime),
    }


def sandbox_write_file(relative_path: str, content: str, session_id: Optional[str] = None) -> Dict[str, Any]:
    """Write a file strictly within the sandboxed agent_workspace."""
    try:
        safe_path = _safe_resolve(relative_path, session_id=session_id)
    except PermissionError as pe:
        return {"error": str(pe), "path": relative_path}

    safe_path.parent.mkdir(parents=True, exist_ok=True)
    safe_path.write_text(content, encoding="utf-8")
    stat = safe_path.stat()
    return {
        "written": True,
        "path": relative_path,
        "bytes": len(content),
        "created_at": time.ctime(stat.st_ctime),
        "modified_at": time.ctime(stat.st_mtime),
    }


def sandbox_list_directory(relative_path: str = ".", session_id: Optional[str] = None) -> Dict[str, Any]:
    """List directory contents strictly within the sandboxed agent_workspace."""
    try:
        safe_path = _safe_resolve(relative_path, session_id=session_id)
    except PermissionError as pe:
        return {"error": str(pe), "path": relative_path}

    if not safe_path.exists():
        return {"error": f"Directory not found: {relative_path}", "entries": []}

    if not safe_path.is_dir():
        return {"error": f"Path is not a directory: {relative_path}", "entries": []}

    def _build_tree(dir_path: Path, base_rel: Path) -> list:
        entries = []
        for e in sorted(dir_path.iterdir()):
            rel = str(e.relative_to(base_rel))
            stat = e.stat()
            if e.is_dir():
                entries.append({
                    "name": e.name,
                    "path": rel,
                    "type": "dir",
                    "children": _build_tree(e, base_rel),
                })
            else:
                entries.append({
                    "name": e.name,
                    "path": rel,
                    "type": "file",
                    "size": stat.st_size,
                    "modified_at": time.ctime(stat.st_mtime),
                })
        return entries

    base_dir = WORKSPACE_ROOT / (Path(session_id).name if session_id else "")
    if not base_dir.exists():
        base_dir.mkdir(parents=True, exist_ok=True)

    entries = _build_tree(safe_path, base_dir)
    return {"path": relative_path, "session_id": session_id, "entries": entries}


def sandbox_execute_command(command: str, timeout: int = EXEC_TIMEOUT_SEC, session_id: Optional[str] = None) -> Dict[str, Any]:
=======
    return {"content": content, "path": relative_path, "bytes": len(content)}


def sandbox_write_file(relative_path: str, content: str) -> Dict[str, Any]:
    """Write a file strictly within the agent_workspace sandbox."""
    safe_path = _safe_resolve(relative_path)
    safe_path.parent.mkdir(parents=True, exist_ok=True)
    safe_path.write_text(content, encoding="utf-8")
    return {"written": True, "path": relative_path, "bytes": len(content)}


def sandbox_list_directory(relative_path: str = ".") -> Dict[str, Any]:
    """List directory contents strictly within the agent_workspace sandbox."""
    safe_path = _safe_resolve(relative_path)

    if not safe_path.exists():
        return {"error": f"Directory not found: {relative_path}"}

    if not safe_path.is_dir():
        return {"error": f"Path is not a directory: {relative_path}"}

    entries = [
        {"name": e.name, "type": "dir" if e.is_dir() else "file", "size": e.stat().st_size if e.is_file() else None}
        for e in sorted(safe_path.iterdir())
    ]
    return {"path": relative_path, "entries": entries}


def sandbox_execute_command(command: str, timeout: int = EXEC_TIMEOUT_SEC) -> Dict[str, Any]:
>>>>>>> 269c4536791406ae7200b6f0aced48c638234a60
    """
    Execute a command with strict timeout, sandboxed CWD within agent_workspace.
    Completely disallows shell metacharacter injection by using list form.
    """
    start = time.perf_counter()
<<<<<<< HEAD
    cwd = WORKSPACE_ROOT
    if session_id:
        cwd = WORKSPACE_ROOT / Path(session_id).name
        cwd.mkdir(parents=True, exist_ok=True)

    try:
        result = subprocess.run(
            command if isinstance(command, list) else command.split(),
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=False,
=======
    try:
        result = subprocess.run(
            command if isinstance(command, list) else command.split(),
            cwd=str(WORKSPACE_ROOT),
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=False,  # Never use shell=True — prevents injection
>>>>>>> 269c4536791406ae7200b6f0aced48c638234a60
        )
        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "latency_ms": elapsed_ms,
        }
    except subprocess.TimeoutExpired:
        return {"error": f"Command timed out after {timeout}s", "stdout": "", "stderr": ""}
    except Exception as e:
        return {"error": str(e), "stdout": "", "stderr": ""}
