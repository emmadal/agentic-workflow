---
name: ship
description: "Use when a change is implemented and ready to verify, review and open as a pull request. Runs lint, tests and security checks, runs an independent review, commits, pushes the branch and opens a short PR. Never merges. Do not use for exploratory work or failing builds."
---
# Ship

Act as a senior engineer who treats a PR as a product for the reviewer.

1. Run the project lint, type check, tests and security scan (commands in `AGENTS.md`). Stop if anything is red; fix the cause, never the check.
2. Run the `reviewer` agent on the diff. Fix blockers and majors. If sub-agents are unavailable, review the diff yourself against the `code-review` skill.
3. Run `security-auditor` when the change touches auth, input handling, storage, networking or dependencies.
4. Confirm the definition of done in `docs/sdlc.md`: tests, docs, flags, rollback.
5. Commit with a conventional message. Author is the repository owner only; no co-author trailers.
6. Push the branch (never `main`) and open a PR with exactly three short sections: Summary, Changes, Testing.
7. Do not merge. A human approves.

Never force-push, skip hooks or disable checks.
