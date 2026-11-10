# ruff: noqa: E501
"""Two-turn behavioral A/B for accountability and swe-interview (see personal.py for the method).

Turn 1 is the opening prompt (for swe-interview the grader was rewritten after reading a first run, see docs/benchmarks.md); turn 2 is a scripted user reply sent with --resume. Graders check
the turn-2 reply only. Regex and counts, no model judge. Spends tokens; not part of CI.

Usage: python evals/behavioral/personal_multi.py [--reps 3] [--model sonnet]
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess  # nosec B404
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from personal import skill_body  # type: ignore[import-not-found]  # noqa: E402

TASKS = {
    "accountability": {
        "skill": "accountability",
        "turn1": "I want to ship my portfolio site and run 3 times a week this month. Hold me accountable.",
        "turn2": (
            "Done means: home, projects and contact pages live on my domain. Deadline Fri 29 Nov 2026. "
            "I skip things when I'm tired after work. Today is Mon 11 Nov 2026."
        ),
        "checks": {
            "at_most_3_items": lambda r: len(re.findall(r"^\s*(?:- \[ \]|\d+\.)", r, re.M)) <= 6,
            "has_proof": lambda r: bool(re.search(r"proof|evidence", r, re.I)),
            "uses_given_deadline": lambda r: bool(re.search(r"29 Nov|Nov 29|Fri 29", r)),
            "if_then_for_tiredness": lambda r: (
                bool(re.search(r"tired", r, re.I)) and bool(re.search(r"\bif\b", r, re.I))
            ),
            "names_next_checkin": lambda r: bool(
                re.search(r"check-?in.{0,60}(Nov|Mon|Tue|Wed|Thu|Fri|Sun|Sat)", r, re.I | re.S)
            ),
            "no_guilt_or_fluff": lambda r: (
                not re.match(r"\s*(great|awesome|sure|absolutely)", r, re.I)
            ),
            "short": lambda r: len(r.split()) <= 300,
        },
    },
    "swe-interview": {
        "skill": "swe-interview",
        "turn1": (
            "Give me a mock coding interview, mid-level backend. Use this exact problem: given an "
            "integer array and a target, return the indices of two numbers that sum to the target. Start now."
        ),
        "turn2": (
            "I'd sort the array first then scan with two pointers, so O(n log n). I haven't thought about "
            "duplicates yet. I think I'm done."
        ),
        "checks": {
            "catches_index_problem": lambda r: (
                bool(re.search(r"indices|index", r, re.I)) and bool(re.search(r"sort", r, re.I))
            ),
            "asks_at_most_two_questions": lambda r: 1 <= r.count("?") <= 2,
            "no_code_or_solution_leak": lambda r: (
                "```" not in r and not re.search(r"hash ?map|dictionary|complement", r, re.I)
            ),
            "does_not_score_early": lambda r: (
                not re.search(r"no hire|lean hire|\b[1-4]/4\b", r, re.I)
            ),
            "no_fluff_opening": lambda r: (
                not re.match(r"\s*(great|awesome|sure|absolutely|thanks)", r, re.I)
            ),
            "short": lambda r: len(r.split()) <= 120,
        },
    },
}


def call(prompt: str, model: str, system: str | None, resume: str | None, cwd: str) -> dict:
    cmd = [
        "claude",
        "-p",
        prompt,
        "--model",
        model,
        "--setting-sources",
        "project",
        "--tools",
        "",
        "--max-turns",
        "2",
        "--output-format",
        "json",
    ]
    if system:
        cmd += ["--append-system-prompt", system]
    if resume:
        cmd += ["--resume", resume]
    proc = subprocess.run(  # nosec B603
        cmd, cwd=cwd, capture_output=True, text=True, timeout=240, stdin=subprocess.DEVNULL
    )
    return json.loads(proc.stdout)


def run_one(args: tuple) -> dict:
    task, arm, rep, model = args
    spec = TASKS[task]
    system = skill_body(spec["skill"]) if arm == "skill" else None
    try:
        with tempfile.TemporaryDirectory() as tmp:
            first = call(spec["turn1"], model, system, None, tmp)
            second = call(spec["turn2"], model, system, first["session_id"], tmp)
    except (json.JSONDecodeError, KeyError, subprocess.TimeoutExpired):
        return {"task": task, "arm": arm, "rep": rep, "failed": True}
    reply = second.get("result", "")
    checks = {k: bool(fn(reply)) for k, fn in spec["checks"].items()}
    cost = first.get("total_cost_usd", 0) + second.get("total_cost_usd", 0)
    return {
        "task": task,
        "arm": arm,
        "rep": rep,
        "failed": False,
        "cost": cost,
        "checks": checks,
        "score": sum(checks.values()) / len(checks),
        "perfect": all(checks.values()),
        "reply": reply,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--model", default="sonnet")
    ap.add_argument("--out", default=str(Path(__file__).with_name("results-personal-multi.json")))
    args = ap.parse_args()
    jobs = [
        (t, a, r, args.model) for t in TASKS for a in ("none", "skill") for r in range(args.reps)
    ]
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(run_one, jobs))
    Path(args.out).write_text(json.dumps(results, indent=1))
    print("task | arm | perfect | mean score | mean cost | failed")
    for t in TASKS:
        for a in ("none", "skill"):
            rows = [x for x in results if x["task"] == t and x["arm"] == a]
            ok = [x for x in rows if not x["failed"]]
            if ok:
                print(
                    f"{t} | {a} | {sum(x['perfect'] for x in ok)}/{len(ok)} | "
                    f"{sum(x['score'] for x in ok) / len(ok):.2f} | "
                    f"${sum(x['cost'] for x in ok) / len(ok):.3f} | {len(rows) - len(ok)}"
                )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
