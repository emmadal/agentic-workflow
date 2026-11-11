#!/usr/bin/env python3
"""Summarize an Android `uiautomator dump` XML for QA.

  ui_tree.py list  DUMP.xml [--all]          one line per meaningful node, with tap centers
  ui_tree.py find  DUMP.xml QUERY            print "x y" center of the best match (exit 1 if none)
  ui_tree.py audit DUMP.xml [--density DPI]  accessibility gaps: unlabeled controls, small targets

Matching order for find: exact text, content-desc or resource-id (with or without the
package prefix), then case-insensitive substring. Python 3.9+, standard library only.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from xml.etree import ElementTree  # nosec B405

BOUNDS = re.compile(r"\[(-?\d+),(-?\d+)\]\[(-?\d+),(-?\d+)\]")


def load(path: str) -> list[dict[str, str]]:
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    start = text.find("<?xml")
    if start < 0:
        start = text.find("<hierarchy")
    end = text.rfind("</hierarchy>")
    if start < 0 or end < 0:
        raise SystemExit("ui_tree: no <hierarchy> found; is the screen locked or secure?")
    if re.search(r"<!(DOCTYPE|ENTITY)", text, re.I):
        # uiautomator never emits these; refusing them rules out entity-expansion attacks.
        raise SystemExit("ui_tree: refusing XML with DOCTYPE or ENTITY declarations")
    root = ElementTree.fromstring(text[start : end + len("</hierarchy>")])  # nosec B314
    return [dict(node.attrib) for node in root.iter("node")]


def center(node: dict[str, str]) -> tuple[int, int] | None:
    m = BOUNDS.fullmatch(node.get("bounds", ""))
    if not m:
        return None
    x1, y1, x2, y2 = map(int, m.groups())
    if x2 <= x1 or y2 <= y1:
        return None
    return (x1 + x2) // 2, (y1 + y2) // 2


def size(node: dict[str, str]) -> tuple[int, int]:
    m = BOUNDS.fullmatch(node.get("bounds", ""))
    if not m:
        return 0, 0
    x1, y1, x2, y2 = map(int, m.groups())
    return x2 - x1, y2 - y1


def short_id(node: dict[str, str]) -> str:
    rid = node.get("resource-id", "")
    return rid.split(":id/", 1)[-1] if rid else ""


def label(node: dict[str, str]) -> str:
    return node.get("text", "").strip() or node.get("content-desc", "").strip()


def clickable(node: dict[str, str]) -> bool:
    return node.get("clickable") == "true" or node.get("long-clickable") == "true"


def describe(node: dict[str, str]) -> str:
    parts = [f'"{label(node)}"' if label(node) else "-"]
    if short_id(node):
        parts.append(f"#{short_id(node)}")
    parts.append(node.get("class", "").rsplit(".", 1)[-1])
    flags = [
        name
        for name, key in (("click", "clickable"), ("checked", "checked"), ("focus", "focused"))
        if node.get(key) == "true"
    ]
    if node.get("enabled") == "false":
        flags.append("disabled")
    if node.get("password") == "true":
        flags.append("password")
    if flags:
        parts.append("[" + ",".join(flags) + "]")
    c = center(node)
    if c:
        parts.append(f"@ {c[0]} {c[1]}")
    return " ".join(parts)


def cmd_list(nodes: list[dict[str, str]], show_all: bool) -> int:
    for i, node in enumerate(nodes):
        if show_all or label(node) or short_id(node) or clickable(node):
            print(f"{i:3d} {describe(node)}")
    return 0


def cmd_find(nodes: list[dict[str, str]], query: str) -> int:
    q = query.strip()
    visible = [n for n in nodes if center(n)]

    def exact(n: dict[str, str]) -> bool:
        return q in (n.get("text", ""), n.get("content-desc", ""), n.get("resource-id", ""))

    def fuzzy(n: dict[str, str]) -> bool:
        hay = " ".join((label(n), n.get("resource-id", ""))).lower()
        return q.lower() in hay

    for test in (exact, lambda n: short_id(n) == q, fuzzy):
        matches = [n for n in visible if test(n)]
        if matches:
            # Prefer a clickable match; a labeled child sits inside its tap target anyway.
            best = next((n for n in matches if clickable(n)), matches[0])
            x, y = center(best)  # type: ignore[misc]
            print(f"{x} {y}")
            return 0
    print(f"ui_tree: nothing matches {query!r}", file=sys.stderr)
    return 1


def cmd_audit(nodes: list[dict[str, str]], density: int) -> int:
    min_px = round(48 * density / 160)
    problems = 0
    screen = BOUNDS.fullmatch(nodes[0].get("bounds", "")) if nodes else None
    top, bottom = (int(screen.group(2)), int(screen.group(4))) if screen else (0, 1 << 30)
    for i, node in enumerate(nodes):
        if not clickable(node) or not center(node):
            continue
        if not label(node) and not _child_label(nodes, i):
            print(f"unlabeled control: {i} {describe(node)}")
            problems += 1
        w, h = size(node)
        y1, y2 = map(int, BOUNDS.fullmatch(node["bounds"]).group(2, 4))  # type: ignore[union-attr]
        clipped = y1 <= top or y2 >= bottom  # partly scrolled off screen: size is not real
        if not clipped and (w < min_px or h < min_px):
            print(f"small touch target ({w}x{h}px < {min_px}px = 48dp): {i} {describe(node)}")
            problems += 1
    print(f"{problems} accessibility problems found" if problems else "no accessibility problems")
    return 0


def _child_label(nodes: list[dict[str, str]], idx: int) -> bool:
    """True when a node nested inside nodes[idx] (by bounds) carries a label."""
    m = BOUNDS.fullmatch(nodes[idx].get("bounds", ""))
    if not m:
        return False
    x1, y1, x2, y2 = map(int, m.groups())
    for other in nodes[idx + 1 :]:
        o = BOUNDS.fullmatch(other.get("bounds", ""))
        if not o:
            continue
        a1, b1, a2, b2 = map(int, o.groups())
        inside = a1 >= x1 and b1 >= y1 and a2 <= x2 and b2 <= y2
        if not inside:
            break
        if label(other):
            return True
    return False


def main(argv: list[str]) -> int:
    if len(argv) < 3 or argv[1] not in ("list", "find", "audit"):
        print(__doc__, file=sys.stderr)
        return 2
    nodes = load(argv[2])
    if argv[1] == "list":
        return cmd_list(nodes, "--all" in argv)
    if argv[1] == "find":
        if len(argv) < 4:
            print("usage: ui_tree.py find DUMP.xml QUERY", file=sys.stderr)
            return 2
        return cmd_find(nodes, argv[3])
    density = 160
    if "--density" in argv:
        density = int(argv[argv.index("--density") + 1])
    return cmd_audit(nodes, density)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
