---
name: solidjs
description: "Use when building SolidJS or SolidStart apps: signals, createAsync, query, actions, fine-grained reactivity."
---
# SolidJS

Read `solid-js`, `@solidjs/router`, `@solidjs/start` in `package.json`; target npm `latest`, never `next`. Use Solid 2 pre-release APIs only if the project already did; never mix 1.x and 2.x. Verify on docs.solidjs.com. Pair with `frontend-engineering`. Legacy map: `references/guide.md`.

## Rules
1. Components run once. Never destructure props or copy them to locals: `props.x`, `splitProps`, `mergeProps`.
2. State: `createSignal`, `createMemo` for derived values, `createStore` for nested data. `createEffect` only for side effects, with `onCleanup`.
3. `<Show>`, `<For>`, `<Index>`, `<Switch>`, `<Dynamic>`, `<Portal>` instead of `.map()` and ternaries.
4. Data: `query(fn, key)` + `createAsync`, preloaded in `route.preload`, inside `<Suspense>` and `<ErrorBoundary>`.
5. Mutations: `action()` on `<form action>`, `useSubmission` for pending state, `reload`/`redirect` with `revalidate` keys.
6. SolidStart 2: `solidStart()` and `nitro()` in `vite.config.ts`; `"use server"` inside the query or action body; validate and authorize every server function.
7. `lazy()` for splitting; typed context hooks; `eslint-plugin-solid`, TypeScript `strict`.

## Test
Vitest with `@solidjs/testing-library`; primitives inside `createRoot`; Playwright E2E.

## Verify
Typecheck, lint, tests green; production build on the target preset; no legacy API added.
