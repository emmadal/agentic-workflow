"""Generate per-tool agent and skill files from the canonical `.agents/` sources.

Canonical:
  .agents/skills/<name>/SKILL.md   (+ scripts/, references/)   Agent Skills standard
  .agents/agents/<name>.md         name, description, access (read-only | inspect | write)

Generated (do not edit):
  .claude/skills/        Claude Code reads skills here; the others read .agents/skills natively
  .claude/agents/        Claude Code subagents
  .opencode/agents/      OpenCode subagents
  .codex/agents/         Codex custom agents (TOML)
  .cursor/agents/        Cursor subagents
  .gemini/agents/        Gemini CLI subagents

Usage: python -m scripts.sync_agents [--check] [repo_root]
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

from .frontmatter import parse, quote

HEADER = (
    "GENERATED from .agents/ by scripts/sync_agents.py. Do not edit; edit the source and re-run."
)

CLAUDE_MODEL = "opus"
CLAUDE_TOOLS = {
    "read-only": "Read, Grep, Glob",
    "inspect": "Read, Grep, Glob, Bash",
    "write": "Read, Grep, Glob, Edit, Write, Bash",
}
GEMINI_TOOLS = {
    "read-only": ["read_file", "list_directory", "glob", "grep_search"],
    "inspect": ["read_file", "list_directory", "glob", "grep_search", "run_shell_command"],
    "write": [
        "read_file",
        "list_directory",
        "glob",
        "grep_search",
        "write_file",
        "replace",
        "run_shell_command",
    ],
}
OPENCODE_PERMISSION = {
    "read-only": "  edit: deny\n  bash: deny\n",
    "inspect": (
        "  edit: deny\n"
        "  bash:\n"
        '    "*": ask\n'
        '    "git diff*": allow\n'
        '    "git log*": allow\n'
        '    "git show*": allow\n'
        '    "git status*": allow\n'
    ),
    "write": "  edit: allow\n  bash: ask\n",
}

# Directories fully owned by the generator.
OUTPUT_DIRS = (
    ".claude/skills",
    ".claude/agents",
    ".opencode/agents",
    ".codex/agents",
    ".cursor/agents",
    ".gemini/agents",
)


def _front(fields: list[tuple[str, str]], extra: str = "") -> str:
    lines = "".join(f"{k}: {v}\n" for k, v in fields)
    return f"---\n{lines}{extra}---\n<!-- {HEADER} -->\n\n"


def render_claude(name: str, desc: str, access: str, body: str) -> str:
    head = _front(
        [
            ("name", name),
            ("description", quote(desc)),
            ("model", CLAUDE_MODEL),
            ("tools", CLAUDE_TOOLS[access]),
        ]
    )
    return head + body


def render_opencode(name: str, desc: str, access: str, body: str) -> str:
    head = _front(
        [("description", quote(desc)), ("mode", "subagent")],
        extra="permission:\n" + OPENCODE_PERMISSION[access],
    )
    return head + body


def render_cursor(name: str, desc: str, access: str, body: str) -> str:
    fields = [("name", name), ("description", quote(desc)), ("model", "inherit")]
    if access != "write":
        fields.append(("readonly", "true"))
    return _front(fields) + body


def render_gemini(name: str, desc: str, access: str, body: str) -> str:
    tools = "tools:\n" + "".join(f"  - {t}\n" for t in GEMINI_TOOLS[access])
    head = _front(
        [("name", name), ("description", quote(desc)), ("kind", "local")],
        extra=tools,
    )
    return head + body


def render_codex(name: str, desc: str, access: str, body: str) -> str:
    instructions = body.rstrip("\n")
    return (
        f"# {HEADER}\n"
        f"name = {quote(name)}\n"
        f"description = {quote(desc)}\n"
        f"developer_instructions = '''\n{instructions}\n'''\n"
    )


AGENT_RENDERERS = {
    ".claude/agents": (".md", render_claude),
    ".opencode/agents": (".md", render_opencode),
    ".cursor/agents": (".md", render_cursor),
    ".gemini/agents": (".md", render_gemini),
    ".codex/agents": (".toml", render_codex),
}


def expected_files(root: Path) -> dict[str, bytes]:
    """Return {relative path: content} for every generated file."""
    out: dict[str, bytes] = {}
    for src in sorted((root / ".agents" / "agents").glob("*.md")):
        doc = parse(src.read_text())
        name, desc, access = doc.meta["name"], doc.meta["description"], doc.meta["access"]
        for directory, (ext, render) in AGENT_RENDERERS.items():
            out[f"{directory}/{name}{ext}"] = render(name, desc, access, doc.body).encode()

    skills = root / ".agents" / "skills"
    for file in sorted(p for p in skills.rglob("*") if p.is_file()):
        out[f".claude/skills/{file.relative_to(skills).as_posix()}"] = file.read_bytes()
    return out


def existing_files(root: Path) -> set[str]:
    found: set[str] = set()
    for directory in OUTPUT_DIRS:
        base = root / directory
        if base.is_dir():
            found |= {p.relative_to(root).as_posix() for p in base.rglob("*") if p.is_file()}
    return found


def check(root: Path) -> list[str]:
    expected = expected_files(root)
    present = existing_files(root)
    problems = [f"missing: {p}" for p in sorted(set(expected) - present)]
    problems += [f"stale: {p}" for p in sorted(present - set(expected))]
    for rel, content in expected.items():
        path = root / rel
        if path.is_file() and path.read_bytes() != content:
            problems.append(f"out of date: {rel}")
    return problems


def sync(root: Path) -> int:
    expected = expected_files(root)
    for directory in OUTPUT_DIRS:
        shutil.rmtree(root / directory, ignore_errors=True)
    for rel, content in expected.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        if rel.startswith(".claude/skills/"):
            source = root / ".agents" / "skills" / rel.removeprefix(".claude/skills/")
            path.chmod(source.stat().st_mode & 0o777)
    return len(expected)


def main(argv: list[str]) -> int:
    args = [a for a in argv[1:] if a != "--check"]
    root = Path(args[0]) if args else Path(__file__).resolve().parent.parent
    if "--check" in argv:
        problems = check(root)
        for problem in problems:
            print(f"error: {problem}", file=sys.stderr)
        if problems:
            print("run: python -m scripts.sync_agents", file=sys.stderr)
        return 1 if problems else 0
    print(f"generated {sync(root)} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
