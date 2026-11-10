# nextjs-app-router: rendering, streaming, boundaries

Verified against Next.js 16.4 docs (getting-started: server-and-client-components, linking-and-navigating, error-handling, css, metadata-and-og-images; guides: server-and-client-boundary, streaming, view-transitions, preserving-ui-state, lazy-loading, content-security-policy).

## Server/Client boundary
- RSC-first: server for data, secrets, heavy deps and static shells; client leaves for interactivity. Props crossing the boundary must be serializable.
- The boundary is where server code stops: do not import server-only modules above a `"use client"` file. `server-only` package to hard-mark server modules.
- Composition over reaching client: pass Server Components as `children`/props into client wrappers instead of making the tree client-wide.

## Streaming and Suspense
- `<Suspense>` around slow fetches: shell + `loading.tsx` render first, content streams in. Keep loading states useful (skeletons, not spinners).
- `loading.tsx` per segment gives instant segment-level fallbacks; `error.tsx` (with `reset`) recovers render errors, `global-error.tsx` for the root; `not-found.tsx` + `notFound()` for 404s.
- Route segment structure defines fallback granularity — split segments where load differs.

## Navigation
- `<Link>` with prefetching; App Router prerenders and prefetches statically-reachable content — structure routes so prefetch hits ("instant-navigation", "optimizing-prefetching", "adopting-partial-prefetching").
- Programmatic: `useRouter`/`redirect`; `usePathname`, `useSearchParams`, `useSelectedLayoutSegment(s)`, `useLinkStatus` for pending link state.
- View transitions via `next/link` + View Transitions API (`docs/app/guides/view-transitions`); React `Activity` preserves or resets UI state across navigations ("preserving-ui-state").

## Metadata and assets
- Static `metadata` export or dynamic `generateMetadata`; `generateViewport`; OG images via `opengraph-image` files or `ImageResponse`; `generateSitemaps`, robots and manifest conventions; JSON-LD guide for structured data.
- `next/image` (sized, remote patterns in config), `next/font` (self-hosted, no layout shift), `next/script` with strategy for third-party tags; `@next/third-parties` for GA/Google Maps.

## Styling and CSP
- Tailwind (default in create-next-app), CSS Modules, global CSS; inline CSS option; Sass supported.
- CSP via nonce/headers guide; never render untrusted HTML without sanitization (XSS).

## Lazy loading and performance
- `next/dynamic` / `React.lazy` for below-the-fold and heavy client components; `optimizePackageImports` for barrel files; bundle analyzer for Turbopack.
- Memoize only with profiler evidence (frontend-engineering rule).

## Pitfalls
One giant `"use client"` page; missing `error.tsx` (uncaught render errors white-screen); oversized client bundles from heavy server-capable deps; metadata duplication across layouts; blocking fetch above the fold with no Suspense.
