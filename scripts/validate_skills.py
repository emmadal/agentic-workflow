"""Validate canonical skills and agents so every tool can discover and call them.

Usage: python -m scripts.validate_skills [repo_root]
Exit code 1 on any error.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from .frontmatter import FrontmatterError, parse

NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
SKILL_KEYS = {"name", "description", "license", "compatibility", "metadata"}
AGENT_KEYS = {"name", "description", "access"}
ACCESS = {"read-only", "inspect", "write"}
# Conservative portable limits: the Agent Skills spec allows 1024, some tools enforce less.
MAX_NAME = 64
MAX_DESCRIPTION = 280
MAX_BODY_WORDS = 400
# Always-loaded cost: every description is in context every session. Keep the catalog lean.
TOTAL_DESCRIPTION_BUDGET = 8000
MAX_AGENTS_MD_WORDS = 450
REF_RE = re.compile(r"`((?:scripts|references|assets)/[A-Za-z0-9._/-]+)`")


def _symlinks(base: Path) -> list[str]:
    return [
        f"symlinks are not allowed: {p.relative_to(base.parent.parent)}"
        for p in sorted(base.rglob("*"))
        if p.is_symlink()
    ]


def validate_skills(root: Path) -> list[str]:
    skills_dir = root / ".agents" / "skills"
    if not skills_dir.is_dir():
        return [f"missing directory: {skills_dir}"]
    errors: list[str] = _symlinks(skills_dir)
    seen: set[str] = set()
    for skill_dir in sorted(p for p in skills_dir.iterdir() if p.is_dir()):
        label = f"skill {skill_dir.name}"
        path = skill_dir / "SKILL.md"
        if not path.is_file():
            errors.append(f"{label}: missing SKILL.md")
            continue
        try:
            doc = parse(path.read_text())
        except FrontmatterError as exc:
            errors.append(f"{label}: {exc}")
            continue
        errors += _check_skill(label, skill_dir, doc.meta, doc.body, seen)
    errors += _check_budgets(root, skills_dir)
    return errors


def _check_budgets(root: Path, skills_dir: Path) -> list[str]:
    errors: list[str] = []
    total = 0
    for path in skills_dir.glob("*/SKILL.md"):
        try:
            total += len(parse(path.read_text()).meta.get("description", ""))
        except FrontmatterError:
            continue
    if total > TOTAL_DESCRIPTION_BUDGET:
        errors.append(
            f"catalog: descriptions total {total} chars, budget {TOTAL_DESCRIPTION_BUDGET}"
        )
    agents_md = root / "AGENTS.md"
    if agents_md.is_file() and len(agents_md.read_text().split()) > MAX_AGENTS_MD_WORDS:
        errors.append(f"AGENTS.md exceeds {MAX_AGENTS_MD_WORDS} words (loaded every session)")
    return errors


def _check_skill(label: str, skill_dir: Path, meta: dict, body: str, seen: set[str]) -> list[str]:
    errors: list[str] = []
    name = meta.get("name", "")
    desc = meta.get("description", "")
    for key in set(meta) - SKILL_KEYS:
        errors.append(f"{label}: unsupported frontmatter key '{key}'")
    if name != skill_dir.name:
        errors.append(f"{label}: name '{name}' must equal directory name")
    if not NAME_RE.match(name) or len(name) > MAX_NAME:
        errors.append(f"{label}: name must be lowercase-hyphen and at most {MAX_NAME} chars")
    if name in seen:
        errors.append(f"{label}: duplicate name")
    seen.add(name)
    if not desc:
        errors.append(f"{label}: description is required")
    if len(desc) > MAX_DESCRIPTION:
        errors.append(f"{label}: description is {len(desc)} chars, max {MAX_DESCRIPTION}")
    if "\n" in desc:
        errors.append(f"{label}: description must be a single line")
    if "use when" not in desc.lower():
        errors.append(f"{label}: description must say when to use it ('Use when ...')")
    words = len(body.split())
    if words > MAX_BODY_WORDS:
        errors.append(
            f"{label}: body is {words} words, max {MAX_BODY_WORDS}; move detail to references/"
        )
    for ref in sorted(set(REF_RE.findall(body))):
        if not (skill_dir / ref).exists() and ref.rstrip("/") not in {
            "scripts",
            "references",
            "assets",
        }:
            errors.append(f"{label}: referenced file not found: {ref}")
    return errors


def validate_agents(root: Path) -> list[str]:
    agents_dir = root / ".agents" / "agents"
    if not agents_dir.is_dir():
        return [f"missing directory: {agents_dir}"]
    errors: list[str] = _symlinks(agents_dir)
    skill_names = {p.name for p in (root / ".agents" / "skills").iterdir() if p.is_dir()}
    for path in sorted(agents_dir.glob("*.md")):
        label = f"agent {path.stem}"
        try:
            doc = parse(path.read_text())
        except FrontmatterError as exc:
            errors.append(f"{label}: {exc}")
            continue
        meta = doc.meta
        for key in set(meta) - AGENT_KEYS:
            errors.append(f"{label}: unsupported frontmatter key '{key}'")
        if meta.get("name") != path.stem or not NAME_RE.match(meta.get("name", "")):
            errors.append(f"{label}: name must equal file name and be lowercase-hyphen")
        if not meta.get("description"):
            errors.append(f"{label}: description is required")
        if meta.get("access") not in ACCESS:
            errors.append(f"{label}: access must be one of {sorted(ACCESS)}")
        if "'''" in doc.body:
            errors.append(f"{label}: body must not contain ''' (breaks the Codex TOML output)")
        for skill in re.findall(r"`([a-z0-9-]+)` skill", doc.body):
            if skill not in skill_names:
                errors.append(f"{label}: references unknown skill '{skill}'")
    return errors


def main(argv: list[str]) -> int:
    root = Path(argv[1]) if len(argv) > 1 else Path(__file__).resolve().parent.parent
    errors = validate_skills(root) + validate_agents(root)
    for err in errors:
        print(f"error: {err}", file=sys.stderr)
    if not errors:
        print("skills and agents valid")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
