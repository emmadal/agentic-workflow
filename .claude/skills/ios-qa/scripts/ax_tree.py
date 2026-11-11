#!/usr/bin/env python3
"""Summarize an iOS accessibility hierarchy (AXe, idb or Maestro JSON) for QA.

  ax_tree.py list  TREE.json            one line per element with label, id, type, tap center
  ax_tree.py find  TREE.json QUERY      print "x y" (points) of the best match, exit 1 if none
  ax_tree.py audit TREE.json            unlabeled buttons and touch targets under 44pt

Reads `axe describe-ui`, `idb ui describe-all --json` or `maestro hierarchy` output.
Coordinates are in points, which is what simulator tap tools expect. Python 3.9+, stdlib only.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

AXFRAME = re.compile(r"\{\{(-?[\d.]+),\s*(-?[\d.]+)\},\s*\{([\d.]+),\s*([\d.]+)\}\}")
BOUNDS = re.compile(r"\[(-?\d+),(-?\d+)\]\[(-?\d+),(-?\d+)\]")
INTERACTIVE = ("button", "link", "textfield", "securetextfield", "switch", "slider", "cell", "tab")


def flatten(data: object) -> list[dict]:
    out: list[dict] = []

    def walk(node: object) -> None:
        if isinstance(node, list):
            for item in node:
                walk(item)
        elif isinstance(node, dict):
            out.append(node)
            walk(node.get("children", []))

    walk(data)
    return out


def attrs(node: dict) -> dict:
    return node.get("attributes", {}) if isinstance(node.get("attributes"), dict) else {}


def label(node: dict) -> str:
    a = attrs(node)
    for value in (
        node.get("AXLabel"),
        node.get("label"),
        a.get("accessibilityText"),
        a.get("text"),
        a.get("title"),
        node.get("title"),
        node.get("AXValue"),
        a.get("value"),
    ):
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def ident(node: dict) -> str:
    a = attrs(node)
    for value in (node.get("AXUniqueId"), node.get("identifier"), a.get("resource-id")):
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def kind(node: dict) -> str:
    a = attrs(node)
    value = node.get("type") or node.get("role") or a.get("class") or ""
    return str(value).replace("AX", "") if value else "?"


def frame(node: dict) -> tuple[float, float, float, float] | None:
    f = node.get("frame")
    if isinstance(f, dict) and {"x", "y", "width", "height"} <= set(f):
        return float(f["x"]), float(f["y"]), float(f["width"]), float(f["height"])
    m = AXFRAME.fullmatch(str(node.get("AXFrame", "")).strip())
    if m:
        x, y, w, h = map(float, m.groups())
        return x, y, w, h
    m = BOUNDS.fullmatch(str(attrs(node).get("bounds", "")))
    if m:
        x1, y1, x2, y2 = map(float, m.groups())
        return x1, y1, x2 - x1, y2 - y1
    return None


def center(node: dict) -> tuple[int, int] | None:
    f = frame(node)
    if not f or f[2] <= 0 or f[3] <= 0:
        return None
    return round(f[0] + f[2] / 2), round(f[1] + f[3] / 2)


def interactive(node: dict) -> bool:
    k = kind(node).lower().replace(" ", "")
    return any(word in k for word in INTERACTIVE) or attrs(node).get("clickable") == "true"


def describe(node: dict) -> str:
    parts = [f'"{label(node)}"' if label(node) else "-"]
    if ident(node):
        parts.append(f"#{ident(node)}")
    parts.append(kind(node))
    if node.get("enabled") is False or attrs(node).get("enabled") == "false":
        parts.append("[disabled]")
    c = center(node)
    if c:
        parts.append(f"@ {c[0]} {c[1]}")
    return " ".join(parts)


def main(argv: list[str]) -> int:
    if len(argv) < 3 or argv[1] not in ("list", "find", "audit"):
        print(__doc__, file=sys.stderr)
        return 2
    raw = Path(argv[2]).read_text(encoding="utf-8", errors="replace")
    start = min((i for i in (raw.find("["), raw.find("{")) if i >= 0), default=-1)
    if start < 0:
        print("ax_tree: no JSON found in input", file=sys.stderr)
        return 2
    nodes = flatten(json.loads(raw[start:]))
    if argv[1] == "list":
        for i, node in enumerate(nodes):
            if label(node) or ident(node) or interactive(node):
                print(f"{i:3d} {describe(node)}")
        return 0
    if argv[1] == "find":
        if len(argv) < 4:
            print("usage: ax_tree.py find TREE.json QUERY", file=sys.stderr)
            return 2
        q = argv[3].strip()
        tests = (
            lambda n: q in (label(n), ident(n)),
            lambda n: q.lower() in f"{label(n)} {ident(n)}".lower(),
        )
        for test in tests:
            matches = [n for n in nodes if center(n) and test(n)]
            if matches:
                best = next((n for n in matches if interactive(n)), matches[-1])
                x, y = center(best)  # type: ignore[misc]
                print(f"{x} {y}")
                return 0
        print(f"ax_tree: nothing matches {q!r}", file=sys.stderr)
        return 1
    problems = 0
    for i, node in enumerate(nodes):
        if not interactive(node) or not center(node):
            continue
        if not label(node):
            print(f"unlabeled control: {i} {describe(node)}")
            problems += 1
        _, _, w, h = frame(node)  # type: ignore[misc]
        if w < 44 or h < 44:
            print(f"small touch target ({w:.0f}x{h:.0f}pt < 44pt): {i} {describe(node)}")
            problems += 1
    print(f"{problems} accessibility problems found" if problems else "no accessibility problems")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
