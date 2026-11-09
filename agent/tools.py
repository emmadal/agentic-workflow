"""Sandboxed tools for the agent loop. All paths are confined to a workdir.

Write access and test execution are code execution. They are opt-in at the CLI.
"""

from __future__ import annotations

import os
import subprocess
from collections.abc import Callable
from pathlib import Path

ToolFn = Callable[..., str]

MAX_OUTPUT = 20_000
MAX_ENTRIES = 500

# Paths the model may never read or write (checked on every path component).
BLOCKED_NAMES = {
    ".git",
    ".claude",
    ".env",
    "conftest.py",
    "pyproject.toml",
    "setup.cfg",
    "setup.py",
    "pytest.ini",
    "tox.ini",
    "id_rsa",
    "id_ed25519",
}
BLOCKED_PREFIXES = (".env",)
BLOCKED_SUFFIXES = (".pem", ".key", ".p12")

SAFE_ENV_KEYS = ("PATH", "HOME", "LANG", "LC_ALL", "VIRTUAL_ENV")


class ToolError(Exception):
    pass


def _resolve(workdir: Path, rel: str) -> Path:
    root = workdir.resolve()
    path = (root / rel).resolve()
    if not path.is_relative_to(root):
        raise ToolError(f"path escapes workdir: {rel}")
    for part in path.relative_to(root).parts:
        lower = part.lower()
        if (
            lower in BLOCKED_NAMES
            or lower.startswith(BLOCKED_PREFIXES)
            or lower.endswith(BLOCKED_SUFFIXES)
        ):
            raise ToolError(f"path not allowed: {rel}")
    return path


def read_file(workdir: Path, path: str) -> str:
    target = _resolve(workdir, path)
    if not target.is_file():
        raise ToolError(f"not a regular file: {path}")
    with target.open(errors="replace") as f:
        return f.read(MAX_OUTPUT)


def list_dir(workdir: Path, path: str = ".") -> str:
    target = _resolve(workdir, path)
    if not target.is_dir():
        raise ToolError(f"not a directory: {path}")
    names = sorted(p.name + ("/" if p.is_dir() else "") for p in target.iterdir())
    visible = [n for n in names if n.rstrip("/").lower() not in BLOCKED_NAMES]
    return "\n".join(visible[:MAX_ENTRIES])


def write_file(workdir: Path, path: str, content: str) -> str:
    target = _resolve(workdir, path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content)
    return f"wrote {len(content)} bytes to {path}"


def run_tests(workdir: Path) -> str:
    env = {k: os.environ[k] for k in SAFE_ENV_KEYS if k in os.environ}
    proc = subprocess.run(
        ["pytest", "-q", "--maxfail=5"],
        cwd=workdir,
        env=env,
        capture_output=True,
        text=True,
        timeout=300,
    )
    return (proc.stdout + proc.stderr)[-MAX_OUTPUT:]


# name -> (function, JSON schema for the model)
REGISTRY: dict[str, tuple[ToolFn, dict]] = {
    "read_file": (
        read_file,
        {
            "name": "read_file",
            "description": "Read a text file inside the workdir.",
            "input_schema": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
        },
    ),
    "list_dir": (
        list_dir,
        {
            "name": "list_dir",
            "description": "List entries of a directory inside the workdir.",
            "input_schema": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
            },
        },
    ),
    "write_file": (
        write_file,
        {
            "name": "write_file",
            "description": "Write a text file inside the workdir.",
            "input_schema": {
                "type": "object",
                "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
                "required": ["path", "content"],
            },
        },
    ),
    "run_tests": (
        run_tests,
        {
            "name": "run_tests",
            "description": "Run the project test suite and return the output.",
            "input_schema": {"type": "object", "properties": {}},
        },
    ),
}

READ_ONLY = ("read_file", "list_dir")
