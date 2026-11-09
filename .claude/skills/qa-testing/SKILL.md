---
name: qa-testing
description: "Use when designing or reviewing a test strategy, fixing flaky tests, closing coverage gaps, or judging release readiness for any stack. For mobile also use mobile-device-testing."
---
# QA and testing

1. **Pyramid**: many fast unit tests, fewer integration tests, a few E2E tests for critical journeys. Invert it and CI becomes slow and flaky.
2. **Risk first**: test where failure costs most (money, data loss, security, onboarding).
3. **Good tests**: arrange, act, assert. One reason to fail. Named by behavior. Deterministic: injected clock and randomness, no sleeps, no shared state, no real network.
4. **Cases**: happy path, boundaries (0, 1, max, max+1), invalid and hostile input, error paths, concurrency, permissions, idempotency, upgrade and rollback.
5. **Fakes over mocks**; mock only at system boundaries. Builders for test data.
6. **Flaky test**: quarantine now, find the nondeterminism (time, order, async, shared state, environment), fix within the sprint. Retry-until-green is not a fix.
7. **Gates in CI**: lint, types, tests, a coverage floor, dependency and static security scans. Coverage is a signal, not a goal. Use mutation or property-based tests for critical logic.
8. **Non-functional**: performance budgets, accessibility, security checks where relevant.

## Release report
Tested, not tested, open defects with severity, residual risk, go or no-go.

## Red flags
Assertion-free tests · tests coupled to private methods · green suite that never ran the new code · coverage chased with trivial tests.

## Verify
New behavior fails without the change; suite is deterministic over 3 consecutive runs; report names what was not covered.
