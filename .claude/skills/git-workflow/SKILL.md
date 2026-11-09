---
name: git-workflow
description: "Use when committing, branching, rebasing, resolving conflicts, splitting a large change into reviewable commits, or preparing a PR: atomic conventional commits and short-lived branches."
---
# Git workflow

1. **Trunk-based**: short-lived branches off `main`, small PRs (about 400 changed lines max), merged often. Never commit to `main` directly or force-push shared branches.
2. **Atomic commits**: one logical change, builds and passes tests alone. Refactors, formatting and features go in separate commits.
3. **Message**: conventional type and scope, imperative subject under 72 chars. Body says why. `feat(auth): add token refresh`. Types: `feat fix docs test refactor perf chore ci`.
4. **Authorship**: commit as the repository owner only. No co-author or tool trailers unless the owner asks.
5. **Before commit**: `git status`, `git diff --staged`. Stage by path, not `git add -A`. Check for secrets and stray files.
6. **Sync**: `git fetch`, rebase your branch on `main`. Resolve conflicts by understanding both sides, then rerun tests.
7. **Split big changes** with `git add -p` or stacked branches so each piece is reviewable.
8. **PR**: short Summary, Changes, Testing. Link the issue. Draft until CI is green.
9. **Undo safely**: `git revert` for shared history; `reset` or `rebase` only on unpushed commits.
10. Never `--no-verify`, `reset --hard` or `clean -fd` without checking what is lost.

## Red flags
"WIP" commits pushed to review · a commit that breaks the build · giant PR with mixed concerns · conflict markers committed.

## Verify
`git log --oneline` reads like a changelog; each commit passes CI; PR text is short and accurate.
