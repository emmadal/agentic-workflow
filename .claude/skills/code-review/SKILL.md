---
name: code-review
description: "Use when reviewing a diff or pull request before merge, or checking your own changes for bugs: correctness, tests, security, design, performance, scope. Returns ranked findings and a verdict."
---
# Code review

1. Learn intent from the spec, PR text and commits. Review against intent.
2. Read tests first. Do they prove the behavior and the failure paths?
3. Read the diff (`git diff`, `git diff --staged`). Trace input to output.
4. Check: **correctness** (edges, null, concurrency, cleanup), **tests** (new behavior covered, none weakened), **security** (validation, authz, secrets, injection), **design** (right layer, no needless abstraction), **performance** (N+1, unbounded work, main thread), **scope** (unrelated changes, new dependencies). Mobile: lifecycle, threading, permissions, old-version compatibility.
5. Self-doubt pass: for each "looks fine", name how it could fail in production.

## Output
`path:line: blocker|major|minor: problem. fix.` One line each. No praise, no style nits unless they hide bugs.
End: `Verdict: approve` or `Verdict: changes requested`.

## Red flags
| Thought | Reality |
|---|---|
| "Tests pass, so it's fine" | Passing tests prove only what they assert. |
| "Author is senior" | Review the diff, not the person. |
| "Too big to review" | Ask to split it. |

## Verify
Every blocker has a concrete fix; findings cite lines; the verdict follows from the findings.
