---
name: ship
description: "Use when a change is implemented and ready to verify, review and open as a pull request: runs checks, independent review, commits, pushes the branch, opens a short PR. Never merges."
---
# Ship

1. Run lint, types, tests and the security scan (commands in `AGENTS.md`). Red means fix the cause, never the check.
2. Independent review: `reviewer` agent on the diff, or the `code-review` skill inline. Fix blockers and majors.
3. Touches auth, input, storage, network or dependencies? Run `security-auditor` or `security-hardening`.
4. Confirm definition of done (`docs/sdlc.md`): tests, docs, flags, rollback.
5. Conventional commit, author is the repo owner only, no co-author trailers (`git-workflow`).
6. Push the branch, never `main`. Open a PR with three short sections: Summary, Changes, Testing.
7. Do not merge. A human approves.

Never force-push, skip hooks or disable checks.

## Verify
CI green, PR text is short and accurate, nothing outside the task changed.
