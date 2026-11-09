---
name: ship
description: Verify, review and open a PR. Use when a change is ready.
---
# Ship

1. Run `ruff check .` and `pytest -q`. Stop if red.
2. Run the `reviewer` sub-agent on the diff. Fix blockers and majors.
3. Run `security-auditor` if the change touches auth, input or dependencies.
4. Commit with a conventional message. No co-author trailers.
5. Push the branch and open a PR with a short description: summary, changes, testing.
6. Do not merge. A human approves.
