---
name: incremental-implementation
description: "Use when implementing any multi-file change or the next task from a plan: build in thin vertical slices, verify and commit each one, use a feature flag for risky rollout."
---
# Incremental implementation

Loop per slice: **implement the smallest working piece, verify, commit, next.** Every slice leaves the system working.

1. Restate the task and its acceptance criteria. Read neighboring code and match its conventions.
2. Slice vertically (one thin path through UI, logic, data) not horizontally (all models first).
3. Every slice ships with a test for its new behavior, written first (`test-driven-development`), then the minimum code. A repo that already has tests is not an exemption: extend the nearest test file. Finding it is part of the slice — look beside the source file or under `tests/`. A slice with no new test is not done.
4. Run the project's real test, lint and type commands. Read their output.
5. Commit the slice with a conventional message (`git-workflow`).
6. Risky or user-visible: ship behind a flag, default off.
7. Out-of-scope ideas go in a note. Do not build them.

## Red flags
| Thought | Reality |
|---|---|
| "I'll test it all at the end" | A 500-line untested batch hides which line broke. |
| "While I'm here, I'll refactor" | Separate commit, or separate task. |
| "The repo already has tests" | Those cover old behavior. New behavior gets its own failing test. |
| "Splitting wastes my sunk effort" | Sunk cost is not a reason to ship an unverified batch. |

Stop and split when a slice passes about 100 changed lines with no verification.

## Verify
Each commit builds and passes tests alone; diff matches the task; nothing outside scope changed.
