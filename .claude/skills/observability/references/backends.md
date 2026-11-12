# Backend setup: OpenTelemetry per language

Official auto-instrumentation first; manual spans only at business boundaries. All SDKs read the standard env vars (`OTEL_SERVICE_NAME`, `OTEL_EXPORTER_OTLP_ENDPOINT`, `OTEL_EXPORTER_OTLP_PROTOCOL`, `OTEL_TRACES_SAMPLER`); `OTEL_SEMCONV_STABILITY_OPT_IN` is a migration opt-in whose support varies per instrumentation — not a spec-standard variable. Config stays outside the code. Package names and APIs move; verify against the linked official doc when you wire a project.

Env baseline (12-factor, same for every language):

```sh
OTEL_SERVICE_NAME=checkout
OTEL_RESOURCE_ATTRIBUTES="deployment.environment.name=staging,service.version=1.4.2"
OTEL_EXPORTER_OTLP_ENDPOINT=http://collector:4317
OTEL_EXPORTER_OTLP_PROTOCOL=grpc            # or http/protobuf (endpoint 4318)
OTEL_TRACES_SAMPLER=parentbased_traceidratio
OTEL_TRACES_SAMPLER_ARG=0.1
OTEL_SEMCONV_STABILITY_OPT_IN=http,database   # migration opt-in: support varies per instrumentation
```

## Python

Docs: `opentelemetry.io/docs/languages/python/` (auto-instrumentation and manual pages).

```sh
pip install opentelemetry-distro opentelemetry-exporter-otlp
opentelemetry-bootstrap -a install      # detects installed libs and installs their instrumentations
opentelemetry-instrument uvicorn app:app
```

- Distro reads env vars and wires exporters. Keep providers global (`trace.set_tracer_provider(provider)`).
- Manual span: `with tracer.start_as_current_span("order.process") as span:` — or the `@tracer.start_as_current_span("...")` decorator; on failure `span.record_exception(ex)` + `span.set_status(Status(StatusCode.ERROR))`.
- Metrics: `MeterProvider` with a `PeriodicExportingMetricReader` exporting OTLP.
- Logs: bridge stdlib `logging` with `LoggingHandler` from `opentelemetry.sdk._logs` (LoggerProvider + `BatchLogRecordProcessor`), so records carry trace ids; async runtimes must keep providers alive for the whole process.
- Stable HTTP/DB conventions via `OTEL_SEMCONV_STABILITY_OPT_IN` supported since Python 1.44.0 / contrib 0.65b0.

## Node.js / TypeScript

Docs: `opentelemetry.io/docs/languages/js/`.

```sh
npm i @opentelemetry/sdk-node @opentelemetry/auto-instrumentations-node \
  @opentelemetry/exporter-trace-otlp-http @opentelemetry/exporter-metrics-otlp-http
```

- Init in a dedicated module loaded first: `node --import ./otel.js server.js` (ESM) or `node --require ./otel.js` (CJS). In the module: `new NodeSDK({ traceExporter, metricReader, instrumentations: [getNodeAutoInstrumentations()] }).start()`.
- Express/Fastify, `http`, pg/mongo and most clients get instrumented automatically; spans come from auto-instrumentation, business spans from `tracer.startActiveSpan`.
- Logs: either bridge `@opentelemetry/api-logs` + OTLP log exporter, or keep Pino/Winston emitting JSON to stdout with trace-id injection for the `filelog` receiver. Serverless/edge: `@opentelemetry/instrumentation-aws-lambda`, or vendor edge runtimes with OTLP HTTP.
- Caveat: initialize before requiring frameworks; ESM loaders order matters (`--import` before app code).

## Go

Docs: `opentelemetry.io/docs/languages/go/` (Go is manual-init, no zero-code agent).

```go
import "go.opentelemetry.io/otel"
import "go.opentelemetry.io/otel/sdk/trace"
```

- SDK init: `trace.NewTracerProvider(trace.WithResource(...), trace.WithBatcher(otlptracegrpc.New(...)))` as global (`otel.SetTracerProvider`); same pattern for metric and log providers — plumb `context.Context` everywhere.
- HTTP servers/clients: wrap with contrib `otelhttp.NewHandler`/`otelhttp.Transport`; DB drivers via contrib instrumentations or third-party wrappers (e.g. `otelsql`).
- Logs: standard `log/slog` bridged with `go.opentelemetry.io/contrib/bridges/otelslog`, or stdout JSON with trace-id fields.
- Graceful shutdown: `tracerProvider.Shutdown(ctx)` on SIGTERM or the last batches are lost.
- Metric names/units: follow stable semconv (`http.server.request.duration` is in seconds).

## Java

Docs: `opentelemetry.io/docs/languages/java/instrumentation/`.

- Zero code: download `opentelemetry-javaagent.jar` and run with `-javaagent:/path/opentelemetry-javaagent.jar` — instruments Spring/JDBC/Kafka/logging frameworks from env vars.
- Log capture for Log4j2/Logback comes with the agent; configure `OTEL_LOGS_EXPORTER=otlp` (default) or keep stdout JSON + collector.
- If the agent cannot be used (GraalVM, strict classpath): `opentelemetry-java` SDK with `sdk-extensions/autoconfigure` reads the same env vars.
- Caveats: `-javaagent` must be the first JVM option; verify instrumentation modules list per agent version; Spring Boot can use the dedicated `opentelemetry-spring-boot-starter` instead.

## .NET

Docs: `opentelemetry.io/docs/languages/dotnet/instrumentation/`.

- Code-first: NuGet `OpenTelemetry.Extensions.Hosting`, in DI: `builder.Services.AddOpenTelemetry().ConfigureResource(...).WithTracing(t => t.AddAspNetCoreInstrumentation().AddHttpClientInstrumentation().AddSource("MyApp")).WithMetrics(m => m.AddRuntimeInstrumentation().AddMeter("MyApp")).UseOtlpExporter()`.
- Zero code: `OpenTelemetry.AutoInstrumentation` via the official install scripts (`CORECLR_ENABLE_PROFILING` / startup hooks for .NET Core).
- Logs: `OpenTelemetry.Extensions.Hosting` log bridge (`builder.Logging.AddOpenTelemetry()`), or `ILogger` JSON to stdout + collector.
- Caveat: SDK assemblies are load-context sensitive in plugins; AOT/blazor differ — check docs for the app model.

## Rust

Docs: `opentelemetry.io/docs/languages/rust/`.

- Crates: `opentelemetry`, `opentelemetry_sdk`, `opentelemetry-otlp` (+ `opentelemetry-semantic-conventions`). Most teams go through `tracing`: `tracing-subscriber` with the `tracing-opentelemetry` layer, so `info!`/`error!` become both logs and spans.
- Build providers manually: `opentelemetry_sdk::trace::TracerProvider` + `BatchSpanProcessor` + OTLP exporter; register global, keep it alive for the process lifetime.
- Metrics via `opentelemetry_sdk::metrics` `MeterProvider` with `PeriodicReader`. Runtime API churn is real — pin versions and check the docs page for the release you use.

## PHP

Docs: `opentelemetry.io/docs/languages/php/instrumentation/` (verify the auto-instrumentation package list at packagist for your framework).

```sh
composer require open-telemetry/sdk open-telemetry/exporter-otlp
composer require open-telemetry/opentelemetry-auto-symfony   # or -auto-laravel, -auto-psr-15, -auto-slim
```

- Framework auto-packages exist for Symfony, Laravel, Slim, PSR-15, plus `auto-pdo`, `auto-guzzle`, async HTTP. Enable with `OTEL_PHP_AUTOLOAD_ENABLED=true`.
- Without a framework package, wire SDK manually (tracer/meter/logger providers + OTLP exporter).
- Long-running workers: flush processors on loop end; FaaS use the `auto-aws-lambda` style wrappers where available.

## Ruby

Docs: `opentelemetry.io/docs/languages/ruby/instrumentation/`.

```sh
gem install opentelemetry-sdk opentelemetry-exporter-otlp opentelemetry-instrumentation-all
```

- `OpenTelemetry::SDK.configure { |c| c.use_all() }` (or `use <instrumentation>`) in a Rails initializer / entrypoint; `service_name` and exporters come from env vars.
- Rails/Sinatra, Net::HTTP, Redis, Sidekiq covered by `instrumentation-all`.
- Logs: prefer stdout JSON + collector; OTLP logs support exists but verify gem maturity for your version.

## Mobile (out of core scope)

For mobile apps use this skill for the backend side and the repo's mobile skills for the app: crash reporting with symbols/mapping files, release health per version, and SDKs that propagate W3C context so app and backend share one trace.
