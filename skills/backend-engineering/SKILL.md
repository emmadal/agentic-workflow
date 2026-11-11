---
name: backend-engineering
description: "Use when implementing server-side code: services, database schemas and migrations, authentication, authorization, background jobs, caching, resilience. For endpoint contracts also use api-design."
---
# Backend engineering

1. **Layers**: transport, domain, persistence. Business rules live in the domain, not in handlers or SQL strings.
2. **Data**: constraints, unique indexes and foreign keys enforce invariants. Transactions wrap multi-row invariants. Check query plans with `EXPLAIN`. Kill N+1 queries.
3. **SQL**: parameterized only. Never concatenate input.
4. **Migrations**: expand, migrate, contract. Backward compatible, reversible. Never drop or rename in the release that stops using the column.
5. **Auth**: authenticate every route; authorize every object (IDOR), not just roles. Hash passwords with Argon2id or bcrypt. Short-lived tokens, rotated keys.
6. **Input**: validate type, size and range at the boundary. Rate limit.
7. **Resilience**: timeout on every outbound call, retry with backoff and jitter on idempotent calls only, circuit breakers, graceful shutdown, health and readiness probes, dead-letter queue for failed jobs.
8. **Idempotency** for any write a client may retry.
9. **Observability**: structured logs with request id, RED metrics, traces (`observability`). No PII or secrets in logs.
10. **Config** from environment; secrets from a manager.

## Test
Unit for domain logic; integration against a real database in a container; contract tests for consumers; load test the hot path before launch.

## Red flags
Handler containing business logic · migration that locks a big table · retry on a non-idempotent call · catch-all `except` that hides errors · secrets in config files.

## Verify
Tests green, migration tested forward and back, dashboards and alerts exist, rollback known.
