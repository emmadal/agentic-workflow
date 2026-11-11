---
name: ci-cd
description: "Use when creating or fixing CI/CD pipelines, quality gates, caching, workflow secrets, deployment automation with rollback, or flaky builds (GitHub Actions and similar)."
---
# CI/CD

1. **Gates on every PR**: lint, format check, types, tests with coverage floor, dependency and static security scan, build. Fast feedback first (lint, unit), slow last.
2. **Same commands as local.** CI runs what `AGENTS.md` documents. No CI-only magic.
3. **Least privilege**: `permissions: contents: read` by default; widen per job. Pin third-party actions to a full commit SHA (Dependabot keeps them current). Never echo secrets. Use OIDC instead of long-lived cloud keys.
4. **Untrusted input**: never interpolate `${{ github.event.* }}` titles, bodies or branch names into `run:`. Pass through `env:` and quote.
5. **Speed**: cache dependencies, run jobs in parallel, `concurrency` to cancel superseded runs, `timeout-minutes` on every job.
6. **Determinism**: pinned toolchains, lockfiles, hermetic tests. Quarantine flaky tests and fix them.
7. **Deploy**: build once, attest it (build provenance, SBOM), promote the same artifact through environments. Staged rollout, health check, automatic rollback on failure. Production deploy needs approval.
8. **Mobile**: macOS runners for iOS, signing via secrets or `fastlane match`, upload symbols, Gradle Managed Devices or a device farm for tests, store upload as a manual gate.
9. Gate exceptions (skipped check, lint ignore) carry an owner and an expiry date.
10. **Fix flaky builds** by finding the nondeterminism, not by rerunning.

## Red flags
`continue-on-error` on a gate · secrets printed in logs · `latest` tags · deploy from a developer laptop · pipeline longer than 10 minutes with no caching.

## Verify
A failing test turns the PR red; a clean rerun is green; permissions are minimal; the pipeline time is known and acceptable.
