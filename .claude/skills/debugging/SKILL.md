---
name: debugging
description: "Use when something fails, crashes, regresses or misbehaves and you don't know why: failing tests, stack traces, flaky behavior, incidents. Reproduce, isolate, fix the root cause, prove."
---
# Debugging

0. **Stop the line**: stop building. Do not push past a failing test or broken build; errors compound. Preserve the evidence (error, logs, repro steps) before changing anything.
1. **Reproduce** deterministically (test, command, device recipe). Cannot reproduce? Collect versions, inputs, environment and logs first.
2. **Read the evidence**: full error and stack, recent changes (`git log`, `git bisect`), logs around the failure. Quote the decisive line.
3. **Hypothesize**: rank causes. Each must predict something you can check.
4. **Isolate**: bisect code or commits, shrink the input, add temporary logging, use a debugger. Change one thing at a time.
5. **Fix the root cause** with the smallest change. No shotgun edits. No try/catch to hide it.
6. **Prove**: the failing test now passes, neighbors pass, the regression test stays.
7. **Explain**: root cause, why it escaped, how to prevent a repeat.

Incident: mitigate first (rollback, flag off), investigate after. App crash: `mobile-device-testing` for logs.

## Red flags
| Thought | Reality |
|---|---|
| "Probably X, let me change it" | Test the hypothesis before editing. |
| "Fixed it, can't reproduce now" | Not fixed until a test fails without the fix. |
| "Add a retry" | That hides the cause. |

## Verify
Root cause is stated with evidence; regression test added; no unrelated edits.
