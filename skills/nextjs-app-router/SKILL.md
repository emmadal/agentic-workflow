---
name: nextjs-app-router
description: "Use when building Next.js App Router applications (Next 16, server components, server actions, cache components, use cache): layouts, data fetching, streaming, metadata, forms, performance, testing, through to Vercel or self-hosted deployment."
---
# Next.js App Router

Read `next` in `package.json` (16.x: Turbopack default bundler, Node 20.9+, React canary built into the App Router). Docs: every nextjs.org/docs page serves Markdown; the installed version's docs ship in `node_modules/next/dist/docs/` — verify APIs there, not from training data. Pair with `frontend-engineering`.

## Rules
1. Server Components by default. Add `"use client"` only at leaves that need state, effects or browser APIs; pass serializable props down. Fetch data in Server Components.
2. Routing: `app/`, `layout.tsx`, `page.tsx`, route groups `(name)`, dynamic `[id]`, `loading.tsx`, `error.tsx`, `not-found.tsx`, parallel and intercepting routes. `proxy.ts` (ex-middleware) for rewrites, redirects and headers before a request completes.
3. Mutations through Server Functions (`"use server"`) called from forms or transitions; validate input server-side; call `revalidateTag`/`revalidatePath` after writes.
4. Caching: prefer Cache Components (`cacheComponents`) with `use cache`, `cacheLife` profiles and `cacheTag` invalidation; `use cache: private` for request-scoped data, `use cache: remote` plus cache handlers for multi-instance. Without it: fetch options and `unstable_cache` (`references/data-and-caching.md`).
5. `params` and `searchParams` are async — `await` them. Wrap slow fetches in Suspense so the shell streams first.
6. Metadata: `generateMetadata`, `opengraph-image`, sitemap/robots conventions. `next/image`, `next/font`, `next/script` for assets.
7. Route Handlers (`route.ts`) use Web Request/Response APIs. Route segment config for `runtime` and `maxDuration`.
8. `next build` no longer lints — wire ESLint (or Biome) into scripts and CI. Test with Vitest (units) and Playwright (E2E).
9. Upgrade with `npx next upgrade`; upgrade the app alongside the docs, never against stale memory.

## Test
Production build clean, typecheck and lint green, unit + E2E for critical journeys, dynamic routes and error/loading states exercised.

## Pitfalls
Fetching in `useEffect` instead of a Server Component; `"use client"` at the top of the tree; assuming fetch caching semantics without checking the active caching model; heavy sync work in `proxy.ts`; mutations without tag revalidation; stale cached pages after upgrading Next without re-reading the docs.

## Verify
Production build runs on the actual target (Vercel or self-hosted), streaming and revalidation behave under real data, Core Web Vitals budgets met. Depth: `references/guide.md`, `data-and-caching.md`, `rendering.md`, `deployment.md`.
