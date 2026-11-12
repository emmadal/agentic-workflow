---
name: frontend-engineering
description: "Use when building or reviewing web UI: components, state, forms, routing, accessibility, responsive layout, rendering performance. Not for native mobile or backend. For Next.js App Router load nextjs-app-router."
---
# Frontend engineering

1. **Accessibility (WCAG 2.2 AA)**: semantic HTML first, ARIA only to fill gaps. Keyboard operable, visible focus, labels on inputs, alt text, 4.5:1 contrast, nothing by color alone, `prefers-reduced-motion`. Manage focus on route change and dialogs.
2. **States**: loading, empty, error, offline and partial data for every view. Preserve form input on error.
3. **State**: server state in a data layer (TanStack Query or framework loaders). UI state local. Global only when truly shared.
4. **Forms**: validate on the client for UX, on the server for truth.
5. **Performance**: budgets for LCP, INP, CLS. Split by route, lazy load below the fold, size and format images, preload critical fonts, virtualize long lists. Memoize only with profiler evidence.
6. **Security**: never insert untrusted HTML; escape or sanitize. CSP, SameSite cookies, CSRF protection. Keep tokens out of `localStorage` where possible.
7. **Structure**: small components with clear props, colocated tests, shared primitives, TypeScript `strict`.
8. Avoid the generic AI look (purple gradients, oversized cards, stock layouts); use the project's design system.
9. Responsive from 320px with no layout shift.
10. **Modern React and platform**: React 19 actions (`useActionState`, `useOptimistic`, form actions) for mutations; the React Compiler handles memoization, so hand-written `useMemo`/`useCallback` need profiler evidence. Use the platform before a library: `<dialog>`, the Popover API, container queries, `:has()`, View Transitions.

## Test
Component tests assert user-visible behavior (Testing Library). Playwright E2E for critical journeys (`browser-testing`). axe in CI. Visual regression for shared components.

## Red flags
`div` with `onClick` · fetch inside `useEffect` with no cancel or cache · index as list key · layout shift from unsized images · spinner as the only error handling · `useMemo` everywhere with the React Compiler on · a modal library where `<dialog>` works.

## Verify
Works by keyboard and screen reader, meets budgets, all states handled, tests green.
