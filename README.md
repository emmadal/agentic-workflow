# agentic-workflow

Default model: Claude Opus 5.5 (`claude-opus-5-5`).

Template for an AI agentic software engineering workflow.

```
Spec -> Plan -> Implement -> Test -> Review -> Ship -> Observe
```

Each stage has an owner (sub-agent or skill), a defined output and a gate.

## Contents

| Path | Purpose |
|------|---------|
| `AGENTS.md` | Shared instructions for Claude Code, OpenCode, Cursor, Codex, Gemini CLI |
| `CLAUDE.md` | Imports `AGENTS.md` plus Claude-specific notes |
| `.agents/skills/` | Source of truth: 33 skills (process, backend, frontend, QA, security, delivery, mobile) |
| `.agents/agents/` | Source of truth: 11 role agents |
| `scripts/` | `sync_agents` generates per-tool files; `validate_skills` lints skills and agents |
| `docs/benchmarks.md` | Token and routing benchmark against `addyosmani/agent-skills` |
| `evals/routing.json` | Deterministic skill-routing cases, run in CI |
| `docs/compatibility.md` | Where each tool reads skills and agents, and how to invoke them |
| `.claude/`, `.opencode/`, `.codex/`, `.cursor/`, `.gemini/` | Generated agent and skill files. Do not edit |
| `.claude/settings.json` | Permissions and hooks (test gate, destructive command block) |
| `agent/` | Minimal Python agent loop (Anthropic SDK) with step and token budgets |
| `tests/` | Tests for the loop and tools |
| `.github/workflows/ci.yml` | Lint and test on every PR |
| `docs/workflow.md` | Stage definitions and gates |
| `docs/sdlc.md` | SDLC phases, definition of ready and done, release and incident process |
| `docs/engineering-standards.md` | Standards for backend, frontend, mobile, QA, security, DevOps |
| `docs/adr/` | Architecture decision records |

## Principles

1. Spec before code.
2. Small, verifiable slices.
3. Tests are the feedback signal.
4. Writer and reviewer are separate agents.
5. Least privilege per role.
6. Deterministic gates (hooks, CI) over model memory.
7. Budgets and stop conditions on every loop.
8. Humans approve the plan and the merge.

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
export ANTHROPIC_API_KEY=...
python -m agent.cli "explain the repo layout" --workdir .
# write_file + run_tests are code execution; enable only in a sandbox
python -m agent.cli "add a --verbose flag" --workdir . --allow-write
```

Use with any supported tool: open the repo, then run `spec`, `plan`, implement slice by slice, `ship`.
Skills load automatically from their descriptions, or by name (`/swift-ios`, `$swift-ios`). See `docs/compatibility.md`.

Edit `.agents/`, then:

```bash
python -m scripts.validate_skills
python -m scripts.sync_agents
```

## Adapting

- Replace test and lint commands in `CLAUDE.md`, `.claude/settings.json` and CI.
- Edit agent prompts in `.claude/agents/` for your stack.
- Add MCP servers (GitHub, Sentry, DB) in `.mcp.json`.
