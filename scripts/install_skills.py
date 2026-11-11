"""Install skills and agents from this repo into another project.

Usage: python -m scripts.install_skills TARGET [--tool claude|opencode|cursor|codex|gemini|all]
                                        [--force] [--dry-run]

Copies generated files only. Never touches the target's AGENTS.md, CLAUDE.md or settings.
Existing files are kept unless --force is given.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .sync_agents import SyncError, expected_files, is_source_file

TOOLS = {
    "claude": (".claude/skills/", ".claude/agents/"),
    "opencode": (".agents/skills/", ".opencode/agents/"),
    "cursor": (".agents/skills/", ".cursor/agents/"),
    "codex": (".agents/skills/", ".codex/agents/"),
    "gemini": (".agents/skills/", ".gemini/agents/"),
}


def plan(root: Path, tools: list[str]) -> dict[str, bytes]:
    """Return {relative path: content} to install for the given tools."""
    generated = expected_files(root)
    out: dict[str, bytes] = {}
    for tool in tools:
        skills_dir, agents_dir = TOOLS[tool]
        if skills_dir == ".agents/skills/":
            src = root / ".agents" / "skills"
            for file in sorted(p for p in src.rglob("*") if is_source_file(p)):
                out[f"{skills_dir}{file.relative_to(src).as_posix()}"] = file.read_bytes()
        for rel, content in generated.items():
            if rel.startswith(skills_dir) or rel.startswith(agents_dir):
                out[rel] = content
    return out


def install(root: Path, target: Path, tools: list[str], force: bool, dry_run: bool) -> int:
    if not target.is_dir():
        raise SyncError(f"target is not a directory: {target}")
    if target.resolve() == root.resolve():
        raise SyncError("target is the source repository; use scripts.sync_agents instead")
    files = plan(root, tools)
    written = skipped = 0
    for rel, content in files.items():
        dest = target / rel
        if not dest.resolve().is_relative_to(target.resolve()):
            raise SyncError(f"path escapes target: {rel}")
        if dest.exists() and not force:
            skipped += 1
            continue
        written += 1
        if dry_run:
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(content)
        source = root / ".agents" / "skills" / rel.split("skills/", 1)[-1]
        if "/skills/" in rel and source.is_file():
            dest.chmod(source.stat().st_mode & 0o777)
    verb = "would write" if dry_run else "wrote"
    print(f"{verb} {written} files, skipped {skipped} existing (use --force to overwrite)")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="install_skills", description=__doc__)
    parser.add_argument("target", type=Path)
    parser.add_argument("--tool", default="claude", choices=[*TOOLS, "all"])
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parent.parent
    tools = list(TOOLS) if args.tool == "all" else [args.tool]
    try:
        return install(root, args.target, tools, args.force, args.dry_run)
    except SyncError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
