---
name: qa
description: "Use when asked to QA, test and fix, or find bugs in a running web app, site, API or CLI, or to check 'does this work?' before shipping: explore, reproduce, fix with a regression test, commit, health score."
---
# QA: test, fix, verify

Find real bugs in the running product, then fix them one at a time with proof. Test plans and strategy: `qa-testing`. "Report only" skips fixes.

## Setup
1. Target: URL, API route or command (infer from the diff or ask). Tier: `quick` fixes critical and high, `standard` adds medium (default), `exhaustive` adds low. Optional `regression <old report>`.
2. `bash scripts/qa-run.sh init <label>` makes a fresh run folder with `report.md` and prints branch, base, tree state and changed files.
3. Fixes need a clean tree. If dirty, ask: commit, stash, or abort.
4. No URL on a feature branch: scope to what the diff touches; `bash scripts/qa-run.sh ports` finds local servers.
5. Never ask for or type real credentials; use test accounts or seeded data. Ask before submitting forms or deleting anything on a non-local target.

## Explore (baseline before any fix)
- One charter per behavior: contract, risk, entry point, expected result. Prove the happy path first, including durable effects.
- Web: `node scripts/probe.mjs <url> --out <run>/evidence [--mobile] [--links]` captures screenshot, console and page errors, failed requests, timing, accessibility gaps and links. Then drive flows with Playwright or your browser tool, using the checklist in `references/issue-taxonomy.md`.
- API and CLI: real requests and commands; status, response shape, errors, auth, idempotency, exit codes.
- Each finding: replay the exact steps once to confirm, minimize, save evidence, classify by severity and category.

## Fix loop (skip in report-only)
In severity order, within the tier:
1. Write a regression test at the smallest level that shows the bug. Run it; it must fail for the bug's reason.
2. Minimal fix in the responsible files. Re-run the test, the original repro and the nearby happy path.
3. Commit test and fix together: `fix(qa): ISSUE-NNN <summary>`. Mark it verified, best-effort or reverted.
4. Stop and ask after 2 reverts, any edit outside the finding's files, or every 5 fixes. Hard cap: 30 fixes.

## Report
Complete `report.md`: health score before and after (`references/health-score.md`), issues with evidence, fixes with SHAs, deferred items, what was not tested. Summary line: "QA found N issues, fixed M, health X to Y." API and CLI runs report pass, fail and blocked contracts instead of a score.

## Rules
Evidence or it did not happen. Timeouts and blocked probes never pass. Never weaken, skip or delete tests, and never edit CI to get green.
