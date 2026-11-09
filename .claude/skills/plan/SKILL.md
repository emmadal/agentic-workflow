---
name: plan
description: Break an approved spec into small verifiable tasks. Use after /spec.
---
# Plan

1. Read the spec in `docs/specs/`.
2. Delegate to the `planner` sub-agent.
3. Write the task list to `docs/specs/<slug>.tasks.md`.
4. Show the plan to the user and wait for approval.

Then implement one task at a time with the `implementer` sub-agent.
