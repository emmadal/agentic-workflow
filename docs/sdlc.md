# SDLC

Default model for the agent loop and all sub-agents: `claude-opus-5-5` (`opus`).
Override per run with `model=` in `run_agent`. Use a smaller model only for bulk, low-risk tasks.

## Phases

| Phase | Activities | Agent / skill | Exit criteria |
|-------|-----------|---------------|---------------|
| 1. Discover | Problem, users, constraints, success metrics | `/spec` | Spec approved, open questions closed |
| 2. Design | Options, data model, API contracts, threat model, rollout plan | `architect`, `/adr` | ADR accepted for hard-to-reverse choices |
| 3. Plan | Small tasks, dependencies, risks | `planner`, `/plan` | Plan approved |
| 4. Build | TDD, small slices, feature flags | `backend-engineer`, `frontend-engineer`, `mobile-engineer`, `implementer` | Tests, lint, types green |
| 5. Verify | Test plan, regression, E2E, a11y, performance, security | `qa-engineer`, `test-engineer`, `security-auditor`, `/test-plan` | Test plan exit criteria met |
| 6. Review | Fresh-context review, human review | `reviewer` | No blockers or majors, human approves |
| 7. Release | CI green, staged rollout, rollback ready | `/ship` | Canary healthy, rollback tested |
| 8. Operate | Monitoring, alerts, incident response, post-mortem | observability setup | SLOs tracked, alerts actionable |
| 9. Learn | Retro, evals, update docs and prompts | evals | Lessons recorded |

## Definition of ready

- Acceptance criteria are testable.
- Dependencies and risks are known.
- Rollout and rollback approach is stated.

## Definition of done

- Acceptance criteria met and covered by tests.
- Tests, lint, type check and security scan pass in CI.
- New behavior has logs, metrics and alerts where relevant.
- Docs, API specs and ADRs updated.
- Reviewed by `reviewer` and approved by a human.
- Behind a feature flag or safely backward compatible.
- Rollback path verified.

## Environments and releases

- Trunk-based development, short-lived branches, small PRs.
- Environments: local, CI, staging, production. Config via environment, never in code.
- Semantic versioning. Changelog per release.
- Staged rollout: flag off, internal, canary, percentage, full. Roll back on SLO breach.

## Incident response

1. Mitigate first (rollback, flag off). 2. Communicate. 3. Find root cause. 4. Blameless post-mortem with owned follow-ups.
