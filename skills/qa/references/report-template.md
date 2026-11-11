# QA report: {target}

| Field | Value |
|---|---|
| Date (UTC) | {date} |
| Target | {url, route or command} |
| Branch and commit | {branch} @ {sha} |
| Tier | quick / standard / exhaustive |
| Mode | fix / report only / regression against {old report} |
| Scope | {pages, routes, commands; or "diff-scoped"} |
| Environment | {local, staging, preview}; browser and viewport; test account used |

## Summary
QA found {N} issues, fixed {M}, health {X} to {Y}.

| Severity | Found | Fixed | Deferred |
|---|---:|---:|---:|
| critical | | | |
| high | | | |
| medium | | | |
| low | | | |

Top 3 to fix next:
1. ISSUE-NNN: {title}

## Health score (web)
| Category | Before | After |
|---|---:|---:|
| Functional | | |
| Console and network | | |
| Accessibility | | |
| UX | | |
| Performance | | |
| Visual | | |
| Content | | |
| Security | | |
| **Total** | | |

## Contracts (API and CLI)
| Contract | Command or request | Expected | Result (pass / fail / blocked / not run) | Evidence |
|---|---|---|---|---|

## Issues
### ISSUE-NNN: {short title}
- Severity and category:
- Where:
- Steps: 1. 2. 3. Observe:
- Expected / actual:
- Evidence: `evidence/issue-NNN-before.png`
- Status: verified / best-effort / reverted / deferred (reason)
- Regression test: `{path}` (failed before the fix, passes after)
- Commit: `{sha}` `fix(qa): ISSUE-NNN ...`
- After: `evidence/issue-NNN-after.png`

## Not tested
{flows, pages, roles, devices or environments not covered, and why}

## Ship readiness
{go / no-go and the residual risks that decide it}
