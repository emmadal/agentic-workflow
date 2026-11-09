---
name: plan
description: "Use when a spec is approved and the work must be broken into small ordered tasks, or when a task feels too large to start. Produces a task list with verification steps, dependencies and risks, then waits for approval. Do not use before acceptance criteria exist."
---
# Plan

Act as a staff engineer who sequences work to retire risk early.

1. Read the spec in `docs/specs/`. If criteria are missing, run `spec` first.
2. Delegate to the `planner` agent. If your tool has no sub-agents, do the planning inline using that agent's rules.
3. Write `docs/specs/<slug>.tasks.md`. Each task has: goal, files likely touched, verification command, dependencies, risk.
4. Order: spikes and risky integrations first, then vertical slices that each leave the system working, then polish.
5. Show the plan and wait for explicit approval before implementing.

Implement one task at a time. After each task: tests green, commit, then the next.
