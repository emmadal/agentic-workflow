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


def fisher_two_sided(a: int, b: int, c: int, d: int) -> float:
    """Two-sided Fisher exact test p-value for the 2x2 table [[a, b], [c, d]]."""
    from math import comb

    n1, n2, k = a + b, c + d, a + c
    total = comb(n1 + n2, k)

    def prob(x: int) -> float:
        return comb(n1, x) * comb(n2, k - x) / total

    observed = prob(a)
    lo, hi = max(0, k - n2), min(n1, k)
    return min(1.0, sum(prob(x) for x in range(lo, hi + 1) if prob(x) <= observed + 1e-12))


def significance(results: list[dict]) -> str:
    """Perfect-run rate per arm (every check passed), with Fisher exact p-values."""
    lines = [
        "| Task | Arm | Perfect runs | ours vs baseline p | ours vs upstream p |",
        "|---|---|---:|---:|---:|",
    ]
    tasks = sorted({r["task"] for r in results} | {"ALL"})
    for task in tasks:
        sel = [r for r in results if task == "ALL" or r["task"] == task]
        counts = {}
        for arm in ARMS:
            rs = [r for r in sel if r["arm"] == arm]
            counts[arm] = (sum(r["score"] == r["max"] for r in rs), len(rs))
        if not all(counts[a][1] for a in ARMS):
            continue
        ok, n = counts["ours"]
        pb = fisher_two_sided(
            ok, n - ok, counts["baseline"][0], counts["baseline"][1] - counts["baseline"][0]
        )
        pu = fisher_two_sided(
            ok, n - ok, counts["upstream"][0], counts["upstream"][1] - counts["upstream"][0]
        )
        for arm in ARMS:
            k, m = counts[arm]
            tail = f" {pb:.3f} | {pu:.3f} |" if arm == "ours" else " | |"
            lines.append(f"| {task} | {arm} | {k}/{m} |{tail}")
    return "\n".join(lines)


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).with_name("results.json")
    results = load(path)
    print(table(results))
    print("\nChecks passed per arm (only checks where some arm missed):\n")
    print(misses(results))
    print("\nPerfect-run rate (all checks passed) and Fisher exact p-values:\n")
    print(significance(results))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
