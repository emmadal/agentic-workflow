# Semantic conventions: current stable names and legacy replacements

Source of truth: the attribute registry at `opentelemetry.io/docs/specs/semconv/registry/`. This file reflects the stable state verified at writing time — when in doubt, check the registry before emitting a name.

## Migration mechanism

Instrumentations migrating from experimental conventions use:

```sh
OTEL_SEMCONV_STABILITY_OPT_IN=http,database      # emit only stable names
OTEL_SEMCONV_STABILITY_OPT_IN=http/dup,database/dup   # emit both during a phased rollout
```

New projects: opt into the stable names from day one and never enable `/dup`.

## Resource attributes (service identity)

| Attribute | Status | Notes |
| --- | --- | --- |
| `service.name` | stable | `OTEL_SERVICE_NAME` env var wins over `OTEL_RESOURCE_ATTRIBUTES` |
| `service.version` | stable | Build artifact version or git hash |
| `service.instance.id`, `service.namespace` | stable | Distinguish replicas and logical ownership |
| `deployment.environment.name` | stable | values: development, staging, production, test |
| `deployment.environment` | **deprecated** | Use `deployment.environment.name` |
| `telemetry.sdk.{name,language,version}` | stable | Set by the SDK |
| `host.*`, `k8s.*`, `process.*`, `cloud.*` | mostly stable/development | Prefer collector `resourcedetection`/`k8sattributes` over hand-set |

## HTTP (stable)

Span name for server spans: `{method} {http.route}` (`HTTP` when method unknown); client spans: `{method}`, or `{method} {url.template}` when a low-cardinality template is available — instrumentation MUST NOT default to the raw URI path.

Key attributes (client and server):

| Stable name | Notes |
| --- | --- |
| `http.request.method` | Known methods only, `_OTHER` otherwise; original in `http.request.method_original` |
| `http.response.status_code` | int |
| `http.route` | Low-cardinality route template, e.g. `/users/:id`; required on server spans when available |
| `url.full` | Client; credentials redacted (`https://REDACTED:REDACTED@...`), sensitive query params replaced by `REDACTED` |
| `url.path`, `url.query`, `url.scheme` | Server |
| `server.address`, `server.port` | Host the request was sent to (client) / received for (server, from Host or X-Forwarded-Host) |
| `client.address`, `client.port` | Server: forwarded client, else socket peer |
| `network.peer.address`/`port`, `network.protocol.{name,version}`, `network.transport` | Wire details |
| `error.type` | Low-cardinality error class (e.g. `timeout`, status code as string) |

Old → new (from the official HTTP migration guide):

| Legacy | Stable |
| --- | --- |
| `http.method` | `http.request.method` |
| `http.status_code` | `http.response.status_code` |
| `http.url` | `url.full` |
| `http.target` | `url.path` + `url.query` |
| `http.scheme` | `url.scheme` |
| `http.host` | `server.address` |
| `http.flavor` | `network.protocol.version` |
| `http.client_ip` | `client.address` |
| `http.request_content_length` | `http.request.body.size` (opt-in) |
| `http.response_content_length` | `http.response.body.size` (opt-in) |
| `net.peer.name`/`net.peer.port` | `server.address`/`server.port` (client) |
| `net.host.name`/`net.host.port` | `server.address`/`server.port` (server) |
| `net.sock.peer.addr`/`port` | `network.peer.address`/`network.peer.port` |
| `net.sock.host.addr`/`port` | `network.local.address`/`network.local.port` |
| `net.protocol.{name,version}` | `network.protocol.{name,version}` |
| `http.user_agent` | `user_agent.original` |
| `http.resend_count` | `http.request.resend_count` |

Span status rules: 1xx–3xx unset; 4xx unset on server spans / `Error` on client spans; 5xx `Error`; set `error.type` on failures; do not set `Ok` explicitly. Request/response bodies are opt-in only (sensitive, large).

Stable HTTP metrics: `http.server.request.duration` and `http.client.request.duration`, unit **seconds** (histograms; replaces legacy `http.server.duration`/`http.client.duration` in ms).

## Database (stable)

Span name: `{db.query.summary}` when available, else `{db.operation.name} {target}` where target is `db.collection.name`, `db.namespace`, or `server.address`; else `{db.system.name}`. Kind: `CLIENT`.

| Stable name | Notes |
| --- | --- |
| `db.system.name` | Renamed from `db.system`; values like `postgresql`, `mysql`, `mongodb` |
| `db.collection.name` | Table/container (renamed from `db.sql.table`) |
| `db.namespace` | Renamed from `db.name` |
| `db.operation.name` | Renamed from `db.operation`; batch prepends `BATCH` |
| `db.query.text` | Renamed from `db.statement`; parameterized text ok by default, literals must be sanitized (`?`) |
| `db.query.summary` | New, low-cardinality grouping key (e.g. `SELECT wuser_table`), used as span name |
| `db.response.status_code` | New, DB error code |
| `db.operation.batch.size` | New |
| `db.query.parameter.<key>` | Opt-in; may contain PII |
| `db.stored_procedure.name` | Renamed from `db.operation.name`-adjacent conventions |

Stable DB metric: `db.client.operation.duration` (seconds; replaces legacy `db.client.duration`).

## Messaging

Status is newer than HTTP/DB: opt in with `OTEL_SEMCONV_STABILITY_OPT_IN=messaging` (or `messaging/dup`) and read `opentelemetry.io/docs/specs/semconv/messaging/messaging-spans/` for the exact current names per system (Kafka, RabbitMQ, SQS/SNS, Pub/Sub, Service Bus each have a dedicated page). Core concepts: producer vs consumer spans, `messaging.destination.name`, and operation-type distinctions for publish/process — confirm names in the per-system doc rather than copying from memory.

## GenAI / LLM workloads

`gen_ai.*` conventions (model, usage tokens, request/response attributes) are now maintained in the dedicated repo `github.com/open-telemetry/semantic-conventions-genai`; use that registry for `gen_ai.system`, `gen_ai.request.model`, token usage, and tool-call events.

## Attributes worth remembering

- `error.type`: low-cardinality error class on failed spans, also a metric attribute.
- `exception.*`: `exception.type`, `exception.message`, `exception.stacktrace` for recorded exceptions.
- `url.full` never carries credentials: redact user/password and signed-query parameters (`X-Amz-Signature`, `sig`, `X-Goog-Signature`, ...).
- Anything you add yourself: keep the `namespace.attr` shape, lowercase, dots for hierarchy, low cardinality — custom ids like `user.id` belong in logs with care, never in metric labels.
