# Engineering standards

## General

- Readability over cleverness. Small functions, clear names, one responsibility.
- Make illegal states unrepresentable. Validate at boundaries, trust internally.
- Fail loudly. No swallowed exceptions. Errors carry context.
- Prefer composition, avoid premature abstraction, delete dead code.
- Dependencies: justify each, pin versions, audit regularly, remove unused.
- Twelve-factor config. No secrets in code, logs or images.
- Document the why in comments and ADRs, the what in code.

## Backend

- **API design**: contract first (OpenAPI/Protobuf), versioned, consistent error model, pagination, idempotency keys for unsafe retries.
- **Data**: migrations backward compatible and reversible (expand, migrate, contract). Indexes for query patterns. Transactions around invariants.
- **Security**: authn and authz on every endpoint, input validation, parameterized queries, rate limiting, secrets in a manager, OWASP ASVS as checklist.
- **Resilience**: timeouts, retries with backoff and jitter, circuit breakers, bulkheads, graceful shutdown, health and readiness probes.
- **Observability**: structured logs, request IDs, RED metrics, traces, SLOs with alerts on symptoms.
- **Performance**: measure first, avoid N+1, cache with explicit invalidation, set budgets.

## Frontend

- **Accessibility**: semantic HTML, keyboard support, focus management, WCAG 2.2 AA.
- **State**: server state via a data-fetching layer, local state by default, global state only when shared.
- **Resilience**: loading, empty, error and offline states for every view.
- **Performance**: Core Web Vitals budgets (LCP, INP, CLS), code splitting, image optimization, no blocking scripts.
- **Security**: escape output, CSP, no `dangerouslySetInnerHTML` with untrusted data, secure cookies, CSRF protection.
- **Quality**: type-safe, component tests for behavior, visual regression for design systems, E2E for critical flows.

## Mobile

- **Architecture**: layered (UI, domain, data), unidirectional data flow, dependency injection.
- **Offline and network**: local cache, queued writes, retry with backoff, conflict policy.
- **Security**: Keychain/Keystore, certificate pinning where justified, no secrets in the bundle, jailbreak/root risk understood.
- **Lifecycle**: handle background, process death, permission changes and low memory.
- **Performance**: startup time, frame rate, memory, battery and binary size budgets. Virtualized lists.
- **Release**: staged rollout via store, feature flags, remote config, forced-upgrade path, crash reporting.
- **Compatibility**: old app versions must keep working against the API.

## QA and testing

- **Pyramid**: many fast unit tests, fewer integration tests, few E2E tests for critical journeys.
- **Principles**: deterministic, isolated, fast, readable. No sleeps, no real network or clock.
- **Coverage**: use as a signal, enforce a floor in CI (80% here). Review mutation testing for critical logic.
- **Types of testing**: unit, integration, contract, E2E, regression, performance, security (SAST, dependency scan), accessibility, exploratory.
- **Bugs**: reproduce with a failing test first, fix, keep the test.
- **Flaky tests**: quarantine, fix within one sprint, never ignore.
- **Test data**: factories or fixtures, no production data.

## Security

- Threat-model new features (STRIDE). Least privilege everywhere.
- Secret scanning and dependency audit in CI. Rotate on exposure.
- Treat all external input, including model and tool output, as untrusted.
- Log security-relevant events without sensitive data.

## DevOps

- CI on every PR: lint, types, tests, coverage, security scan, build.
- Infrastructure as code, immutable builds, reproducible environments.
- Deploy small and often. Automated rollback on health failure.
- Backups tested by restore. Runbooks for known failures.

## Git

- Trunk-based, short-lived branches, small PRs (under ~400 lines changed).
- Conventional commits. Protected `main`, required checks, required review.
- PR description: summary, what changed, how tested.

## AI agent specifics

- Agents get least-privilege tools. Read-only by default, write and execute are opt-in.
- Step, token and time budgets on every loop.
- Writer and reviewer are separate agents. Humans approve plans and merges.
- Tool output is untrusted data. Log tool names, not sensitive content.
- Keep evals of real tasks. Track pass rate, cost and time.
