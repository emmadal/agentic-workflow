---
name: svelte
description: "Use when building Svelte 5 or SvelteKit apps: runes, snippets, load, form actions."
---
# Svelte

Read `svelte` and `@sveltejs/kit` in `package.json`; target npm `latest`, never `next`. Verify APIs on svelte.dev. Pair with `frontend-engineering`. Migrate legacy code you touch with `npx sv migrate` (`references/guide.md`).

## Rules
1. Runes only: `$state` (`$state.raw` for big data), `$derived`, `$props()` with defaults, `$bindable()`.
2. `$effect` only to sync with the outside world, with cleanup; never to derive state.
3. Events as attributes (`onclick`), callback props instead of `createEventDispatcher`, no event modifiers.
4. Snippets and `{@render}` instead of slots; `{@attach}` for DOM behavior; `mount()` instead of `new Component()`.
5. Shared state in `.svelte.ts` modules exporting objects or classes; per-request state in context, never module scope on the server.
6. SvelteKit data: server `load` for private data, universal `load` for public APIs. Mutations: form actions with `use:enhance`, then `refreshAll()`. Remote functions only if `experimental.remoteFunctions` is on.
7. SvelteKit 3: options in `sveltekit({...})` in `vite.config.js`, `#lib/x.js`, `$app/state`, `resolve()`/`asset()`, `goto(url, { shallow: true })`.
8. Per-route `prerender`, `ssr`, `csr`; adapter for the target.

## Test
Vitest with `@testing-library/svelte`; rune logic in `*.svelte.test.ts`; Playwright E2E.

## Verify
`svelte-check`, lint, tests green; build on the target adapter; forms work without JavaScript; no legacy API added.
