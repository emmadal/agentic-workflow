---
name: api-design
description: "Use when designing or changing an HTTP, gRPC, library or module interface: contracts, error model, versioning, pagination, idempotency, backward compatibility, deprecation."
---
# API and interface design

Interfaces outlive implementations. Hard to change once consumers exist, and mobile apps cannot be force-updated.

1. **Contract first**: OpenAPI, Protobuf or a typed signature, reviewed before code. Generate clients and mocks from it.
2. **Errors**: one model everywhere: stable `code`, human `message`, `request_id`, field details. Correct status codes. Never leak internals.
3. **Compatibility**: additive changes only. Do not remove, rename or retype fields. New required input needs a default or a new version.
4. **Versioning**: explicit (path or header). Support N-1 at least. Publish a deprecation date, then follow `migration`.
5. **Lists**: pagination (cursor over offset), stable sort, filtering, a max page size.
6. **Writes**: idempotency keys for unsafe retries. Same key and same payload replays the stored response; same key with a different payload fails loudly (409 or 422); choose the in-flight duplicate behavior on purpose (409, wait, or 202). Validate and bound every input. Authorize each object, not only each route.
7. **Naming**: nouns for resources, consistent casing, ISO-8601 UTC timestamps, money as integer minor units plus currency.
8. **Docs and examples** for every endpoint, including failures.
9. Contract tests for each consumer, mobile clients included.

## Red flags
Boolean flags that change meaning · responses whose shape depends on state · `200` with an error body · unbounded list endpoints · breaking change shipped as a patch.

## Verify
Contract linted; consumers still pass contract tests; error cases documented; version and deprecation policy stated.
