---
name: test-plan
description: Produce a risk-based test plan for a feature. Use after /spec and before release.
---
# Test plan

Delegate to the `qa-engineer` sub-agent. Write `docs/specs/<slug>.test-plan.md`:

1. Scope and risks
2. Test matrix: unit, integration, E2E, performance, security, accessibility
3. Edge cases and negative paths from the acceptance criteria
4. Test data and environments
5. Exit criteria: what must pass before release
6. Rollback verification
