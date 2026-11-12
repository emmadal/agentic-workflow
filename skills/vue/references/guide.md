# vue: detailed guide

Loaded on demand from SKILL.md. Checked against the official docs for Vue 3.5, Vue Router 5, Pinia and Nuxt 4 (npm `latest` on 2026-11-12). Vue 3.6 and Vapor mode were still release candidates then: do not adopt them unless the project already has. Re-check the docs for the versions in `package.json`.

## Component shape
```vue
<script setup lang="ts">
const { title, count = 0 } = defineProps<{ title: string; count?: number }>()
const open = defineModel<boolean>('open', { default: false })
const emit = defineEmits<{ save: [id: string] }>()
const dialog = useTemplateRef<HTMLDialogElement>('dialog')
const id = useId()
const doubled = computed(() => count * 2)
</script>

<template>
  <dialog ref="dialog" :aria-labelledby="id" @close="open = false">
    <h2 :id="id">{{ title }}</h2>
  </dialog>
</template>
```
- Destructured props stay reactive in `<script setup>`; to watch one, pass a getter: `watch(() => count, ...)`.
- `defineModel` replaces the `modelValue` prop plus `update:modelValue` emit pair; modifiers via `const [model, modifiers] = defineModel()`.
- Keep components small; extract logic into composables in `composables/useX.ts`.

## Reactivity
- `ref()` everywhere for consistency; `reactive()` only for objects you never destructure or replace.
- `computed` must be pure; use a writable computed only for real two-way derivations.
- `watch`/`watchEffect` for side effects only. Register cleanup with `onWatcherCleanup(() => controller.abort())`. Use `{ once: true }` for one-shot watchers and a numeric `deep` to limit depth.
- `shallowRef` plus `triggerRef` for large lists or third-party instances.
- `provide`/`inject` with typed `InjectionKey` for subtree dependencies.

## State and data
- Pinia setup stores: `defineStore('cart', () => { const items = ref([]); const total = computed(...); function add() {} return { items, total, add } })`. Read with `storeToRefs(store)` for state and getters; call actions directly.
- Server state does not belong in Pinia: use Pinia Colada (`useQuery`, `useMutation`, cache keys, invalidation) or TanStack Vue Query.
- Validate API responses at the boundary (Zod or Valibot).

## Routing
- Vue Router 5 ships file-based routing: `import VueRouter from 'vue-router/vite'`, placed before `vue()` in `plugins`, pages in `src/pages`, generated types in `src/route-map.d.ts`.
- Navigation guards as functions; `definePage()` for route meta in a page; lazy loading is the default import mode.
- Focus the main heading or `<main>` after navigation for screen readers.

## Nuxt 4
- App code lives in `app/`; server code in `server/` (Nitro); shared types and utils in `shared/`.
- `useFetch(url, { key })` or `useAsyncData(key, handler)` for SSR-safe data; `$fetch` in event handlers and server code. Same key means one request shared by components.
- `useState` for SSR-safe shared state, `definePageMeta` for layout and middleware, `useHead`/`useSeoMeta` for metadata, route rules for prerender, ISR and SWR per path.
- `<ClientOnly>` only for widgets that cannot render on the server.

## Testing
- Vitest with `@vue/test-utils` `mount` or `@testing-library/vue` `render`; query by role and label; `await` DOM updates with `flushPromises` or `nextTick`.
- Test composables by calling them inside a test component or `withSetup` helper; mock network with MSW.
- Nuxt: `@nuxt/test-utils` with the Nuxt Vitest environment. E2E with Playwright.

## Pitfalls
- Destructuring a Pinia store without `storeToRefs` (loses reactivity).
- Mutating a prop instead of emitting or using `defineModel`.
- Deep watchers on large objects; prefer a getter or numeric `deep`.
- Reading `window` during SSR; dates or random values causing hydration mismatches.
- Two `useFetch` calls for the same data without a shared `key` (two requests).

## Legacy to modern (migrate when touched)
| Legacy | Modern |
|---|---|
| Vue 2, Nuxt 2, Nuxt Bridge | Vue 3.5, Nuxt 4 |
| Options API, mixins, `vue-class-component`, `vue-property-decorator` | `<script setup>`, composables |
| Vuex | Pinia setup stores |
| `this.$refs`, string `ref` plus `ref(null)` lookups | `useTemplateRef()` |
| `withDefaults(defineProps())` | destructure with defaults |
| `modelValue` prop plus `update:modelValue` emit | `defineModel()` |
| filters, `$on`/`$off` event bus, `Vue.set`, `.sync`, `$listeners` | computed or functions, props and emits, `v-model:arg`, `$attrs` |
| `unplugin-vue-router` imports | `vue-router/vite`, `vue-router/unplugin` |
| Vue CLI, webpack, `vue-jest`, Jest | Vite, Vitest |
| hand-rolled fetch in `onMounted` | Pinia Colada, TanStack Vue Query or Nuxt `useFetch` |

Migrate one component or store per commit, with its tests passing before and after.
