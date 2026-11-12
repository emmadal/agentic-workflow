# solidjs: detailed guide

Loaded on demand from SKILL.md. Checked against docs.solidjs.com for Solid 1.9, `@solidjs/router` 1.x and SolidStart 2 (npm `latest` on 2026-11-12; Solid 2.0 was on the `next` tag). Re-check the docs for the versions in `package.json`.

## Reactivity model
- A component function runs once to build DOM; only signal reads inside JSX, memos and effects re-run. Anything read outside a tracking scope is a snapshot.
- Props are reactive getters. `const { name } = props` or `const name = props.name` freezes the value; use `props.name` in JSX or `() => props.name`.
- `mergeProps({ size: 'md' }, props)` for defaults; `splitProps(props, ['class', 'onClick'])` to forward the rest.
- `createMemo` caches derived values used in several places; plain functions are fine for cheap derivations.
- `createEffect(on(source, fn, { defer: true }))` when dependencies must be explicit; `untrack` to read without subscribing; `batch` is rarely needed because updates in event handlers are already batched.

## Stores
```ts
const [state, setState] = createStore({ todos: [] as Todo[] });
setState('todos', (t) => t.id === id, 'done', true);
setState(produce((s) => { s.todos.push(todo); }));
setState('todos', reconcile(serverTodos, { key: 'id' }));
```
- Path syntax updates only the touched leaves; `reconcile` diffs server data into the store without replacing unchanged rows.
- Keep stores in context providers per subtree, not module scope, when rendering on the server.

## Data and routing
```tsx
const getPosts = query(async () => {
  'use server';
  return db.post.findMany();
}, 'posts');

export const route = { preload: () => getPosts() } satisfies RouteDefinition;

export default function Posts() {
  const posts = createAsync(() => getPosts());
  return (
    <ErrorBoundary fallback={(err, reset) => <Retry error={err} onRetry={reset} />}>
      <Suspense fallback={<Skeleton />}>
        <For each={posts()}>{(post) => <PostRow post={post} />}</For>
      </Suspense>
    </ErrorBoundary>
  );
}
```
- `query` deduplicates and caches by key and arguments; `createAsync` reads it and suspends. `createAsyncStore` keeps fine-grained updates for large lists.
- `action(async (form: FormData) => { ... return reload({ revalidate: 'posts' }); }, 'createPost')`; `useSubmission(action)` exposes `pending`, `result`, `error`, `input` for optimistic rows; `useAction` to call it from code.
- Router: file routes in SolidStart (`src/routes`), `<A>` links with active classes, `useParams`, `useSearchParams`, `useNavigate`; nested layouts with `props.children`.

## SolidStart 2
- `vite.config.ts`: `plugins: [solidStart({ middleware: './src/middleware/index.ts' }), nitro()]`, deploy preset under the top-level `nitro` key. No `app.config.ts`.
- Server functions: `"use server"` as the first statement inside the function passed to `query` or `action`, or at the top of a server-only module. Treat every server function as a public endpoint: authenticate, authorize, validate.
- Sessions with `useSession` from `@solidjs/start/http` and a secret from the environment; API routes export `GET`/`POST` handlers from route files.
- Rendering: streaming SSR by default; `deferStream: true` on `createAsync` for data that must be in the first flush (SEO); prerender routes through `nitro.prerender`.

## Testing
- Vitest with `vite-plugin-solid` and `@solidjs/testing-library` (`render(() => <Comp />)`); queries by role and label; `user-event` for interactions.
- Primitives: `createRoot((dispose) => { ...; dispose(); })`. Router-dependent components: render inside a `<Router>` with memory history.
- Playwright E2E for actions, redirects and streaming pages.

## Pitfalls
- Early property reads (`const x = props.x`) that freeze values.
- Effects that write the signals they read.
- Module-level signals or stores shared between SSR requests.
- `"use server"` placed on the wrapper instead of inside the function body, or a server module importing client-only code.
- `createAsync` reads outside `<Suspense>` showing `undefined` without a loading state.

## Legacy to modern (migrate when touched)
| Legacy | Modern |
|---|---|
| destructured props, props copied to locals | `props.x`, `splitProps`, `mergeProps` |
| `createEffect` setting another signal | `createMemo` or a derived function |
| `.map()` in JSX, nested ternaries | `<For>`, `<Index>`, `<Show>`, `<Switch>` |
| `routeData`, `useRouteData`, `createRouteData`, `createServerData$` | `query` + `createAsync`, `route.preload` |
| router `cache()` | `query()` |
| `createRouteAction`, `createServerAction$` | `action()` + `useSubmission` |
| `createResource` for route data | `query` + `createAsync` (keep `createResource` for non-router async) |
| SolidStart 1 `app.config.ts`, Vinxi | `vite.config.ts` with `solidStart()` and `nitro()` |
| `solid-app-router` | `@solidjs/router` |

Follow the SolidStart "Migrating from v1" guide for the config move; migrate one route at a time.
