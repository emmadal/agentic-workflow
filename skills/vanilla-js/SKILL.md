---
name: vanilla-js
description: "Use when building web UI without a framework or jQuery: plain JavaScript, DOM APIs, web components."
---
# Vanilla JavaScript

No framework does not mean old code. Check each API's Baseline status (MDN, webstatus.dev): widely available freely, newly available with feature detection, the rest as progressive enhancement. Pair with `frontend-engineering`. Patterns and legacy map: `references/guide.md`.

## Rules
1. `<script type="module">`, ES modules, import maps; Vite only for TypeScript or bundling. `const`/`let`, `async`/`await`.
2. DOM: `createElement`, `textContent`, `<template>`, `replaceChildren`. Never `innerHTML` with untrusted data; sanitize under Trusted Types.
3. Events: `addEventListener` with an `AbortController` `signal`; delegation; `event.key`.
4. State: a small `EventTarget` store per feature; update only changed nodes; no globals.
5. Components: custom elements with cleanup in `disconnectedCallback`, declarative shadow DOM, `ElementInternals` for form controls.
6. Network: `fetch` with `AbortSignal.timeout()`; check `response.ok`; validate JSON.
7. Platform UI: `<dialog>`, `popover`, invoker commands, `<details name>`, View Transitions, container queries.
8. Routing: real links first; SPA via the Navigation API with feature detection, else History API.
9. TypeScript or JSDoc with `tsc --checkJs`; ESLint.

## Test
Vitest browser mode with `@testing-library/dom`; Playwright E2E; axe.

## Verify
Keyboard and screen reader work, no console errors, budgets met, no legacy API added, tests green.
