---
name: frontend-engineering
description: "Use when building or reviewing web UI in React, Preact or any framework: accessible components, state, forms, layout, performance."
---
# Frontend engineering

Read `package.json`. Target npm `latest` stable, never `next` or RC; verify APIs in the installed docs. Load the framework skill: `angular`, `vue`, `svelte`, `solidjs`, `vanilla-js` or `nextjs-app-router`. React and Preact live here; legacy map: `references/frameworks.md`.

1. **Accessibility (WCAG 2.2 AA)**: semantic HTML, ARIA only for gaps, keyboard, visible focus, labels, alt text, 4.5:1 contrast, reduced motion, focus on route change and dialogs.
2. **States**: loading, empty, error, offline, partial data. Keep form input on error.
3. **State**: server state in a data layer (TanStack Query, loaders, resources); UI state local in signals; global only when shared.
4. **Forms**: native `<form>` and constraint validation; server validation is the truth.
5. **Performance**: LCP, INP, CLS budgets; split by route, lazy load, sized images, virtual lists.
6. **Security**: never insert untrusted HTML. CSP, Trusted Types, SameSite cookies, CSRF protection, tokens out of `localStorage`.
7. **Structure**: small components, colocated tests, TypeScript `strict`, Vite, the design system (no generic AI look), responsive from 320px.
8. **Platform first**: `<dialog>`, popover, invoker commands, container queries, `:has()`, View Transitions; check Baseline.
9. **React 19**: function components; Actions (`useActionState`, `useOptimistic`, `<form action>`), `use()`, `ref` as a prop, `<Context>` as provider. The React Compiler memoizes; manual `useMemo` needs profiler proof.
10. **Preact 11**: `preact/hooks`, `@preact/signals`, refs forwarded by default, `@preact/preset-vite`, `preact-iso`; `preact/compat` only for React libraries.

## Test
Testing Library on Vitest (browser mode), Playwright journeys (`browser-testing`), axe in CI.

## Red flags
Legacy APIs (class components, `forwardRef`, NgModules, `*ngIf`, mixins, Vuex, `export let`, `$:`, jQuery) · `div` with `onClick` · uncached fetch in an effect · index keys · a modal library where `<dialog>` works.

## Verify
Keyboard and screen reader work, budgets met, every state handled, no legacy API added, tests green.
