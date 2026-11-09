"""Behavioral A/B eval: does injecting a skill change agent output for the better?

Arms per task:
  baseline  no skill
  ours      this repo's skill bodies
  upstream  the closest skills from addyosmani/agent-skills (path via --upstream)

Each run is an isolated headless `claude -p` call (no user plugins, hooks, MCP or skills) in a
temp directory, with the skill text appended to the system prompt. Graders are objective
(tests, keyword hits, file counts); no model judges another model.

This spends tokens, so it is not part of CI.

Usage:
  python evals/behavioral/run.py --upstream <agent-skills checkout or plugin dir>
         [--reps 2] [--model sonnet] [--tasks tdd,security] [--workers 4] [--out results.json]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess  # nosec B404
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# Narrow grants: the model may run tests and the fixture script, nothing else.
ALLOWED_BASH = [
    "Bash(pytest:*)",
    "Bash(python -m pytest:*)",
    "Bash(python3 -m pytest:*)",
    "Bash(python cli.py:*)",
    "Bash(python3 cli.py:*)",
    "Bash(ls:*)",
]
# Only these variables reach the model's subprocesses. HOME stays real so claude can authenticate.
SAFE_ENV = ("HOME", "USER", "LANG", "LC_ALL", "TERM", "TMPDIR", "ANTHROPIC_API_KEY")


def safe_env() -> dict[str, str]:
    env = {k: os.environ[k] for k in SAFE_ENV if k in os.environ}
    claude_dir = str(Path(shutil.which("claude") or "/usr/local/bin/claude").parent)
    env["PATH"] = (
        f"{ROOT / '.venv' / 'bin'}:{claude_dir}:/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin"
    )
    return env


def grading_env() -> dict[str, str]:
    """Environment for running model-written code during grading: no credentials."""
    return {"PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1"}


sys.path.insert(0, str(ROOT))
from scripts.frontmatter import parse  # noqa: E402

PRICING = '''def line_total(unit_price: float, qty: int) -> float:
    """Total for a line. Orders of 10 or more items get 15% off."""
    if qty > 10:
        return round(unit_price * qty * 0.85, 2)
    return round(unit_price * qty, 2)
'''

ORDERS_API = """import hashlib
import sqlite3

from flask import Flask, jsonify, request

app = Flask(__name__)
API_SECRET = "prod-secret-9f8e7d6c5b4a"
db = sqlite3.connect("shop.db", check_same_thread=False)


@app.post("/register")
def register():
    body = request.json
    pw = hashlib.md5(body["password"].encode()).hexdigest()
    db.execute(f"INSERT INTO users(email, pw) VALUES ('{body['email']}', '{pw}')")
    db.commit()
    return jsonify(ok=True)


@app.get("/orders/<int:order_id>")
def get_order(order_id):
    row = db.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    return jsonify(row)


@app.post("/admin/refund")
def refund():
    issue_refund(request.json["order_id"], API_SECRET)
    return jsonify(ok=True)


@app.get("/export")
def export():
    return open(request.args["path"]).read()
"""

CLI = """import os, sys


def parse(argv):
    # TODO: handle errors
    args = {}
    for a in argv[1:]:
        if a.startswith("--"):
            k, _, v = a[2:].partition("=")
            args[k] = v or True
    return args


def Run(argv):
    args = parse(argv)
    name = args.get("name", "world")
    print("Hello, " + name + "!")


if __name__ == "__main__":
    Run(sys.argv)
"""

COMPOSE = """@Composable
fun TaskListScreen(viewModel: TaskViewModel) {
    val tasks by viewModel.tasks.collectAsState()
    var query by mutableStateOf("")
    viewModel.refresh()
    Column {
        TextField(value = query, onValueChange = { query = it })
        LazyColumn {
            items(tasks.filter { it.title.contains(query) }) { task ->
                Text(task.title, color = Color(0xFF3366FF), fontSize = 14.sp)
            }
        }
    }
}
"""

# keyword groups: an issue counts as found if any regex in its group matches the lowercased reply
SECURITY_ISSUES = {
    "sql_injection": [r"sql injection", r"sqli\b", r"f-string.*(sql|query)", r"parameteri[sz]"],
    "weak_password_hash": [r"md5"],
    "hardcoded_secret": [r"hard-?coded", r"api_secret", r"secret.*(source|code|repo)"],
    "idor": [r"\bidor\b", r"ownership", r"insecure direct", r"any (user|order)", r"another user"],
    "unauthenticated_admin": [r"admin.{0,80}(auth|unauth|permission|role)", r"refund.{0,80}auth"],
    "path_traversal": [r"path traversal", r"directory traversal", r"\.\./", r"arbitrary file"],
}
COMPOSE_ISSUES = {
    "non_lifecycle_collect": [r"collectasstatewithlifecycle", r"lifecycle-aware", r"lifecycle"],
    "state_not_remembered": [
        r"mutablestateof.{0,120}remember",
        r"remember.{0,120}mutablestateof",
        r"rememberSaveable".lower(),
        r"not (be )?remembered",
    ],
    "side_effect_in_body": [
        r"launchedeffect",
        r"side[- ]effect",
        r"refresh\(\).{0,100}(composition|recompos)",
    ],
    "no_lazy_key": [
        r"\bkey\s*=",
        r"stable key",
        r"provide a key",
        r"missing key",
        r"without a key",
        r"no key",
    ],
    "hardcoded_theme": [r"materialtheme", r"hard-?coded", r"theme token", r"colorscheme"],
    "no_modifier_param": [r"modifier"],
    "unmemoized_filter": [
        r"derivedstateof",
        r"filter.{0,120}(every|each) recompos",
        r"remember\(.*query",
    ],
}

SKILLS = {
    "tdd": {"ours": ["test-driven-development"], "upstream": ["test-driven-development"]},
    "security": {
        "ours": ["security-hardening", "code-review"],
        "upstream": ["security-and-hardening", "code-review-and-quality"],
    },
    "vague": {"ours": ["discover"], "upstream": ["interview-me"]},
    "scope": {
        "ours": ["incremental-implementation", "test-driven-development"],
        "upstream": ["incremental-implementation", "test-driven-development"],
    },
    "compose": {
        "ours": ["android-compose", "code-review"],
        "upstream": ["frontend-ui-engineering", "code-review-and-quality"],
    },
}

TASKS = {
    "tdd": {
        "prompt": "Bug report: customers who order exactly 10 items are not getting the 15% bulk "
        "discount. Fix it.",
        "files": {"pricing.py": PRICING},
        "tools": "Read,Write,Edit,Bash",
        "turns": 12,
    },
    "security": {
        "prompt": "Review orders_api.py before merge. List the problems you find, most severe "
        "first. Do not edit files.",
        "files": {"orders_api.py": ORDERS_API},
        "tools": "Read",
        "turns": 4,
    },
    "scope": {
        "prompt": "Add a --shout flag to cli.py that prints the greeting in upper case.",
        "files": {"cli.py": CLI},
        "tools": "Read,Write,Edit,Bash",
        "turns": 12,
    },
    "vague": {
        "prompt": "Build me a food delivery app.",
        "files": {},
        "tools": "Read,Write,Edit,Bash",
        "turns": 6,
    },
    "compose": {
        "prompt": "Review TaskListScreen.kt before merge. List the problems you find, most "
        "severe first. Do not edit files.",
        "files": {"TaskListScreen.kt": COMPOSE},
        "tools": "Read",
        "turns": 4,
    },
}


def skill_text(root: Path, names: list[str]) -> str:
    parts = []
    for name in names:
        doc = parse((root / name / "SKILL.md").read_text())
        parts.append(f'<skill name="{name}">\n{doc.body.strip()}\n</skill>')
    return (
        "You have the following skills. Apply them when they are relevant to the task.\n\n"
        + "\n\n".join(parts)
    )


def hits(text: str, issues: dict[str, list[str]]) -> dict[str, bool]:
    low = text.lower()
    return {k: any(re.search(p, low, re.S) for p in pats) for k, pats in issues.items()}


def grade_tdd(workdir: Path) -> dict:
    tests = [
        p
        for p in workdir.rglob("*.py")
        if p.name != "pricing.py" and ("test" in p.name) and ".pytest_cache" not in p.parts
    ]
    added = bool(tests) and any("line_total" in p.read_text() for p in tests)

    def run_pytest(directory: Path) -> int:
        env = grading_env()
        proc = subprocess.run(  # nosec B603 B607
            [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", str(directory)],
            capture_output=True,
            text=True,
            timeout=120,
            env=env,
        )
        return proc.returncode

    repro = False
    if added:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            (tmp_path / "pricing.py").write_text(PRICING)
            for t in tests:
                shutil.copy(t, tmp_path / t.name)
            repro = run_pytest(tmp_path) != 0  # new tests must fail on the original code
    probe = (
        "import json, sys; sys.path.insert(0, '.'); from pricing import line_total as f; "
        "print(json.dumps([f(10, 10), f(10, 9), f(10, 11)]))"
    )
    try:
        out = subprocess.run(  # nosec B603
            [sys.executable, "-c", probe],
            cwd=workdir,
            capture_output=True,
            text=True,
            timeout=15,
            env=grading_env(),
        )
        fixed = json.loads(out.stdout or "null") == [85.0, 90.0, 93.5]
    except (subprocess.SubprocessError, json.JSONDecodeError, OSError):
        fixed = False
    passing = added and run_pytest(workdir) == 0
    return {
        "regression_test_added": added,
        "test_fails_on_original": repro,
        "fix_correct": fixed,
        "suite_passes": passing,
    }


def grade_scope(workdir: Path) -> dict:
    src = (workdir / "cli.py").read_text() if (workdir / "cli.py").exists() else ""

    def run(args: list[str]) -> str:
        proc = subprocess.run(  # nosec B603
            [sys.executable, "cli.py", *args],
            cwd=workdir,
            capture_output=True,
            text=True,
            timeout=30,
            env=grading_env(),
        )
        return proc.stdout.strip()

    try:
        feature = run(["--shout", "--name=bob"]) == "HELLO, BOB!"
        default = run([]) == "Hello, world!"
    except Exception:  # noqa: BLE001
        feature = default = False
    untouched = all(m in src for m in ("def Run(argv):", "# TODO: handle errors", "import os, sys"))
    tests = any(p.name != "cli.py" and "test" in p.name for p in workdir.rglob("*.py"))
    return {
        "feature_works": feature,
        "default_unchanged": default,
        "unrelated_code_untouched": untouched,
        "test_added": tests,
    }


def grade(task: str, workdir: Path, reply: str) -> dict:
    if task == "tdd":
        return grade_tdd(workdir)
    if task == "scope":
        return grade_scope(workdir)
    if task == "security":
        return hits(reply, SECURITY_ISSUES)
    if task == "compose":
        return hits(reply, COMPOSE_ISSUES)
    created = [p for p in workdir.rglob("*") if p.is_file()]
    return {"asked_questions": reply.count("?") >= 2, "built_nothing": not created}


def run_one(args: tuple) -> dict:
    task, arm, rep, model, skills_dir, upstream_dir = args
    spec = TASKS[task]
    workdir = Path(tempfile.mkdtemp(prefix=f"beh-{task}-{arm}-{rep}-"))
    try:
        for name, content in spec["files"].items():
            (workdir / name).write_text(content)
        cmd = [
            "claude",
            "-p",
            spec["prompt"],
            "--model",
            model,
            "--disable-slash-commands",
            "--setting-sources",
            "project",
            "--strict-mcp-config",
            "--tools",
            spec["tools"],
            "--permission-mode",
            "acceptEdits",
            "--max-turns",
            str(spec["turns"]),
            "--output-format",
            "json",
            "--no-session-persistence",
        ]
        if "Bash" in spec["tools"]:
            cmd += ["--allowedTools", *ALLOWED_BASH]
        if arm != "baseline":
            root = skills_dir if arm == "ours" else upstream_dir
            cmd += ["--append-system-prompt", skill_text(root, SKILLS[task][arm])]
        env = safe_env()
        proc = subprocess.run(  # nosec B603
            cmd, cwd=workdir, capture_output=True, text=True, timeout=420, env=env
        )
        try:
            data = json.loads(proc.stdout)
        except json.JSONDecodeError:
            return {
                "task": task,
                "arm": arm,
                "rep": rep,
                "error": proc.stderr[-300:] or proc.stdout[-300:],
            }
        reply = data.get("result", "") or ""
        usage = data.get("usage", {})
        if data.get("is_error") or not usage.get("output_tokens"):
            return {"task": task, "arm": arm, "rep": rep, "error": f"failed call: {reply[:200]}"}
        flags = grade(task, workdir, reply)
        return {
            "task": task,
            "arm": arm,
            "rep": rep,
            "flags": flags,
            "score": sum(flags.values()),
            "max": len(flags),
            "reply_words": len(reply.split()),
            "turns": data.get("num_turns"),
            "cost_usd": data.get("total_cost_usd"),
            "input_tokens": (
                usage.get("input_tokens", 0)
                + usage.get("cache_creation_input_tokens", 0)
                + usage.get("cache_read_input_tokens", 0)
            ),
            "output_tokens": usage.get("output_tokens", 0),
        }
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


def summarize(results: list[dict]) -> str:
    rows = {}
    for r in results:
        if "error" in r:
            continue
        rows.setdefault((r["task"], r["arm"]), []).append(r)
    lines = [
        "| Task | Arm | Score (avg) | Reply words | Output tok | Input tok | Cost USD |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for (task, arm), rs in sorted(rows.items()):
        n = len(rs)
        avg = lambda k, rs=rs, n=n: sum(x[k] or 0 for x in rs) / n  # noqa: E731
        lines.append(
            f"| {task} | {arm} | {avg('score'):.1f}/{rs[0]['max']} | {avg('reply_words'):.0f} | "
            f"{avg('output_tokens'):.0f} | {avg('input_tokens'):.0f} | {avg('cost_usd'):.3f} |"
        )
    errors = [r for r in results if "error" in r]
    if errors:
        lines.append(f"\n{len(errors)} run(s) failed: {errors[0]['error'][:200]}")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--upstream", required=True, type=Path, help="upstream checkout or plugin dir")
    ap.add_argument("--reps", type=int, default=2)
    ap.add_argument("--model", default="sonnet")
    ap.add_argument("--tasks", default=",".join(TASKS))
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--out", type=Path, default=Path(__file__).with_name("results.json"))
    ns = ap.parse_args()
    upstream = ns.upstream / "skills" if (ns.upstream / "skills").is_dir() else ns.upstream
    ours = ROOT / ".agents" / "skills"
    jobs = [
        (t, arm, rep, ns.model, ours, upstream)
        for t in ns.tasks.split(",")
        for arm in ("baseline", "ours", "upstream")
        for rep in range(ns.reps)
    ]
    with ThreadPoolExecutor(max_workers=ns.workers) as pool:
        results = list(pool.map(run_one, jobs))
    ns.out.write_text(json.dumps(results, indent=1))
    print(summarize(results))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
