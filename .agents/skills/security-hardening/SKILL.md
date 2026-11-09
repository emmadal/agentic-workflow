---
name: security-hardening
description: "Use when reviewing code for vulnerabilities or when it handles login, input validation, auth, where to store secrets and tokens safely, uploads or dependencies, or before release: threat model, validate, authorize, scan."
---
# Security hardening

1. **Threat model** the change in five lines: assets, entry points, who the attacker is, what they gain, worst case.
2. **Input**: untrusted until validated for type, size, range and encoding at the boundary. Parameterize queries. Encode output for its context.
3. **AuthN/AuthZ**: check on every path and every object (IDOR). Deny by default. Re-check on the server; client checks are UX.
4. **Secrets**: never in code, logs, URLs, images or the app bundle. Use a secret manager. Rotate on exposure. Scan with gitleaks or trufflehog.
5. **Data**: TLS everywhere, encrypt sensitive data at rest, minimize collection, no PII in logs.
6. **Dependencies**: pin, audit (`pip-audit`, `npm audit`, `./gradlew dependencyCheck`), remove unused, review new ones.
7. **Web**: CSP, SameSite and HttpOnly cookies, CSRF tokens, no untrusted HTML, SSRF allowlists.
8. **Mobile**: Keychain or Keystore, no secrets in the bundle, validate deep links and intents, `exported` set deliberately, release builds not debuggable, certificate pinning only with a rotation plan.
9. **Errors**: generic message to the user, detail in server logs.
10. **Ask a human first** before: new auth flows, new categories of sensitive data, new external integrations, CORS changes, file upload handlers, rate-limit changes, elevated permissions.
11. **AI and agents**: treat model and tool output as untrusted; least-privilege tools; no secrets in prompts.

## Red flags
| Thought | Reality |
|---|---|
| "Internal only" | Internal services are SSRF and lateral-movement targets. |
| "Frontend validates it" | Attackers skip the frontend. |
| "It's just a test key" | Test keys leak into production. |

## Verify
Scans clean or findings triaged; every new input and route has validation and authorization; no secret in the diff or history.
