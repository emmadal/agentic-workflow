# Workflow

| Stage | Owner | Output | Gate |
|-------|-------|--------|------|
| Spec | `/spec` skill | `docs/specs/<slug>.md` | Human approves criteria |
| Plan | `planner` agent | task list | Human approves plan |
| Implement | `implementer` agent | code + tests, one task per commit | `pytest`, `ruff` green |
| Test | `test-engineer` agent | edge case tests | Coverage gaps reported |
| Review | `reviewer` agent (fresh context) | findings | No blockers or majors |
| Security | `security-auditor` agent | findings | No high severity |
| Ship | `/ship` skill | PR | CI green, human merges |
| Observe | logs, evals | pass rate, cost, time | Review failed traces |

## Safety

- Reviewer, explorer, auditor, planner are read-only.
- Destructive commands denied in `.claude/settings.json`.
- Agent loop enforces step and token budgets and confines file access to the workdir.

## Evals

Keep a set of real tasks with expected outcomes. Track pass rate, steps, tokens and time per change.
Fix tool descriptions first, prompts second, structure last.
