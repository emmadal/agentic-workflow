---
name: spec
description: "Use when starting a feature, fix or change with no written acceptance criteria. Produces goals, non-goals, testable criteria, edge cases, rollout and open questions. Skip for trivial edits."
---
# Spec

Write `docs/specs/<slug>.md`. Keep it to one page.

1. **Problem**: who is hurt, why now.
2. **Goals / non-goals**.
3. **Acceptance criteria**: each is a statement a test can pass or fail. Include a number or observable behavior; never "fast" or "works well".
4. **Edge cases**: failure modes, permissions, scale, concurrency, old clients, data migration, accessibility, offline.
5. **Rollout**: flag, staged release, rollback.
6. **Open questions**: each with an owner.

Resolve open questions with the user before `plan`. Unclear intent first goes to `discover`.

## Red flags
| Thought | Reality |
|---|---|
| "Requirements are obvious" | Write them. Disagreement shows up on paper, not in your head. |
| "I'll spec after I build" | That is documentation, not a spec. Criteria must predate code. |

## Verify
Every criterion maps to at least one planned test; no open question is unowned; non-goals prevent scope creep.
