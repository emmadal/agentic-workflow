---
name: test-plan
description: "Use when a feature needs a risk-based test plan before release, covering unit, integration, end-to-end, performance, security, accessibility and, for apps, device and OS coverage. Writes docs/specs/<slug>.test-plan.md with exit criteria. Do not use to write the tests themselves."
---
# Test plan

Act as a senior QA lead. Spend effort where failure would hurt most.

Delegate to the `qa-engineer` agent if available; otherwise follow the `qa-testing` skill inline. For mobile, also apply `mobile-device-testing`.

Write `docs/specs/<slug>.test-plan.md`:
1. **Scope and top risks**, ranked by impact times likelihood.
2. **Test matrix**: level (unit, integration, E2E), what, who runs it, where (CI, staging, device).
3. **Cases from acceptance criteria**, then negative paths, boundaries, permissions, interruptions, concurrency.
4. **Environments and data**: OS versions, device classes, locales, network conditions, test accounts, seeded data.
5. **Non-functional**: performance budgets, accessibility, security, battery and memory for apps.
6. **Exit criteria**: exactly what must pass for release.
7. **Rollback verification**: how to prove rollback works.
