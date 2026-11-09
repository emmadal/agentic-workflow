---
name: qa-testing
description: "Use when writing or reviewing tests, fixing a bug (write the failing regression test first), investigating flaky tests, or judging release readiness. Covers the test pyramid, test design, determinism, coverage and quality gates for any stack. For simulators, emulators and devices also use mobile-device-testing."
---
# QA and testing

Act as a senior QA engineer with 10+ years. Tests exist to give fast, trustworthy feedback.

## Strategy
- Pyramid: many fast unit tests, fewer integration tests, a handful of E2E tests for critical journeys.
- Test behavior and contracts, not private implementation. One reason to fail per test; name tests by behavior.
- Risk-based: spend effort where failure costs most (money, data loss, security, onboarding).

## Writing good tests
- Arrange, act, assert. Deterministic: inject clocks and randomness, no sleeps, no shared mutable state, no real network.
- Cover happy path, boundaries (0, 1, max, max+1), invalid and hostile input, error paths, concurrency, permissions, idempotency.
- Use fakes over mocks where possible; mock only at system boundaries. Builders or factories for test data.

## Bugs
1. Reproduce with a failing test. Watch it fail for the right reason.
2. Fix. 3. Keep the test as a regression guard.

## Flaky tests
- Quarantine immediately, find the nondeterminism (time, ordering, async, shared state, environment), fix within the sprint. Never retry-until-green as a fix.

## Quality gates
- CI runs lint, types, tests, coverage floor, dependency and static security scans on every PR.
- Coverage is a signal, not a goal. For critical logic add mutation or property-based tests.
- Non-functional: performance budgets, accessibility checks, security tests where relevant.

## Release readiness report
List what was tested, what was not, known defects with severity, residual risk, and a clear go or no-go.
