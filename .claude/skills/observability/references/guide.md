# Observability guide: pipeline, collector, sampling, cost

Verified against opentelemetry.io (specification, semconv registry, collector docs) at the time of writing; when a component name looks different, check the current docs before trusting this file.

## The four signals and where they belong

| Signal | Source | Notes |
| --- | --- | --- |
| Traces | OTel SDK, auto-instrumentation first | One trace per request; propagate W3C `tracecontext`/`baggage` everywhere |
| Metrics | OTel SDK | Pre-aggregated; the cheap always-on signal |
| Logs | Existing logger bridged to OTel, or stdout JSON → `filelog` receiver | LogRecord carries `trace_id`/`span_id` for correlation |
| Profiles | SDK push (pprof-based) or eBPF | Experimental OTLP endpoint `/v1/profiles`; add after the first three |

Baggage is for request-scoped metadata (tenant, feature-flag id), not for data you want to aggregate.

## Collector topology

- **Agent** (DaemonSet on Kubernetes, or sidecar on VMs): local OTLP receiver, does cheap work — `memory_limiter`, `resourcedetection`, `k8sattributes` enrichment, `batch` — then ships to the gateway or backend. One per node, not per pod.
- **Gateway** (Deployment/StatefulSet, one per cluster or region): the only place for **tail sampling**, expensive processing, PII `redaction`, and fan-out to multiple backends. Code never talks to a vendor directly.
- **Two tiers are required for tail sampling at scale**: an agent layer plus a gateway layer where the agent layer uses the `loadbalancing` exporter (routing by trace ID) so all spans of one trace reach the same gateway instance.

Minimal core config (names verified in the collector distributions; check versions):

```yaml
receivers:
  otlp:
    protocols:
      grpc: { endpoint: 0.0.0.0:4317 }
      http: { endpoint: 0.0.0.0:4318 }
processors:
  memory_limiter: { check_interval: 1s, limit_mib: 512 }
  resourcedetection: { detectors: [env, system] }
  batch: { timeout: 5s }
exporters:
  otlp: { endpoint: <backend-or-gateway>:4317 }
extensions:
  health_check: {}
service:
  pipelines:
    traces: { receivers: [otlp], processors: [memory_limiter, resourcedetection, batch], exporters: [otlp] }
```

Local development: run `otelcol-contrib` locally with the `debug` exporter, or a local all-in stack (docker compose); point the SDK at `http://localhost:4318`.

## Sampling

Two kinds, use both:

1. **Head sampling (SDK, cheap, keeps cost bounded)**: `OTEL_TRACES_SAMPLER=parentbased_traceidratio`, `OTEL_TRACES_SAMPLER_ARG=0.1`. Parent-based means children follow the root decision — no broken traces.
2. **Tail sampling (gateway, expensive, decision after seeing the whole trace)**: keep every error and every slow trace, drop the boring majority.

Verified tail-sampling policy types: `always_sample`, `latency` (`threshold_ms`), `numeric_attribute`, `probabilistic` (`sampling_percentage`), `status_code` (`[ERROR, UNSET, OK]`), `string_attribute`, `trace_state`, `trace_flags`, `rate_limiting`, `bytes_limiting`, `span_count`, `boolean_attribute`, `ottl_condition`, and combinators `and`, `not`, `drop`, `composite`. Defaults: `decision_wait: 30s`, `num_traces: 50000`.

```yaml
processors:
  tail_sampling:
    decision_wait: 10s
    num_traces: 5000
    decision_cache:
      sampled_cache_size: 100_000
      non_sampled_cache_size: 100_000
    policies:
      - name: keep-errors
        type: status_code
        status_code: { status_codes: [ERROR] }
      - name: keep-slow
        type: latency
        latency: { threshold_ms: 1000 }
      - name: baseline
        type: probabilistic
        probabilistic: { sampling_percentage: 10 }
      - name: drop-health-noise
        type: drop
        drop:
          drop_sub_policy:
            - name: probes
              type: string_attribute
              string_attribute: { key: http.route, values: [/healthz, /readyz, /metrics], enabled_regex_matching: true }
```

Stateful: spans wait in memory for a decision, so all spans of a trace must hit the same gateway (loadbalancing exporter above). Sample 100% in dev and staging; tune the ratio in production.

## Metrics discipline

- RED on services: request rate, error rate, `http.server.request.duration` and `db.client.operation.duration` percentiles (seconds, histograms). USE on resources (CPU, memory, connections, queues).
- Instrument names follow `<namespace>.<unit>` dot convention, lowercase; one instrument per measurement, attributes stay low-cardinality (`http.route`, `error.type`, `db.operation.name`).
- High-cardinality services: exponential histograms — `OTEL_EXPORTER_OTLP_METRICS_DEFAULT_HISTOGRAM_AGGREGATION=base2_exponential_bucket_histogram`.
- Temporality: default `cumulative`; `delta`/`lowmemory` via `OTEL_EXPORTER_OTLP_METRICS_TEMPORALITY_PREFERENCE` when the backend prefers it.
- Collector-side guards: `filter`/`transform` (OTTL) to drop noise, `redaction` for PII, `cardinalityguardian` (alpha) for metric label explosions.
- Banned: a metric per endpoint or per user; `user_id`, unbounded ids, or raw URLs as labels; `error.message` text as a label.

## Logs pipeline

Modern options, pick one and be consistent:

1. **Bridge to OTLP**: the language's log bridge/appenders push LogRecords with `trace_id`/`span_id` and resource — best correlation, needs SDK wiring.
2. **stdout JSON → `filelog` receiver**: keep the logger library-agnostic, the collector parses JSON, injects trace context from the log fields, and adds resource context.

Either way: one line per event, structured fields, severity honest (`ERROR` only for what needs action), no secrets or full request bodies, errors link a runbook. Legacy formats (syslog, log4j 1.x appenders) get parsed at the collector, not pushed as-is to a vendor.

## Legacy → modern replacements

| Legacy | Modern |
| --- | --- |
| StatsD / DogStatsD / OpenCensus exporters | OTLP from the OTel SDK |
| Jaeger UDP agent, Zipkin shipper, Jaeger all-in-one in production | OTLP → Collector (`otlp` receiver, gRPC 4317 / HTTP 4318) |
| Promtail scraping log files | Collector `filelog` receiver, or the vendor's OTel-compatible agent |
| Vendor tracer/profiler SDK hardcoded in app code | OTel SDK auto-instrumentation; vendor receives via gateway |
| Printing trace ids into log text | Log bridge with native trace context fields |
| Alerts on CPU/memory | SLO burn-rate alerts on user-visible symptoms |
| `deployment.environment`, `db.statement`, `http.method`, `net.*`, `http.status_code`, `http.url` | `deployment.environment.name`, `db.query.text`, `http.request.method`, `network.*`/`server.*`, `http.response.status_code`, `url.full` |
| Config per environment baked into code | Env vars: `OTEL_SERVICE_NAME`, `OTEL_EXPORTER_OTLP_ENDPOINT`, `OTEL_RESOURCE_ATTRIBUTES`, `OTEL_SDK_DISABLED=1` for tests |

## Environments

- Same image/binaries everywhere; only env vars differ. `deployment.environment.name` ∈ {development, staging, production, test}.
- `OTEL_SDK_DISABLED=1` (or exporters `none`) for unit tests so telemetry never blocks.
- Deploy markers: emit the release as a resource attribute `service.version` and tag deploys so dashboards line regressions with changes.
- Shutdown: flush exporters on SIGTERM (graceful shutdown in the language SDK) — telemetry lost in the last seconds hides exactly the errors that killed the pod.
