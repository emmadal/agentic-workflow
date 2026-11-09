# Project rules

Default model: `claude-opus-5-5` (sub-agents use `model: opus`). See `docs/adr/0001-default-model-opus.md`.
Process: `docs/sdlc.md`. Code standards (backend, frontend, mobile, QA, security, DevOps): `docs/engineering-standards.md`.

## Role routing
- Design and trade-offs: `architect` (+ `/adr`)
- Server code: `backend-engineer`; web UI: `frontend-engineer`; apps: `mobile-engineer`
- Tests and release risk: `qa-engineer`, `test-engineer` (+ `/test-plan`)
- Review: `reviewer`; security: `security-auditor`

## Definition of done
Acceptance criteria met and tested, CI green (lint, types, tests, coverage, security scan),
docs/ADRs updated, reviewed by `reviewer`, human approved, rollback path known.

## Commands
- Test: `pytest -q --cov=agent --cov-fail-under=80`
- Security: `bandit -q -r agent` and `pip-audit`
- Lint: `ruff check .`
- Format: `ruff format .`

## Workflow
1. Write or confirm a spec with acceptance criteria before coding (`/spec`).
2. Break work into small tasks, each ending in a passing check (`/plan`).
3. Test first: failing test, then code, then green.
4. Keep each change small. Touch few files per task.
5. Review with the `reviewer` sub-agent in fresh context before merge.
6. Ship with `/ship`. A human approves the merge.

## Conventions
- Python 3.11+, type hints on public functions.
- No new dependency without stating why.
- No secrets in code or logs. Read from environment.
- Errors: fail loudly, never swallow exceptions.

## Never
- Push to `main` directly.
- Skip or delete tests to get green.
- Run destructive commands (`rm -rf`, `git push --force`, DB drops) without explicit approval.
- Approve your own change. Use the reviewer.

## Commits and PRs
- Conventional commits: `feat:`, `fix:`, `docs:`, `test:`, `chore:`.
- Author is the repository owner only. No co-author trailers.
- PR description: short summary, what changed, how tested. No filler.
