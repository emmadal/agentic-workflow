# Frameworks: modern APIs versus legacy

Loaded on demand from SKILL.md. "Legacy" means: never in new code; when you touch a file that uses it, migrate it with the framework's official migration (schematic, codemod, `sv migrate`) in its own commit. Versions move: read `package.json`, check `npm view <pkg> dist-tags` for the current `latest`, and confirm in the official docs before relying on any API below. Never adopt `next`, beta or RC tags unless the project already did.

## React 19
- Use: function components and hooks; Actions (`<form action>`, `useActionState`, `useFormStatus`, `useOptimistic`, `startTransition` with async functions); `use()` for promises and context; `ref` as a plain prop and ref cleanup functions; `<Context value>` as provider; `<title>`, `<meta>`, `<link>` rendered in components (hoisted); `<Activity>` for hidden-but-kept UI; `useEffectEvent` for non-reactive logic in effects; `createRoot`/`hydrateRoot`; the React Compiler.
- Server Components and Server Functions come through a framework (`nextjs-app-router`), not hand-rolled.
- Legacy: class components and lifecycle methods; `forwardRef`; `defaultProps` and `propTypes` on function components; string refs; legacy context (`contextTypes`); `ReactDOM.render`/`hydrate`; `react-dom/test-utils`; `<Context.Provider>`; HOCs and render props for logic reuse (use custom hooks); Create React App; Enzyme; blanket `memo`/`useMemo`/`useCallback`.
- Data: TanStack Query or framework loaders. Routing: the framework's router, React Router or TanStack Router.
- Test: Vitest, React Testing Library, `user-event`; `act` from `react`.

## Preact 11
- Use: hooks from `preact/hooks`; `@preact/signals` (`signal`, `computed`, `effect`, `useSignal`, `useComputed`), passing a signal straight into JSX so only that text node updates; refs forwarded by default; `useRef(initial)`; Hydration 2.0 with streamed SSR (`preact-render-to-string`); `preact-iso` (`LocationProvider`, `Router`, `lazy`, `prerender`); Vite with `@preact/preset-vite`; `npm create preact`.
- `preact/compat` only to run React libraries; alias `react` and `react-dom` to it in Vite, never import it in app code for features core has.
- Legacy: class components in new code; `forwardRef`; `defaultProps`, automatic `px` suffixing and `SuspenseList` (now compat-only); `render()` with a `replaceNode` argument; `Component.base`; `useRef()` with no initial value; `preact-router` (use `preact-iso`); `preact-cli`; Preact 8 and 10 APIs removed by the v11 upgrade guide.
- Test: Vitest and `@testing-library/preact`.

## Angular (load `angular`)
- Use: standalone components, signals (`signal`, `computed`, `linkedSignal`, `effect`), `input()`, `output()`, `model()`, signal queries (`viewChild()`), `inject()`, built-in control flow (`@if`, `@for` with `track`, `@switch`, `@let`), `@defer`, zoneless and OnPush (both default), `resource`/`httpResource`, Signal Forms, `host` metadata, functional guards and interceptors, Vitest.
- Legacy: NgModules, `*ngIf`/`*ngFor`/`*ngSwitch`, `@Input`/`@Output`/`@ViewChild` decorators, constructor injection, `@HostBinding`/`@HostListener`, zone.js, `ChangeDetectionStrategy.Eager` without a reason, class-based guards, `HttpClientModule`, Karma, Jasmine, Protractor, `.component.ts` file suffixes in new files.

## Vue (load `vue`)
- Use: `<script setup lang="ts">` with the Composition API, reactive props destructure, `defineModel`, `useTemplateRef`, `useId`, composables, Pinia setup stores, Vue Router file-based typed routes (`vue-router/vite`), Vite, Vitest, Nuxt for SSR.
- Legacy: Vue 2, the Options API and mixins in new code, Vuex, filters, event buses (`$on`), `Vue.extend`, `this.$refs`, `withDefaults` where destructure defaults work, Vue CLI and webpack, `unplugin-vue-router` imports.

## Svelte (load `svelte`)
- Use: runes (`$state`, `$derived`, `$effect`, `$props`, `$bindable`), event attributes (`onclick`), callback props, snippets and `{@render}`, `{@attach}`, `.svelte.ts` modules for shared state, `mount()`, SvelteKit `load` and form actions, `$app/state`, `#lib`.
- Legacy: `export let`, `$:`, `on:click` and event modifiers, `createEventDispatcher`, slots, `<svelte:component>`, `beforeUpdate`/`afterUpdate`, `new Component()`, `svelte/legacy`, `$app/stores`, `$lib`, `svelte.config.js` for SvelteKit 3 options, `context="module"`.

## Solid (load `solidjs`)
- Use: `createSignal`, `createMemo`, `createStore`, `splitProps`/`mergeProps`, `<Show>`, `<For>`, `<Switch>`, `<Suspense>`, `<ErrorBoundary>`, router `query` + `createAsync` + `action`, SolidStart 2 with `solidStart()` in `vite.config.ts`.
- Legacy: destructuring props, `createEffect` to derive state, `.map()` in JSX for lists, `routeData`/`useRouteData`, router `cache` (renamed `query`), SolidStart 1 `app.config.ts` and Vinxi, Solid 2 RC APIs in a 1.x project.

## No framework (load `vanilla-js`)
- Use: ES modules, `<script type="module">`, import maps, custom elements, declarative shadow DOM, `AbortController` for listener cleanup, `fetch` with `AbortSignal.timeout`, `<dialog>`, popover, invoker commands, `structuredClone`, `Intl`.
- Legacy: jQuery, `var`, `XMLHttpRequest`, `document.write`, inline `on*` attributes, `innerHTML` with untrusted data, global scripts and IIFE bundles, `keyCode`, user-agent sniffing, polyfills for Baseline features, Moment.js.
