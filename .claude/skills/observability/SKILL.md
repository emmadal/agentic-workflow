---
name: observability
description: "Use when adding or reviewing logs, metrics, traces, health checks, dashboards, alerts or SLOs, or before launching a service or app feature: make failures visible and diagnosable."
---
# Observability

Goal: answer "what broke, for whom, since when, why" without a redeploy.

1. **Logs**: structured JSON, levels used honestly, `request_id` and user-safe ids on every line, errors with stack and context. No secrets or PII.
2. **Metrics**: RED for services (rate, errors, duration percentiles), USE for resources (utilization, saturation, errors). Keep label cardinality low.
3. **Traces**: propagate trace context across services and into mobile clients.
4. **Health**: liveness (process up) and readiness (dependencies ok) probes.
5. **SLOs**: pick a user-visible indicator and target (e.g. 99.9% of requests under 500 ms). Alert on SLO burn or user symptoms, not on CPU.
6. **Alerts** must be actionable: each links a runbook and has an owner. Delete noisy ones.
7. **Mobile**: crash and ANR reporting with symbols or mapping files, startup and screen-load timings, network error rate, release health by version.
8. **Dashboards** per service: golden signals, recent deploys, dependency health.
9. More logs is not more observability: a few queryable fields beat paragraphs. Two or more services means traces.
10. **Release markers**: tag deploys so regressions line up with changes.

## Red flags
`catch` that logs nothing · `console.log` debugging left in · alert with no runbook · metric labeled by user id · logging full request bodies.

## Verify
Trigger a failure in staging and see it in logs, metrics and the alert; a new on-call can diagnose from the dashboard.
