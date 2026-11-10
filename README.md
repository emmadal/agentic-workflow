# agentic-workflow

**Skills and role agents that make AI coding agents work like a senior engineer: spec first, small slices, tests as the signal, independent review.**

38 skills and 11 agents, written once in `.agents/` and generated for Claude Code, OpenCode, Cursor, Codex and Gemini CLI. Built to be cheap: about 70 tokens per skill sit in context, and one skill costs about 370 tokens when it loads.

## The workflow

```
      DEFINE            PLAN              BUILD             VERIFY            REVIEW            SHIP
 ┌───────────────┐ ┌───────────────┐ ┌─────────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
 │ discover      │ │ plan          │ │ incremental     │ │ debugging     │ │ code-review   │ │ release       │
 │ spec          │ │ adr           │ │ test-driven     │ │ qa-testing    │ │ security-     │ │ ship          │
 │ context-eng.  │ │               │ │ implementation  │ │ test-plan     │ │ hardening     │ │               │
 └───────────────┘ └───────────────┘ └─────────────────┘ └───────────────┘ └───────────────┘ └───────────────┘
        │                 │                 │                 │                │                 │
   questions, then   small ordered     thin slices,      reproduce →      ranked findings   checklist, staged
   2-3 options       tasks, risks      tests first       isolate → fix    and a verdict     rollout, rollback
```

Every phase maps to a skill that loads by itself from its description ("Use when ..."), or by name (`/spec`). You do not need to memorize anything.

## How it reaches every tool

```
                    ┌─────────────────────────────────┐
                    │  .agents/          ← source    │
                    │  ├── skills/    (38 skills)    │
                    │  └── agents/     (11 agents)   │
                    └───────────────┬─────────────────┘
                                    │  python -m scripts.sync_agents
                                    │  (CI checks --check for drift)
        ┌───────────────┬───────────┴───┬───────────────┬───────────────┐
        ▼               ▼               ▼               ▼               ▼
 ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
 │ .claude/    │ │ .opencode/  │ │ .cursor/    │ │ .codex/     │ │ .gemini/    │
 └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘
   generated — do not edit; add a skill by editing .agents/skills/ and re-syncing
```

## Quick start

<details open>
<summary><b>Claude Code (plugin)</b></summary>

```
/plugin marketplace add emmadal/agentic-workflow
/plugin install agentic-workflow@agentic-workflow
```

Skills appear namespaced, for example `/agentic-workflow:spec`. To try it from a clone: `claude --plugin-dir /path/to/agentic-workflow`.

The repo is private today. Make it public, or use the HTTPS URL with a GitHub login that can read it.

</details>

<details open>
<summary><b>Any tool, from a clone</b></summary>

```bash
git clone https://github.com/emmadal/agentic-workflow && cd agentic-workflow
python -m scripts.install_skills /path/to/your/project                  # Claude Code (default)
python -m scripts.install_skills /path/to/your/project --tool opencode  # cursor | codex | gemini | all
python -m scripts.install_skills /path/to/your/project --dry-run        # preview only
```

Needs Python 3.11+ and nothing else. Existing files are kept unless you pass `--force`. Your `AGENTS.md`, `CLAUDE.md` and settings are never touched.

</details>

<details>
<summary><b>Other installers</b> (`npx skills` list tested locally; Gemini install not run)</summary>

```bash
npx skills add emmadal/agentic-workflow
gemini skills install https://github.com/emmadal/agentic-workflow --path .agents/skills
```

</details>

| Tool | Skills read from | Agents read from | Invoke |
|------|------------------|------------------|--------|
| Claude Code | `.claude/skills/` | `.claude/agents/` | `/spec` or ask naturally |
| OpenCode | `.agents/skills/` | `.opencode/agents/` | "use the spec skill" |
| Cursor | `.agents/skills/` | `.cursor/agents/` | `/spec` in Agent chat |
| Codex | `.agents/skills/` | `.codex/agents/*.toml` | `$spec` or `/skills` |
| Gemini CLI | `.agents/skills/` | `.gemini/agents/` | "use the spec skill" |

After installing, restart the tool and check: type `/` in Claude Code and look for `spec`, or run `claude -p "list project skills"`.

## What you get

| You are doing | Skill | What you get |
|---------------|-------|--------------|
| Unsure what to build | `discover` | Questions, then 2 or 3 options with trade-offs |
| Starting a change | `spec` | Goals, non-goals, testable acceptance criteria |
| Splitting the work | `plan` | Small ordered tasks, dependencies, risks |
| Building | `incremental-implementation` + `test-driven-development` | Thin slices, each with a test that failed first |
| Something broke | `debugging` | Reproduce, isolate, fix the cause |
| Before merge | `code-review` | Ranked findings and a verdict |
| Opening the PR | `ship` | Checks run, independent review, short PR. Never merges |
| Going live | `release` | Checklist, staged rollout, rollback |
| Coming back tomorrow | `context-save` / `context-restore` | Checkpoint to `.context/checkpoints/`, then resume exactly |

### Session continuity

- `context-save` writes a checkpoint (goal, decisions, done, remaining work, git state) to `.context/checkpoints/<time>-<title>.md`. The folder is excluded from git.
- `context-restore` loads the newest checkpoint, compares branch and commits with the repo, reports drift and proposes the next step. It waits for your go-ahead before editing.

Checkpoints are local notes. Never put secrets in them.

### Personal skills

- `accountability`: turns goals into commitments with a date and a proof, keeps a ledger in `.context/accountability.md`, runs check-ins and weekly reviews, and does not accept "almost".
- `secretary`: meeting minutes with owners and dates, email and message drafts and replies, plans, briefs. Drafts only; it never sends or books anything.
- `swe-interview`: mock coding, system design and behavioral interviews with one hint at a time, rubric scoring from 1 to 4, and drills aimed at your lowest scores.

## All 38 skills

**Define and plan:** `discover` `spec` `plan` `adr` `context-engineering`
**Build:** `incremental-implementation` `test-driven-development` `source-verified-coding` `code-simplification` `migration` `git-workflow`
**Backend and platform:** `backend-engineering` `api-design` `security-hardening` `observability` `performance-optimization` `ci-cd`
**Frontend:** `frontend-engineering` `browser-testing`
**Mobile:** `mobile-engineering` `swift-ios` `kotlin-android` `android-compose` `kotlin-multiplatform` `react-native` `expo` `mobile-device-testing`
**Quality and delivery:** `qa-testing` `test-plan` `debugging` `code-review` `ship` `release`
**Session continuity:** `context-save` `context-restore`
**Personal:** `accountability` `secretary` `swe-interview`

## Agents

Writer and reviewer are always different agents. No sub-agents in your tool? The skills tell the model to follow the same rules inline.

```
 ┌───────────────────────┐  ┌───────────────────────┐  ┌───────────────────────┐
 │  read-only            │  │  write                │  │  no edits             │
 │  planner, explorer,   │  │  implementer,         │  │  reviewer,            │
 │  architect            │  │  backend-engineer,    │  │  security-auditor     │
 │                       │  │  frontend-engineer,   │  │                       │
 │  task breakdown, code │  │  mobile-engineer      │  │  fresh-context diff   │
 │  search, design, ADRs │  │  one planned task,    │  │  review, security     │
 │                       │  │  test-first           │  │  audit                │
 └───────────────────────┘  └───────────────────────┘  └───────────────────────┘
```

## Why it is cheap and precise

- **Descriptions are triggers**, one line, 280 characters or less, so the model routes correctly without reading bodies.
- **Bodies are 400 words or less.** Depth lives in `references/` and is opened only when needed.
- **Always-on text is small:** all descriptions plus `AGENTS.md` come to about 2,700 tokens for 38 skills.
- **Routing is tested** on every PR: 114 prompts, 98.2% right at rank 1, 100% in the top 3, 38 of 38 negative prompts routed away.
- **Behavior is measured:** in a 90-run headless test, perfect runs were 26/30 with these skills, 7/30 with no skill and 14/30 with the closest upstream skills, at about 40% lower cost per run than upstream. Method and limits are in [`docs/benchmarks.md`](docs/benchmarks.md).

## Develop this repo

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest -q --cov=agent --cov=scripts --cov-fail-under=80
ruff check . && ruff format --check .
```

`.agents/skills/` and `.agents/agents/` are the only source of truth. After editing them:

```bash
python -m scripts.validate_skills        # lint skills and agents
python -m scripts.sync_agents            # regenerate .claude, .opencode, .codex, .cursor, .gemini
python -m scripts.route_eval --min-rank1 95
python -m scripts.token_report           # token cost of the catalog
```

Never edit the generated folders. CI runs `sync_agents --check` and fails on drift. Adding a skill also needs routing cases in `evals/routing.json`. The authoring rules are in [`docs/compatibility.md`](docs/compatibility.md).

## Project structure

```
.agents/skills/, .agents/agents/     source of truth
.claude/ .opencode/ .codex/ .cursor/ .gemini/   generated, do not edit
.claude-plugin/                      Claude Code plugin and marketplace manifests
scripts/                             sync_agents, validate_skills, install_skills, route_eval, token_report
evals/                               routing cases (CI) and behavioral evals
agent/, tests/                       small Python agent loop (optional) and tests
docs/                                workflow, sdlc, engineering-standards, compatibility, benchmarks, adr/
AGENTS.md, CLAUDE.md                 shared rules; CLAUDE.md imports AGENTS.md
```

### Optional agent loop

`agent/` is a minimal tool-using loop on the Anthropic SDK with step and token budgets. It does not load the skills above.

```bash
export ANTHROPIC_API_KEY=...
python -m agent.cli "explain the repo layout" --workdir .
# write_file and run_tests execute code; enable only in a sandbox
python -m agent.cli "add a --verbose flag" --workdir . --allow-write
```

## Principles

1. Spec before code.
2. Small, verifiable slices.
3. Tests are the feedback signal.
4. Writer and reviewer are separate agents.
5. Least privilege per role.
6. Deterministic gates (hooks, CI) over model memory.
7. Budgets and stop conditions on every loop.
8. Humans approve the plan and the merge.

## Limits

- Verified by running: Claude Code (all 38 skills load, also through `install_skills` and as a plugin) and OpenCode (`opencode debug agents` lists the 11 installed agents, and with an empty `HOME` the skill tool it sends to a mock model provider lists exactly all 38 skills installed in `.agents/skills/`, none missing, plus two OpenCode built-ins). `npx skills add . --list` run in this repo discovered and listed the project skills (I read the end of the list, from `swift-ios` to `test-plan`; I did not confirm each of the 38). Cursor, Codex and Gemini CLI are not installed here, so their loading was not run; their paths follow each tool's documentation. Details in [`docs/compatibility.md`](docs/compatibility.md).
- `accountability`, `secretary` and `swe-interview` have a small single-turn behavioral test (5 runs per cell) and a two-turn multi-turn test (5 reps per cell, see `docs/benchmarks.md`); longer multi-turn behavior (ledger check-ins over weeks, full interview rounds) is untested.
- Hooks in `.claude/settings.json` are Claude Code only; CI applies the same gates to every tool.
- Model pinning applies to Claude Code and OpenCode only.
- No license file yet. Add one before publishing.
