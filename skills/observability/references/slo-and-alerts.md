# SLOs, alerts, dashboards and health

## SLI first

Define SLIs from stable, always-collected signals — not from dashboards or guesses:

- **Availability**: fraction of requests with a non-error outcome — success = `http.server.request.duration` histogram with no `error.type` and status not in the 5xx class; track 4xx separately (client faults are not service faults).
- **Latency**: `http.server.request.duration` percentiles (p99 under a user-visible threshold like 500 ms).
- **Freshness / durability** for pipelines: time since last successful run, message age (messaging `*.duration` metrics), replication lag.
- Correctness: business SLI (orders completed / orders started) — the strongest signal users actually feel.

Target a user-visible objective per service (e.g. 99.9% of requests < 500 ms over 28 days). One or two SLOs per service; the error budget is `1 − target`.

## Multi-window burn-rate alerts

Alert on budget burn, not CPU. Canonical multi-window pairs (page = act now, ticket = fix this week):

| Condition | Second window | Action |
| --- | --- | --- |
| 14.4× burn over 1h | 14.4× over 5m | Page (~2% budget in an hour) |
| 6× burn over 6h | 6× over 30m | Page (~5% budget in 6h) |
| 3× burn over 1d | 3× over 2h | Ticket |
| 1× burn over 3d | 1× over 6h | Ticket |

Burn rate = `(actual error fraction) / (allowed error fraction)`. Both windows must burn to page — kills most flapping. Every alert: runbook link + owning team + severity; otherwise delete it.

## Alerts that are allowed

- SLO burn-rate (fast and slow windows).
- Symptom alerts with no SLO: error log spike with no correlated deploy, `absent()` telemetry (agent died — detect missing data itself), backup/replication failure.
- Alert hygiene: each alert answers "what does the user feel, what do I check first"; anything answering "CPU is high" belongs on a dashboard, not a pager. Delete or fix noisy alerts the same week.

## Dashboards

Per service, one screen, golden signals first:

1. **Traffic**: request rate by `http.route` (or job/topic).
2. **Errors**: error rate and `error.type` breakdown.
3. **Latency**: p50/p95/p99 of `http.server.request.duration`.
4. **Saturation**: the resource that fails first (connection pool, queue depth, memory).
5. **Dependencies**: downstream call rate/errors from `db.client.operation.duration` and outbound spans.
6. **Deploys**: annotations from `service.version`/release markers so regressions line up with changes.
7. **Exemplars on latency panels** linking percentiles to trace ids when the backend supports it.

Dashboards are for diagnosis, alerts are for paging; do not recreate the alert tree as panels.

## Health checks (process, not telemetry)

- `liveness`: process is alive — failure restarts the pod. Cheap, no dependency calls, no auth.
- `readiness`: can serve traffic — checks dependencies with short timeouts; failure removes the pod from load balancing.
- `startup`: slow warmup gets its own probe so liveness does not kill cold starts.
- Checks are endpoints with stable paths (`/healthz`, `/readyz`); keep them out of SLOs and sampled telemetry (drop at the collector).

## Runbook template

```markdown
## <Alert name> (owner: <team>, severity: <sev>)
Symptom: what users/queries feel.
Meaning: what the burn rate / metric says.
First checks (2 min): recent deploys (service.version), dependency status, error.type mix in traces/logs.
Mitigate: rollback <how>, turn off <flag>, scale <what>.
Escalate: <team/channel> after <time>.
Related: dashboard <link>, SLO <link>.
```

## Verification loop

Trigger a controlled failure in staging (kill a dependency, inject 500s): latency and error panels move, the burn-rate alert fires with its runbook, the error log carries the `trace_id`, and the tail-sampled trace shows the failing hop. A new on-call walks the runbook alone. If any step fails, the pipeline — not the incident drill — needs fixing.
