"""Behavioral A/B for the personal skills: accountability, secretary, swe-interview.

Arms: no skill vs the skill body appended to the system prompt. One headless `claude -p` call per
run in an empty temp directory with project-only settings and no tools. Graders are regexes and
counts; no model judges another model. Spends tokens, so it is not part of CI.

Usage: python evals/behavioral/personal.py [--reps 3] [--model sonnet] [--out results-personal.json]
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess  # nosec B404
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

NOTES = """Meeting: Q4 launch sync, Mon 11 Nov 2026. Present: Ana, Ben, Chloe.
Ana: we ship the beta on 22 Nov, agreed. Budget stays at 12k.
Ben will fix the payment bug before the beta.
Someone needs to email the vendor about the contract. No date set.
Chloe to prepare the demo by next Friday.
Open: do we need a legal review? Nobody knew."""

TASKS = {
    "secretary": {
        "skill": "secretary",
        "prompt": f"Write the minutes with action items from these notes:\n\n{NOTES}",
        "checks": {
            "has_decisions_and_actions": lambda r: bool(
                re.search(r"decision", r, re.I) and re.search(r"action", r, re.I)
            ),
            "flags_unknown_owner": lambda r: bool(
                re.search(r"confirm|unassigned|tbd|unknown", r, re.I)
            ),
            "chloe_date_absolute_or_flagged": lambda r: any(
                re.search(r"\d{1,2} Nov|Nov \d{1,2}|confirm", line, re.I)
                for line in r.splitlines()
                if "Chloe" in line and re.search(r"demo", line, re.I)
            ),
            "lists_open_question": lambda r: bool(re.search(r"legal", r, re.I)),
            "keeps_budget_fact": lambda r: "12k" in r.lower() or "12,000" in r,
            "no_invented_name": lambda r: not re.search(r"\b(Dan|David|Sarah|Mark|Tom)\b", r),
            "short": lambda r: len(r.split()) <= 260,
        },
    },
    "accountability": {
        "skill": "accountability",
        "prompt": "I want to get fit and learn Rust this month. Hold me accountable.",
        "checks": {
            "has_proof": lambda r: bool(re.search(r"proof|evidence", r, re.I)),
            "has_dates": lambda r: (
                len(re.findall(r"\b(due|by)\b.{0,25}\b(\d{1,2}|Mon|Tue|Wed|Thu|Fri|Sun|Sat)", r))
                >= 2
            ),
            "if_then_plan": lambda r: bool(
                re.search(r"\bif\b.{0,80}\bthen\b|if-then", r, re.I | re.S)
            ),
            "limits_scope": lambda r: len(re.findall(r"^\s*(?:- \[ \]|\d+\.)", r, re.M)) <= 6,
            "asks_or_sets_checkin": lambda r: bool(re.search(r"check-?in", r, re.I)),
            "no_fluff_opening": lambda r: (
                not re.match(r"\s*(great|awesome|sure|absolutely)", r, re.I)
            ),
            "short": lambda r: len(r.split()) <= 300,
        },
    },
    "swe-interview": {
        "skill": "swe-interview",
        "prompt": "Give me a mock system design interview for a mid-level backend role. Start now.",
        "checks": {
            "gives_one_prompt": lambda r: bool(re.search(r"design (a|an)\b", r, re.I)),
            "no_solution_leak": lambda r: (
                not re.search(
                    r"here'?s (a|the) (solution|design)|sample answer|reference (design|answer)",
                    r,
                    re.I,
                )
            ),
            "waits_for_user": lambda r: (
                r.rstrip().endswith(("?", ".", "!", ":")) and len(r.split()) <= 220
            ),
            "sets_format": lambda r: bool(re.search(r"\b(minutes|45|35|time)\b", r, re.I)),
            "no_design_dump": lambda r: len(re.findall(r"^#{1,3} ", r, re.M)) <= 3,
            "hint_policy_or_rules": lambda r: bool(
                re.search(r"hint|clarif|ask me|probe|interrupt|score", r, re.I)
            ),
            "no_fluff_opening": lambda r: (
                not re.match(r"\s*(great|awesome|sure|absolutely)", r, re.I)
            ),
        },
    },
}


def skill_body(name: str) -> str:
    text = (ROOT / ".agents" / "skills" / name / "SKILL.md").read_text()
    return text.split("---", 2)[2].strip()


def run_one(args: tuple) -> dict:
    task, arm, rep, model = args
    spec = TASKS[task]
    cmd = [
        "claude",
        "-p",
        spec["prompt"],
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
    if arm == "skill":
        cmd += ["--append-system-prompt", skill_body(spec["skill"])]
    with tempfile.TemporaryDirectory() as tmp:
        proc = subprocess.run(  # nosec B603
            cmd, cwd=tmp, capture_output=True, text=True, timeout=240, stdin=subprocess.DEVNULL
        )
    try:
        data = json.loads(proc.stdout)
        reply, cost = data.get("result", ""), data.get("total_cost_usd", 0.0)
    except json.JSONDecodeError:
        return {"task": task, "arm": arm, "rep": rep, "failed": True}
    checks = {k: bool(fn(reply)) for k, fn in spec["checks"].items()}
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
    ap.add_argument("--out", default=str(Path(__file__).with_name("results-personal.json")))
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
