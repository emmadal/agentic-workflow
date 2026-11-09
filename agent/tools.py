"""Sandboxed tools for the agent loop. All paths are confined to a workdir."""

from __future__ import annotations

import subprocess
from collections.abc import Callable
from pathlib import Path

ToolFn = Callable[..., str]

MAX_OUTPUT = 20_000


class ToolError(Exception):
    pass


def _resolve(workdir: Path, rel: str) -> Path:
    path = (workdir / rel).resolve()
    if not path.is_relative_to(workdir.resolve()):
        raise ToolError(f"path escapes workdir: {rel}")
    return path


def read_file(workdir: Path, path: str) -> str:
    return _resolve(workdir, path).read_text()[:MAX_OUTPUT]


def list_dir(workdir: Path, path: str = ".") -> str:
    target = _resolve(workdir, path)
    return "\n".join(sorted(p.name + ("/" if p.is_dir() else "") for p in target.iterdir()))


def write_file(workdir: Path, path: str, content: str) -> str:
    target = _resolve(workdir, path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content)
    return f"wrote {len(content)} bytes to {path}"


def run_tests(workdir: Path) -> str:
    proc = subprocess.run(
        ["pytest", "-q", "--maxfail=5"],
        cwd=workdir,
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
