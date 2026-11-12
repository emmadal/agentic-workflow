---
name: observability
description: "Use when adding or reviewing logs, metrics, traces, profiles, SLOs, alerts, dashboards or health checks in any backend, or before launch: OpenTelemetry-first, sampling, semconv."
---
# Observability

Goal: answer "what broke, for whom, since when, why" without a redeploy. One instrumentation: OpenTelemetry SDK → OTLP → Collector → any backend, no vendor code.

## Setup order
1. Identity: `OTEL_SERVICE_NAME` env + `deployment.environment.name`/`service.version` attrs.
2. Official auto-instrumentation per language; OTLP gRPC 4317 or HTTP 4318.
3. Manual spans only at business boundaries: `<domain>.<action>`, low-cardinality attributes; on failure `error.type` + status `Error` + `record_exception`.
4. Logs: bridge the logger to OTel (auto `trace_id`) or stdout JSON for the `filelog` receiver.
5. Metrics: RED via stable histogram names (see semconv); USE for resources.
6. SLOs on user journeys; multi-window burn-rate alerts with runbooks.

## Hard rules
- W3C `tracecontext`/`baggage`; one trace across every hop.
- `http.route`, not raw paths; never `user_id` in metric labels.
- Head sampling `parentbased_traceidratio`; Collector tail sampling keeps errors and slow traces 100%. Flush at SIGTERM.
- No secrets, tokens or bodies; redact `url.full` credentials.
- Collector: `memory_limiter` + `batch`, `resourcedetection`, `redaction`/OTTL `filter`.

## Legacy banned
StatsD, Jaeger UDP, Zipkin, vendor SDKs, Promtail → OTLP + Collector. `deployment.environment`, `db.statement`, `http.method`, `net.*` → stable semconv names.

## Verify
Break a dependency in staging: panels move, the error log carries the `trace_id`, the sampled trace shows the failing hop, the burn-rate alert fires with runbook.

Depth: `references/guide.md`, `backends.md`, `semantic-conventions.md`, `slo-and-alerts.md`.
