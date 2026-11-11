---
name: plan
description: "Use when an approved spec must be split into small ordered tasks with verification, dependencies and risks, or a task feels too big to start. Waits for approval before building."
---
# Plan

Write `docs/specs/<slug>.tasks.md`. Delegate to the `planner` agent, or do it inline if sub-agents are unavailable.

Per task: goal in one sentence · files touched · verification command · depends on · risk (low, medium, high).

1. No spec or criteria? Run `spec` first.
2. Order: spikes and risky integrations first, then vertical slices that each leave the system working, then polish.
3. Each task fits one commit and one review. If it needs "and", split it.
4. Name rollout and rollback for anything user-facing.
5. Show the plan. Wait for explicit approval. Then follow `incremental-implementation`.

## Red flags
Horizontal layers ("all models, then all APIs") · a task with no verification command · more than ~10 tasks without a milestone check · estimate-free plan for risky work.

## Verify
Every acceptance criterion is covered by a task; the first task is the riskiest; the plan was approved.
