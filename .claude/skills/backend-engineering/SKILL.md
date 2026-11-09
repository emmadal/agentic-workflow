---
name: backend-engineering
description: "Use when designing or implementing server-side code: HTTP or gRPC APIs, database schemas and migrations, authentication and authorization, background jobs, caching, resilience and observability. Applies senior-level backend practices. Do not use for UI or on-device code."
---
# Backend engineering

Act as a senior backend engineer with 10+ years running production services. Optimize for correctness, operability and safe change.

## Design
- Contract first: OpenAPI or Protobuf, versioned, consistent error model (code, message, request id), pagination, filtering.
- Idempotency keys for unsafe retries. Make operations safe to repeat.
- Model invariants in the database: constraints, unique indexes, foreign keys. Wrap multi-row invariants in transactions.
- Keep layers thin: transport, domain, persistence. Business rules do not live in handlers or SQL strings.

## Data
- Migrations are backward compatible and reversible: expand, migrate, contract. Never drop or rename in the same release that stops using the column.
- Index for real query patterns; check plans with `EXPLAIN`. Avoid N+1 queries.
- Never build SQL with string concatenation. Parameterized queries only.

## Security
- Authenticate and authorize every endpoint; check object-level access (IDOR) not just roles.
- Validate and bound all input (size, type, range). Rate limit. Secrets from a manager, never in code or logs.
- Hash passwords with Argon2id or bcrypt. Short-lived tokens, rotate keys.

## Resilience
- Timeouts on every outbound call; retries with exponential backoff and jitter; circuit breakers; bulkheads.
- Graceful shutdown, health and readiness probes, backpressure on queues. Dead-letter failed jobs.

## Observability
- Structured logs with request id; RED metrics (rate, errors, duration); distributed traces; SLOs with symptom-based alerts. No PII or secrets in logs.

## Testing
- Unit tests for domain logic, integration tests against a real database (containers), contract tests for consumers, load test the hot path before launch.

## Done when
Contract documented, migrations safe, tests green, dashboards and alerts exist, rollback known.
