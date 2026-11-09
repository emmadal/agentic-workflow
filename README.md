# agentic-workflow

Template for an AI agentic software engineering workflow.

```
Spec -> Plan -> Implement -> Test -> Review -> Ship -> Observe
```

Each stage has an owner (sub-agent or skill), a defined output and a gate.

## Contents

| Path | Purpose |
|------|---------|
| `CLAUDE.md` | Project rules loaded into every session |
| `.claude/agents/` | Role sub-agents with scoped tools |
| `.claude/skills/` | Reusable procedures: `spec`, `plan`, `ship` |
| `.claude/settings.json` | Permissions and hooks (test gate, destructive command block) |
| `agent/` | Minimal Python agent loop (Anthropic SDK) with step and token budgets |
| `tests/` | Tests for the loop and tools |
| `.github/workflows/ci.yml` | Lint and test on every PR |
| `docs/workflow.md` | Stage definitions and gates |

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

Use with Claude Code: open the repo, then run `/spec`, `/plan`, implement slice by slice, `/ship`.

## Adapting

- Replace test and lint commands in `CLAUDE.md`, `.claude/settings.json` and CI.
- Edit agent prompts in `.claude/agents/` for your stack.
- Add MCP servers (GitHub, Sentry, DB) in `.mcp.json`.
