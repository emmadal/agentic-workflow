# svelte: detailed guide

Loaded on demand from SKILL.md. Checked against svelte.dev for Svelte 5.57 and SvelteKit 3.2 (npm `latest` on 2026-11-12). SvelteKit 3 needs Node 22.17+, TypeScript 6, Vite 8 and `@sveltejs/vite-plugin-svelte` 7. Re-check the docs for the versions in `package.json`.

## Component shape
```svelte
<script lang="ts">
  import type { Snippet } from 'svelte';
  let { items, selected = $bindable(), onselect, row }: {
    items: Item[]; selected?: Item; onselect?: (item: Item) => void; row: Snippet<[Item]>;
  } = $props();
  let query = $state('');
  const visible = $derived(items.filter((i) => i.name.includes(query)));
</script>

<input bind:value={query} aria-label="Filter" />
<ul>
  {#each visible as item (item.id)}
    <li><button onclick={() => { selected = item; onselect?.(item); }}>{@render row(item)}</button></li>
  {:else}
    <li>No results</li>
  {/each}
</ul>
```
- Key every `{#each}` with a stable id.
- `$state` objects and arrays are deeply reactive proxies; use `$state.raw` for big data you replace rather than mutate, and `$state.snapshot` before passing to non-Svelte code.
- `$derived` values are writable for optimistic UI and recompute when dependencies change.
- `$inspect` for debugging only; remove before commit.

## Shared state
```ts
// cart.svelte.ts
export class Cart {
  items = $state<Line[]>([]);
  total = $derived(this.items.reduce((s, l) => s + l.price * l.qty, 0));
  add(line: Line) { this.items.push(line); }
}
```
- Export an object or class instance, not a reassigned `let`, so importers keep reactivity.
- On the server, module state is shared across requests: keep per-user state in context set in a layout, never in module scope.
- Stores (`svelte/store`) remain valid for real streams and interop; do not use them for local or shared component state.

## SvelteKit
- Routes: `+page.svelte`, `+layout.svelte`, `+page.ts`, `+page.server.ts`, `+server.ts`, `+error.svelte`; groups `(name)`, params `[id]`, matchers.
- `load` runs in parallel; return promises for non-critical data to stream them. `depends()` plus `invalidate()` or `refreshAll()` to rerun.
- Form actions in `+page.server.ts`: validate `FormData`, return `fail(400, { errors })` and render them; `redirect(303, ...)` after success. `use:enhance` keeps the native form working without JavaScript.
- Remote functions (`query`, `form`, `command`, `prerender` in `*.remote.ts`) are experimental: opt in with `experimental.remoteFunctions` and `compilerOptions.experimental.async` in `sveltekit({...})`, validate arguments with a Standard Schema, and keep them out of prerendered pages unless they use `prerender`.
- `hooks.server.ts` `handle` for auth and headers; `event.locals` for per-request user; CSRF protection is always on, allow other origins with `csrf.trustedOrigins`.
- Env: `$env/static/private` and `$env/dynamic/private` only in server files; anything in `$env/*/public` is shipped to the browser.
- Images: `@sveltejs/enhanced-img`. Links: `resolve('/blog/[slug]', { slug })` for type-checked paths.

## Testing
- Vitest with `@testing-library/svelte` and `@testing-library/user-event`; jsdom or browser mode (`@vitest/browser-playwright`). Test `.svelte.ts` logic directly from `*.svelte.test.ts` files (runes only compile there); wrap code that creates effects in `$effect.root` and clean it up.
- `svelte-check --tsconfig ./tsconfig.json` in CI. Playwright for E2E; test forms with JavaScript disabled once.

## Pitfalls
- Reassigning an exported `$state` primitive from a module (importers do not update); export an object or class.
- Destructuring a `$state` object into locals and losing reactivity.
- Secrets imported into universal `load` or client code.
- `$effect` that writes state it reads (infinite loop).
- `await` in markup or `*.remote.ts` files without the experimental flags enabled.

## Legacy to modern (migrate when touched)
| Legacy | Modern | Migration |
|---|---|---|
| `export let` | `$props()` | `npx sv migrate svelte-5` |
| `$:` statements | `$derived`, `$effect` | same; replace any `run()` from `svelte/legacy` |
| `on:click`, `\|preventDefault` | `onclick`, `event.preventDefault()` | same |
| `createEventDispatcher` | callback props | same |
| `<slot>`, `let:` | snippets, `{@render}` | same |
| `<svelte:component this>` | `<Comp />` with a dynamic variable | same |
| `use:action` for new DOM behavior | `{@attach}` | manual |
| `beforeUpdate`, `afterUpdate` | `$effect.pre`, `$effect` | manual |
| `new Component({ target })` | `mount()` | manual |
| `<script context="module">` | `<script module>` | manual |
| `$app/stores`, `$page` | `$app/state`, `page` | `npx sv migrate app-state` |
| `svelte.config.js` options, `$lib` | `sveltekit({...})` in `vite.config.js`, `#lib/x.js` | `npx sv migrate sveltekit-3` |
| `base`, `assets`, `resolveRoute` | `resolve()`, `asset()` | same |
| `pushState`, `replaceState` | `goto(url, { shallow: true, state })` | same |
| `invalidateAll` | `refreshAll` | same |
| `csrf.checkOrigin: false` | `csrf.trustedOrigins` | same |

Upgrade SvelteKit 2 projects to the last 2.x first to see deprecation warnings, then run the migration on a clean branch.
