# nextjs-app-router: deployment (multi-target)

Verified against Next.js 16.4 docs (getting-started: deploying; guides: deploying-to-platforms, self-hosting, production-checklist, open-telemetry, ci-build-caching; api-reference: adapters, config/cacheHandlers, config/output).

## Choose the target first
Some features require platform capabilities (cache infrastructure, image optimization, ISR persistence) — check "Deploying to Platforms" before promising a feature on a host. Decide: Vercel (zero-config), self-hosted Node, Docker, or static export.

## Vercel
- `vercel deploy` / Git integration; preview deployments per branch; ISR, Cache Components and image optimization work out of the box.
- `npx next upgrade` before each release train; Speed Insights for Web Vitals.

## Self-hosted Node.js
- `next build` → `next start`. Use `output: 'standalone'` to emit a minimal server bundle (`server.js`) with only traced files — copy it, not `node_modules`.
- Multi-instance caching needs a shared `cacheHandlers` config (Redis/Memcached) so `use cache`/ISR revalidation coordinates; in-memory cache alone is per-instance (`cacheMaxMemorySize`).
- Version skew: set `deploymentId` so old tabs stay compatible during rollouts.
- OpenTelemetry instrumentation (`instrumentation.ts`) for server tracing; `instrumentation-client.ts` for RUM.

## Docker
- Multi-stage build on `output: 'standalone'`: install → build → copy `.next/standalone`, `.next/static`, `public/` → run `node server.js`.
- Run as non-root, health-check the server, pass config via env vars (twelve-factor).

## Static export
- `output: 'export'` for static HTML/SPA when no server features are used; upgrading later to a server target is the documented path ("static-exports").

## Adapters (Next 16)
- The adapter API (`adapterPath` / `NEXT_ADAPTER_PATH`, `NextAdapter` interface) lets platforms hook the build; PPR support, output types and cache hooks are documented for platform engineers ("PPR Platform Guide", "Creating an Adapter").

## Before go-live
- Production checklist: build locally (`next build`), exercise ISR/streaming with real data, image/font budgets, security headers + CSP, `x-powered-by` off, env secrets in the platform's secret manager.
- CI: cache `.next` between builds, lint + typecheck + tests as gates (build no longer lints).
- Rollback: keep the previous build/deploy one command away; verify cache behavior after rollback (tags persist in the shared handler).

## Pitfalls
- Standalone image missing `.next/static` or `public/` (blank assets).
- ISR/cache revalidation silently diverging per instance without a shared cache handler.
- Static export of a route that uses cookies/headers or dynamic APIs.
- Assuming host parity: features "work locally, fail on host" usually mean a missing platform capability — check "Deploying to Platforms".
