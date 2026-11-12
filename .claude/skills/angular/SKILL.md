---
name: angular
description: "Use when building Angular apps: signals, zoneless, Signal Forms, httpResource, SSR."
---
# Angular

Read `@angular/core` in `package.json`; target npm `latest`, `ng update` one major at a time, never `next`. Verify APIs on angular.dev. Pair with `frontend-engineering`. Migrate legacy code you touch with the schematics in `references/guide.md`.

## Rules
1. Standalone components, no NgModules. `inject()`, not constructor injection. File names without `.component`.
2. State: `signal`, `computed`, `linkedSignal`. `effect` only to sync with non-signal APIs, never to derive state.
3. Component API: `input()`, `output()`, `model()`, `viewChild()`; `host: {}` instead of `@HostBinding`/`@HostListener`.
4. Templates: `@if`, `@for` with `track`, `@switch`, `@let`, `@defer`; class bindings, not `ngClass`; `NgOptimizedImage`.
5. Keep the defaults: zoneless and OnPush. No `zone.js`, no `ChangeDetectionStrategy.Eager` without a measured reason.
6. Reads: `httpResource`/`resource`, guarded by `hasValue()`. Writes: `HttpClient` with `withFetch()`. RxJS only for streams, via `toSignal`.
7. Forms: Signal Forms (`form()`, `[formField]`, `submit()`); reactive forms only in code being migrated.
8. Routing: lazy `loadComponent`, functional guards, `withComponentInputBinding()`. SSR: `@angular/ssr`, route render modes, `provideClientHydration()` (incremental hydration and event replay on).

## Test
`ng test` on Vitest; zoneless TestBed with `await fixture.whenStable()`; harnesses or Testing Library; Playwright E2E.

## Verify
`ng build` within budgets, lint and tests green, SSR hydrates cleanly, no legacy API added.
