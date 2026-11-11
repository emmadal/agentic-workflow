---
name: release
description: "Use when preparing to deploy or launch to production or the app stores: pre-launch checklist, staged rollout, monitoring, rollback plan, post-launch review."
---
# Release and launch

1. **Pre-launch gate**: CI green, tests and security scan pass, migrations tested forward and back, docs and changelog updated, feature flags set, on-call aware.
2. **Rollback first**: write the rollback step before the deploy and test it. Mobile cannot be recalled: halt the staged rollout, flag off, ship a fix.
3. **Observability ready** (`observability`): dashboards, alerts and crash reporting live before traffic arrives. Name the 3 metrics that define healthy.
4. **Error-budget gate**: over 20% budget left, ship normally; 0-20%, slow rollouts and no risky changes; exhausted, freeze features and fix reliability. Treat a fast burn during canary as a hold.
5. **Staged rollout**: flag off, then internal, canary (1-5%), 25%, 100%. Hold at each step long enough to see real signals. Mobile: App Store phased release, Play staged rollout.
6. **Watch** error rate, latency, crash-free users, key business metric. Stop and roll back on a threshold you set beforehand.
7. **Stores**: privacy manifest and data safety form current, permission strings, screenshots, release notes, review-ready test account.
8. **Communicate**: release note, support brief, status page if user-facing.
9. **After**: confirm metrics for 24-48 h, remove temporary flags, record lessons and follow-ups.

## Red flags
No rollback plan · deploy on Friday evening with no on-call · changing schema and code in one irreversible step · "we'll add monitoring later".

## Verify
Rollback rehearsed, signals watched through each stage, flags cleaned up, post-launch note written.
