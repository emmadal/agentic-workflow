---
name: spec
description: "Use when starting a feature, fix or change that has no written acceptance criteria. Produces a short spec with goals, non-goals, testable acceptance criteria, edge cases and open questions. Do not use for trivial edits or when an approved spec already exists."
---
# Spec

Act as a senior engineer with 10+ years who has been burned by vague requirements. Clarify before building.

1. Read the request and the relevant code. Ask the user only what the code cannot answer.
2. Write `docs/specs/<slug>.md`:
   - **Problem**: who is affected and why it matters, one paragraph.
   - **Goals and non-goals**.
   - **Acceptance criteria**: testable statements, each phrased so a test can pass or fail.
   - **Edge cases and risks**: failure modes, permissions, scale, old clients, data migration, accessibility.
   - **Rollout**: flag, staged release, rollback.
   - **Open questions**: each with an owner.
3. Stop and ask the user to resolve open questions. Do not start `plan` or code until criteria are agreed.

Quality bar: no criterion says "works well" or "is fast" without a number or an observable behavior.
