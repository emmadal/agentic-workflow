"""Generate per-tool agent and skill files from the canonical `.agents/` sources.

Canonical:
  .agents/skills/<name>/SKILL.md   (+ scripts/, references/)   Agent Skills standard
  .agents/agents/<name>.md         name, description, access (read-only | inspect | write)

  .agents/manifest.json  name, version and summary for every plugin manifest

Generated (do not edit):
  .claude/skills/        Claude Code reads skills here; the others read .agents/skills natively
  .claude/agents/        Claude Code subagents
  .opencode/agents/      OpenCode subagents
  .codex/agents/         Codex custom agents (TOML)
  .cursor/agents/        Cursor subagents
  .gemini/agents/        Gemini CLI subagents
  skills/, agents/       plugin and extension root: Claude Code plugin, Codex plugin and
                         Gemini CLI extension load skills/; Gemini loads agents/ (Gemini format)
  .claude-plugin/        Claude Code plugin + marketplace (Codex also reads this marketplace)
  .codex-plugin/         Codex plugin manifest
  .agents/plugins/       Codex marketplace
  gemini-extension.json  Gemini CLI extension manifest

Usage: python -m scripts.sync_agents [--check] [repo_root]
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

from .frontmatter import parse, quote
from .validate_skills import validate_agents, validate_skills

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
        '    "git diff": allow\n'
        '    "git diff --staged": allow\n'
        '    "git status": allow\n'
        '    "git log --oneline -20": allow\n'
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
    "skills",
    "agents",
)
# Byte-for-byte copies of .agents/skills (executable bits preserved).
SKILL_COPIES = (".claude/skills", "skills")
MANIFEST_SOURCE = ".agents/manifest.json"
# Local by-products that must never be copied into generated or installed outputs.
IGNORED_NAMES = {"__pycache__", ".DS_Store", "node_modules"}
IGNORED_SUFFIXES = {".pyc", ".pyo"}


def is_source_file(path: Path) -> bool:
    return (
        path.is_file()
        and path.suffix not in IGNORED_SUFFIXES
        and not IGNORED_NAMES.intersection(path.parts)
    )


def _front(fields: list[tuple[str, str]], extra: str = "") -> str:
    lines = "".join(f"{k}: {v}\n" for k, v in fields)
    return f"---\n{lines}{extra}---\n<!-- {HEADER} -->\n\n"


def render_claude(name: str, desc: str, access: str, body: str) -> str:
    head = _front(
        [
            ("name", quote(name)),
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
    fields = [("name", quote(name)), ("description", quote(desc)), ("model", "inherit")]
    if access != "write":
        fields.append(("readonly", "true"))
    return _front(fields) + body


def render_gemini(name: str, desc: str, access: str, body: str) -> str:
    tools = "tools:\n" + "".join(f"  - {t}\n" for t in GEMINI_TOOLS[access])
    head = _front(
        [("name", quote(name)), ("description", quote(desc)), ("kind", "local")],
        extra=tools,
    )
    return head + body


def render_codex(name: str, desc: str, access: str, body: str) -> str:
    instructions = body.rstrip("\n")
    # Read-only agents get the shell tool disabled; Codex agents cannot change sandbox settings.
    features = "\n[features]\nshell_tool = false\n" if access == "read-only" else ""
    return (
        f"# {HEADER}\n"
        f"name = {quote(name)}\n"
        f"description = {quote(desc)}\n"
        f"developer_instructions = '''\n{instructions}\n'''\n{features}"
    )


AGENT_RENDERERS = {
    ".claude/agents": (".md", render_claude),
    ".opencode/agents": (".md", render_opencode),
    ".cursor/agents": (".md", render_cursor),
    ".gemini/agents": (".md", render_gemini),
    ".codex/agents": (".toml", render_codex),
    # Gemini CLI extensions load sub-agents from <extension root>/agents/.
    "agents": (".md", render_gemini),
}


class SyncError(Exception):
    pass


def _inside(root: Path, rel: str) -> None:
    target = (root / rel).resolve()
    if not target.is_relative_to(root.resolve()):
        raise SyncError(f"output path escapes repository: {rel}")


def _json(data: dict) -> bytes:
    return (json.dumps(data, indent=2, ensure_ascii=False) + "\n").encode()


def load_manifest(root: Path) -> dict:
    path = root / MANIFEST_SOURCE
    try:
        meta = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise SyncError(f"cannot read {MANIFEST_SOURCE}: {exc}") from exc
    required = {"name", "displayName", "version", "summary", "highlights", "author", "homepage"}
    missing = sorted(required - set(meta))
    if missing:
        raise SyncError(f"{MANIFEST_SOURCE} is missing: {', '.join(missing)}")
    return meta


def render_manifests(meta: dict, skills: int, agents: list[str]) -> dict[str, bytes]:
    """Plugin and extension manifests for Claude Code, Codex and Gemini CLI."""
    name, version = meta["name"], meta["version"]
    desc = f"{skills} skills and {len(agents)} role agents: {meta['highlights']}."
    common = {
        "author": meta["author"],
        "homepage": meta["homepage"],
        "repository": meta.get("repository", meta["homepage"]),
        "keywords": meta.get("keywords", []),
    }
    claude_plugin = {
        "name": name,
        "version": version,
        "description": desc,
        **common,
        # Skills load from the default skills/ directory. `agents` replaces the default
        # agents/ directory, which holds the Gemini-format copies.
        "agents": [f"./.claude/agents/{a}.md" for a in agents],
    }
    entry = {"name": name, "version": version, "source": "./", "description": desc}
    claude_market = {
        "$schema": "https://json.schemastore.org/claude-code-marketplace.json",
        "name": name,
        "description": meta["summary"],
        "owner": meta["author"],
        "plugins": [{**entry, "homepage": meta["homepage"], "keywords": common["keywords"]}],
    }
    codex_plugin = {
        "name": name,
        "version": version,
        "description": desc,
        **common,
        "skills": "./skills/",
        "interface": {
            "displayName": meta["displayName"],
            "shortDescription": meta["summary"],
            "longDescription": desc,
            "developerName": meta["author"]["name"],
            "category": "Coding",
            "websiteURL": meta["homepage"],
        },
    }
    codex_market = {
        "name": name,
        "interface": {"displayName": meta["displayName"]},
        "plugins": [{**entry, "category": "Coding"}],
    }
    gemini = {
        "name": name,
        "version": version,
        "description": desc,
        "contextFileName": "GEMINI.md",
    }
    return {
        ".claude-plugin/plugin.json": _json(claude_plugin),
        ".claude-plugin/marketplace.json": _json(claude_market),
        ".codex-plugin/plugin.json": _json(codex_plugin),
        ".agents/plugins/marketplace.json": _json(codex_market),
        "gemini-extension.json": _json(gemini),
    }


def expected_files(root: Path) -> dict[str, bytes]:
    """Return {relative path: content} for every generated file. Validates sources first."""
    errors = validate_skills(root) + validate_agents(root)
    if errors:
        raise SyncError("invalid sources:\n" + "\n".join(f"  {e}" for e in errors))
    out: dict[str, bytes] = {}
    agent_names: list[str] = []
    for src in sorted((root / ".agents" / "agents").glob("*.md")):
        doc = parse(src.read_text())
        name, desc, access = doc.meta["name"], doc.meta["description"], doc.meta["access"]
        agent_names.append(name)
        for directory, (ext, render) in AGENT_RENDERERS.items():
            rel = f"{directory}/{name}{ext}"
            _inside(root, rel)
            out[rel] = render(name, desc, access, doc.body).encode()

    skills = root / ".agents" / "skills"
    for file in sorted(p for p in skills.rglob("*") if is_source_file(p)):
        for copy in SKILL_COPIES:
            rel = f"{copy}/{file.relative_to(skills).as_posix()}"
            _inside(root, rel)
            out[rel] = file.read_bytes()
    skill_count = sum(1 for p in skills.iterdir() if (p / "SKILL.md").is_file())
    out.update(render_manifests(load_manifest(root), skill_count, agent_names))
    return out


def existing_files(root: Path) -> set[str]:
    found: set[str] = set()
    for directory in OUTPUT_DIRS:
        base = root / directory
        if base.is_dir():
            found |= {p.relative_to(root).as_posix() for p in base.rglob("*") if is_source_file(p)}
    return found


def check(root: Path) -> list[str]:
    expected = expected_files(root)
    present = existing_files(root)
    problems = [f"missing: {p}" for p in sorted(expected) if not (root / p).is_file()]
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
        copy = next((c for c in SKILL_COPIES if rel.startswith(f"{c}/")), None)
        if copy:
            source = root / ".agents" / "skills" / rel.removeprefix(f"{copy}/")
            path.chmod(source.stat().st_mode & 0o777)
    return len(expected)


def main(argv: list[str]) -> int:
    args = [a for a in argv[1:] if a != "--check"]
    root = Path(args[0]) if args else Path(__file__).resolve().parent.parent
    try:
        return _run(argv, root)
    except SyncError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


def _run(argv: list[str], root: Path) -> int:
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
