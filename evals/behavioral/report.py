"""Summarize evals/behavioral/results.json: per-arm scores, token cost, and which checks failed.

Usage: python evals/behavioral/report.py [results.json]
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ARMS = ("baseline", "ours", "upstream")


def load(path: Path) -> list[dict]:
    return [r for r in json.loads(path.read_text()) if "error" not in r]


def table(results: list[dict]) -> str:
    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for r in results:
        groups[(r["task"], r["arm"])].append(r)
    lines = [
        "| Task | Arm | Score | Reply words | Output tok | Input tok | Cost USD |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    totals: dict[str, list[float]] = defaultdict(lambda: [0, 0, 0, 0, 0])
    for task in sorted({t for t, _ in groups}):
        for arm in ARMS:
            rs = groups.get((task, arm), [])
            if not rs:
                continue
            n = len(rs)
            mean = lambda k, rs=rs, n=n: sum((x[k] or 0) for x in rs) / n  # noqa: E731
            lines.append(
                f"| {task} | {arm} | {mean('score'):.2f}/{rs[0]['max']} "
                f"| {mean('reply_words'):.0f} | {mean('output_tokens'):.0f} "
                f"| {mean('input_tokens'):.0f} | {mean('cost_usd'):.3f} |"
            )
            frac = mean("score") / rs[0]["max"]
            t = totals[arm]
            t[0] += frac
            t[1] += 1
            t[2] += mean("input_tokens")
            t[3] += mean("output_tokens")
            t[4] += mean("cost_usd")
    lines += [
        "",
        "| Arm | Mean normalized score | Mean input tok | Mean output tok | Mean cost USD |",
        "|---|---:|---:|---:|---:|",
    ]
    for arm in ARMS:
        if arm in totals:
            s, n, i, o, c = totals[arm]
            lines.append(f"| {arm} | {s / n:.3f} | {i / n:.0f} | {o / n:.0f} | {c / n:.3f} |")
    return "\n".join(lines)


def misses(results: list[dict]) -> str:
    miss: dict[tuple[str, str, str], list[int]] = defaultdict(lambda: [0, 0])
    for r in results:
        for flag, ok in r["flags"].items():
            cell = miss[(r["task"], flag, r["arm"])]
            cell[1] += 1
            cell[0] += 0 if ok else 1
    rows = defaultdict(dict)
    for (task, flag, arm), (bad, total) in miss.items():
        rows[(task, flag)][arm] = f"{total - bad}/{total}"
    lines = ["| Check | baseline | ours | upstream |", "|---|---:|---:|---:|"]
    for (task, flag), arms in sorted(rows.items()):
        if len({v.split("/")[0] + v.split("/")[1] for v in arms.values()}) > 1 or any(
            v.split("/")[0] != v.split("/")[1] for v in arms.values()
        ):
            lines.append(
                f"| {task}.{flag} | {arms.get('baseline', '-')} | {arms.get('ours', '-')} "
                f"| {arms.get('upstream', '-')} |"
            )
    return "\n".join(lines)


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).with_name("results.json")
    results = load(path)
    print(table(results))
    print("\nChecks passed per arm (only checks where some arm missed):\n")
    print(misses(results))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
