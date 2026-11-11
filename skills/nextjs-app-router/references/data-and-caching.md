# nextjs-app-router: data fetching, mutations, caching

Verified against Next.js 16.4 docs (getting-started: fetching-data, mutating-data, caching, revalidating; guides: server-actions, how-revalidation-works, isr, caching-without-cache-components).

## Fetching in Server Components
- Default: fetch in RSC with the built-in `fetch`; pass data down to client components as serializable props.
- Client-side data (SWR or TanStack Query) for interactive views; optionally seed with initial data from a Server Component.
- Client Components never hold server secrets; validate at the boundary.

## Two caching models — know which one is on
- **Cache Components (current default in create-next-app):** caching is explicit per component/function. Use the `use cache` directive, `cacheLife('...')` profiles for expiry, `cacheTag('tag')` for invalidation groups. `use cache: private` caches request-scoped data (session-derived UI); `use cache: remote` persists to a shared cache handler across instances. Runtime request APIs (`cookies`, `headers`) make code dynamic — keep them out of cached scopes or use `use cache: private`.
- **Legacy model (no Cache Components):** `fetch` options (`cache: 'force-cache'`, `next: { revalidate, tags }`), `unstable_cache`, route segment configs (`revalidate`, `dynamic`). See guide "Caching (Previous Model)".
- Never assume semantics: check `package.json` + `next.config` for `cacheComponents` before writing cache code.

## Revalidation
- Tag-based: `cacheTag('post-123')` when caching, `revalidateTag('post-123')` or `updateTag` after mutations; `revalidatePath` for whole segments.
- Time-based: `cacheLife` profiles or `revalidate` seconds (ISR). On-demand wins over timers for user-triggered writes.
- Multi-instance deployments coordinate through a shared cache handler (`cacheHandlers` config: Redis/Memcached backends).

## Mutations: Server Functions and Actions
- `"use server"` functions run only on the server; call from forms (`<form action={...}>`), Server Actions, or transitions.
- The single-roundtrip response model + sequential dispatch; use optimistic UI and `useTransition`/`useActionState` for pending feedback (`docs/app/guides/interactive-apps`, `docs/app/guides/forms`).
- Validate every input server-side (never trust client validation); typed error returns; `redirect`/`notFound` for control flow.
- After a successful write, revalidate the affected tags — a mutation that leaves stale cache is a bug.
- Security: actions are public endpoints; authz-check inside the action, close over validated arguments, respect the data-security guide.

## ISR and static/dynamic split
- ISR: prerender + background refresh (`docs/app/guides/incremental-static-regeneration`); with Cache Components, prerender a subset of dynamic routes and serve App Shells for the rest.
- Keep pages static where possible ("keeping pages static", "public-static-pages"); dynamic only where the request truly demands it.
- `generateStaticParams` for static param paths; `dynamicParams` controls unknown-param behavior.

## Route Handlers
- `route.ts` for Web-standard request handling (REST, webhooks, BFF pattern); stream responses; cookies/headers from `next/headers`.
- Route Handlers are not the default for rendering — prefer Server Components; use handlers when an HTTP contract is needed.

## Pitfalls
Mixing the two caching models mid-project; mutating without tag revalidation; secrets passed as props to client components; slow fetch without Suspense blocking the whole route; treating Server Actions as private functions.
