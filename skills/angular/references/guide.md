# angular: detailed guide

Loaded on demand from SKILL.md. Checked against angular.dev for Angular 22 (npm `latest` on 2026-11-12). Re-check the docs for the version in `package.json` before relying on an API; each major runs `ng update @angular/core @angular/cli` and its automatic migrations.

## Project setup
- New app: `ng new` (zoneless, OnPush by default, Vitest, 2025 style guide, standalone). Add SSR with `ng add @angular/ssr` or `ng new --ssr`.
- `bootstrapApplication(App, appConfig)` with an `ApplicationConfig` providers array: `provideRouter(routes, withComponentInputBinding())`, `provideHttpClient(withFetch(), withInterceptors([...]))`, `provideClientHydration()` for SSR, `provideAppInitializer()` for startup work.
- Strict TypeScript and `strictTemplates`. ESLint with `angular-eslint`.

## Components
```ts
@Component({
  selector: 'app-user-card',
  templateUrl: 'user-card.html',
  host: { class: 'card', '(keydown.escape)': 'close.emit()' },
})
export class UserCard {
  readonly user = input.required<User>();
  readonly selected = model(false);
  readonly close = output<void>();
  readonly initials = computed(() => this.user().name.slice(0, 2));
  private readonly api = inject(UserApi);
}
```
- Keep components presentational where possible; put data access in injectable services with `providedIn: 'root'`.
- `linkedSignal(() => source())` for writable state that resets when a source changes (selected item reset on list change).
- `effect` runs after render; use `afterRenderEffect` for DOM measurement. Never write a signal that the same effect reads.
- `@defer` blocks with `@placeholder`, `@loading`, `@error`; triggers `on viewport`, `on idle`, `on interaction`, `when cond`; prefetch with `prefetch on idle`.

## Data
- `httpResource(() => \`/api/users/${id()}\`)` re-fetches when `id` changes and cancels the previous request; it exposes `value`, `status`, `error`, `isLoading`, `hasValue()`, `reload()`. Add a `parse` function (Zod or Standard Schema) to validate responses.
- `resource({ params, loader })` for non-HTTP async work; `rxResource` from `@angular/core/rxjs-interop` when the loader is an Observable.
- Mutations: call `HttpClient` from a service, then `reload()` the affected resource or update it with `set`/`update`.
- Global state: a service holding private signals and exposing `asReadonly()` and `computed` views. Add NgRx SignalStore only when many features share complex state.

## Forms
- Signal Forms from `@angular/forms/signals`: a `signal` model, `form(model, schema => { required(schema.email); email(schema.email); })`, `[formField]="f.email"` in the template, `submit(f, { action })` for async submit with server errors mapped back to fields.
- Custom controls implement the Signal Forms control interface (`value` model plus `invalid`/`errors` inputs) instead of `ControlValueAccessor`.
- Existing reactive forms interoperate during migration; do not start new reactive or template-driven forms.

## SSR and hydration
- Route-level render mode in `app.routes.server.ts`: `RenderMode.Prerender` for static pages, `RenderMode.Server` for per-request, `RenderMode.Client` for app-only areas.
- `provideClientHydration()` enables incremental hydration and event replay; use `@defer (hydrate on viewport)` to hydrate heavy blocks lazily. Opt out with `withNoIncrementalHydration()` only with a reason.
- No direct `window`/`document` in code that runs on the server; use `inject(DOCUMENT)`, `afterNextRender`, or platform checks.

## Testing
- `ng test` runs Vitest through `@angular/build:unit-test`; `ng test --coverage`; browser mode with `@vitest/browser-playwright`.
- TestBed is zoneless by default. Create the component, set inputs with `fixture.componentRef.setInput()`, then `await fixture.whenStable()`. Avoid forcing `detectChanges()`.
- Mock HTTP with `provideHttpClientTesting()` and `HttpTestingController`. Prefer component harnesses (CDK, Material) or Testing Library queries by role and label.
- E2E with Playwright (`browser-testing`).

## Pitfalls
- Writing signals inside `computed`, or an `effect` that copies one signal into another (use `computed` or `linkedSignal`).
- Reading `resource.value()` in the error state (it throws); check `hasValue()` first.
- `@for` tracking `$index` on lists that reorder; track a stable id.
- Subscriptions without `takeUntilDestroyed` or `toSignal`.
- Zone-dependent third-party libraries in a zoneless app without a test proving they still update the view.
- `window` or `document` touched during SSR.

## Legacy to modern (migrate when touched)
| Legacy | Modern | Migration |
|---|---|---|
| NgModules, `standalone: false` | standalone components | `ng g @angular/core:standalone` |
| `*ngIf`, `*ngFor`, `*ngSwitch` | `@if`, `@for`, `@switch` | `ng g @angular/core:control-flow` |
| `@Input()` | `input()` | `ng g @angular/core:signal-input-migration` |
| `@Output()` + `EventEmitter` | `output()` | `ng g @angular/core:output-migration` |
| `@ViewChild`, `@ContentChildren` | `viewChild()`, `contentChildren()` | `ng g @angular/core:signal-queries-migration` |
| constructor injection | `inject()` | `ng g @angular/core:inject` |
| `ngClass` | class bindings | `ng g @angular/core:ngclass-to-class` |
| `@HostBinding`, `@HostListener` | `host` metadata | manual |
| zone.js, `provideZoneChangeDetection` | zoneless (default) | remove `zone.js` from `polyfills` |
| `ChangeDetectionStrategy.Default` | OnPush (default since v22), `Eager` (its new name) only with a reason | manual |
| class guards and resolvers, `HttpClientModule` | functional guards, `provideHttpClient()` | manual |
| reactive and template-driven forms | Signal Forms | migrate per form |
| `APP_INITIALIZER` | `provideAppInitializer()` | manual |
| `withIncrementalHydration()`, `withEventReplay()` | defaults of `provideClientHydration()` | remove |
| Karma, Jasmine, Protractor | Vitest, Playwright | `ng g @schematics/angular:refactor-jasmine-vitest` (experimental; review output) |

Run each schematic on a clean branch, build, test, and commit it separately from feature work.
