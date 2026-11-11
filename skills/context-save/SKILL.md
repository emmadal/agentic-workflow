---
name: context-save
description: "Use when pausing, switching task or branch, ending a session, or the context window is filling up: saves a checkpoint of goal, decisions, remaining work and git state so context-restore can resume exactly."
---
# Context save

1. Run `scripts/context.sh state` for branch, HEAD, changed files and recent commits.
2. Write the checkpoint to the path printed by `scripts/context.sh path "<short title>"`. Folder is `.context/checkpoints/`, kept out of git.
3. Use this template, short and concrete:

```markdown
---
branch: <branch>
head: <short sha>
saved: <ISO time>
---
## Working on: <title>
### Goal
One or two sentences: what and why.
### Decisions made
- Decision and the reason. Include options rejected.
### Done
- Finished and verified (say which command proved it).
### Remaining work
1. Next step first. Name files and commands.
### Open questions and risks
- Anything blocked or unverified.
### Files in play
- path: why it matters
```

4. Never save secrets, tokens or `.env` content. Record failing test names and exact errors, not whole logs.
5. Do not commit, stash or change code. Saving is read-only apart from the checkpoint file.
6. Tell the user the file path and the one next step.

## Verify
File exists, `Remaining work` starts with an actionable step, a stranger could resume from it alone.
