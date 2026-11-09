"""Estimate the token cost of a skill catalog.

Usage: python -m scripts.token_report [--compare DIR] [repo_root]

`--compare DIR` reads another catalog laid out as DIR/skills/<name>/SKILL.md (for example the
upstream plugin cache) so the two can be compared with the same method.

Tokens are estimated as characters / 4, a rule of thumb for English text. It is an estimate,
not a tokenizer count, but it is applied identically to both catalogs.
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from pathlib import Path

from .frontmatter import FrontmatterError, parse


def tokens(text: str) -> int:
    return math.ceil(len(text) / 4)


@dataclass
class Catalog:
    label: str
    skills: int
    always_on: int  # name + description of every skill (+ AGENTS.md when present)
    body_total: int
    body_avg: int
    body_max: int
    body_max_name: str
    refs_total: int  # on-demand reference tokens, not loaded unless needed


def measure(label: str, skills_dir: Path, instructions: Path | None = None) -> Catalog:
    always = tokens(instructions.read_text()) if instructions and instructions.is_file() else 0
    bodies: list[tuple[str, int]] = []
    refs = 0
    for skill_md in sorted(skills_dir.glob("*/SKILL.md")):
        try:
            doc = parse(skill_md.read_text())
        except FrontmatterError:
            text = skill_md.read_text()
            doc = None
        name = skill_md.parent.name
        if doc:
            always += tokens(f"{doc.meta.get('name', name)} {doc.meta.get('description', '')}")
            bodies.append((name, tokens(doc.body)))
        else:
            bodies.append((name, tokens(text)))
        for extra in skill_md.parent.rglob("*.md"):
            if extra != skill_md:
                refs += tokens(extra.read_text())
    total = sum(t for _, t in bodies)
    top = max(bodies, key=lambda x: x[1]) if bodies else ("-", 0)
    return Catalog(
        label,
        len(bodies),
        always,
        total,
        total // len(bodies) if bodies else 0,
        top[1],
        top[0],
        refs,
    )


def render(catalogs: list[Catalog]) -> str:
    rows = [
        ("Skills", [str(c.skills) for c in catalogs]),
        (
            "Always-loaded tokens (descriptions + instructions)",
            [str(c.always_on) for c in catalogs],
        ),
        (
            "Always-loaded tokens per skill",
            [str(c.always_on // max(c.skills, 1)) for c in catalogs],
        ),
        ("Tokens to load one average skill", [str(c.body_avg) for c in catalogs]),
        (
            "Tokens to load the largest skill",
            [f"{c.body_max} ({c.body_max_name})" for c in catalogs],
        ),
        ("All skill bodies", [str(c.body_total) for c in catalogs]),
        ("On-demand references (not loaded by default)", [str(c.refs_total) for c in catalogs]),
    ]
    head = "| Metric | " + " | ".join(c.label for c in catalogs) + " |"
    sep = "|---|" + "---:|" * len(catalogs)
    body = [f"| {name} | " + " | ".join(vals) + " |" for name, vals in rows]
    return "\n".join([head, sep, *body])


def main(argv: list[str]) -> int:
    args = argv[1:]
    compare: Path | None = None
    if "--compare" in args:
        i = args.index("--compare")
        compare = Path(args[i + 1])
        del args[i : i + 2]
    root = Path(args[0]) if args else Path(__file__).resolve().parent.parent
    catalogs = [measure("this repo", root / ".agents" / "skills", root / "AGENTS.md")]
    if compare:
        other = compare / "skills" if (compare / "skills").is_dir() else compare
        catalogs.append(measure(compare.name, other, compare / "AGENTS.md"))
    print(render(catalogs))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
