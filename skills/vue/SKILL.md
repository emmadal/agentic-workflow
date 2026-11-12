---
name: vue
description: "Use when building Vue or Nuxt apps: script setup, composables, Pinia, Vue Router, SSR."
---
# Vue

Read `vue`, `vue-router`, `pinia`, `nuxt` in `package.json`; target npm `latest`, never `beta`, `rc` or Vapor previews. Verify APIs on vuejs.org. Pair with `frontend-engineering`. Legacy map: `references/guide.md`.

## Rules
1. `<script setup lang="ts">` and the Composition API. No Options API or mixins in new code.
2. Props: `defineProps<{...}>()` with reactive destructure and defaults (no `withDefaults`); `defineModel()` for `v-model`; typed `defineEmits`.
3. Reactivity: `ref`, `computed`, `shallowRef` for big data. Never destructure `reactive()`. `watch` for side effects only, with `onWatcherCleanup`.
4. `useTemplateRef()` for DOM, `useId()` for ids.
5. Reuse in composables; shared state in Pinia setup stores read with `storeToRefs`.
6. Server state: Pinia Colada or TanStack Vue Query; Nuxt `useFetch`/`useAsyncData` with explicit keys.
7. Routing: Vue Router file-based typed routes (`vue-router/vite`), lazy pages.
8. Templates: stable `:key` on `v-for`, no `v-if` beside `v-for`, `v-html` only sanitized.
9. SSR with Nuxt (`app/`, `server/`); lazy hydration via `defineAsyncComponent({ hydrate })`. Vite, `vue-tsc`, `eslint-plugin-vue`.

## Test
Vitest with `@vue/test-utils` or `@testing-library/vue`; composables as plain functions; Playwright E2E.

## Verify
`vue-tsc` and lint clean, tests green, no hydration mismatch, no legacy API added.
