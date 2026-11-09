---
name: debugging
description: "Use when something fails, crashes, regresses or behaves unexpectedly and the cause is unknown: failing tests, stack traces, flaky behavior, production incidents, app crashes. Drives a reproduce-isolate-fix-verify loop and finds root cause before changing code."
---
# Debugging

Act as a senior engineer who fixes causes, not symptoms.

1. **Reproduce**: get a deterministic failing case (a test, a command, a device recipe). If you cannot reproduce, gather logs, versions, inputs and environment first.
2. **Read the evidence**: full error and stack trace, recent changes (`git log`, `git bisect`), logs around the failure. Quote the decisive line.
3. **Hypothesize**: list candidate causes ranked by likelihood. Each must predict something you can check.
4. **Isolate**: bisect the code path or the commit range, shrink the input, add temporary logging, use a debugger. Change one thing at a time.
5. **Fix the root cause**: the smallest change that removes the cause. No shotgun edits, no try/catch to hide it.
6. **Prove**: the failing test now passes, nearby tests still pass, and the regression test stays in the suite.
7. **Explain**: state root cause, why it was missed, and how to prevent a repeat.

For incidents: mitigate first (rollback, flag off), then investigate. For app crashes also use `mobile-device-testing` to collect crash logs.
