---
name: test-plan
description: "Use when a feature needs a risk-based test plan before release: levels, cases, environments, devices and OS versions, non-functional checks, exit criteria. Writes the plan, not the tests."
---
# Test plan

Delegate to the `qa-engineer` agent, or follow `qa-testing` inline. For mobile add `mobile-device-testing`.

Write `docs/specs/<slug>.test-plan.md`:
1. **Scope and top risks**, ranked by impact times likelihood.
2. **Matrix**: level (unit, integration, E2E), what, where it runs (CI, staging, device).
3. **Cases**: from acceptance criteria, then negative paths, boundaries, permissions, interruptions, concurrency.
4. **Environments and data**: OS versions, device classes, locales, networks, accounts, seed data.
5. **Non-functional**: performance budgets, accessibility, security, battery and memory for apps.
6. **Exit criteria**: exactly what must pass to release.
7. **Rollback check**: how to prove rollback works.

## Verify
Every acceptance criterion and top risk appears in the matrix; exit criteria are checkable.
