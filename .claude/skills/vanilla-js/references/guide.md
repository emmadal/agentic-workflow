# vanilla-js: detailed guide

Loaded on demand from SKILL.md. Baseline statuses below come from the `web-features` dataset on 2026-11-12; they change, so re-check on MDN or webstatus.dev before relying on one.

## Baseline snapshot (2026-11-12)
- Widely available: `<dialog>`, custom elements and shadow DOM, declarative shadow DOM, form-associated custom elements, import maps, `modulepreload`, container queries, `:has()`, CSS nesting, `structuredClone`, `AbortSignal.timeout()`, `AbortSignal.any()`, `Promise.withResolvers()`, `Array.fromAsync()`, `loading="lazy"`, compression streams.
- Newly available (feature-detect or accept that a few recent browsers lack them): Popover API, invoker commands, Navigation API, `URLPattern`, same-document View Transitions, Trusted Types, iterator helpers, Set methods, `@starting-style`, `field-sizing`, `<details name>`, `fetchpriority`, `content-visibility`, scroll-driven animations, scoped custom element registries, JSON modules.
- Not Baseline (progressive enhancement only): Sanitizer API `setHTML()`, cross-document View Transitions, CSS anchor positioning, customizable `<select>`, `dialog closedby`, Temporal, `requestIdleCallback`, `scheduler.yield()`.

## Structure
```html
<script type="importmap">{ "imports": { "lit-html": "/vendor/lit-html.js" } }</script>
<script type="module" src="/src/main.js"></script>
```
- One module per feature: `state.js` (store), `view.js` (render), `main.js` (wiring). No globals; export functions.
- Without a build step, serve modules with long-cache hashed names or `modulepreload` the critical graph. With Vite, keep the same module layout.

## State and rendering
```js
export class Store extends EventTarget {
  #state;
  constructor(initial) { super(); this.#state = initial; }
  get state() { return this.#state; }
  update(fn) {
    this.#state = fn(structuredClone(this.#state));
    this.dispatchEvent(new CustomEvent('change', { detail: this.#state }));
  }
}
```
- Render by keyed diff: keep a `Map` from id to element, update text and attributes in place, insert or remove only changed rows. For large templated views, a tiny library such as `lit-html` is acceptable; do not hand-roll a virtual DOM.
- Keep focus: after replacing content, move focus to the new heading or the element that triggered the change.

## Events and cleanup
```js
const controller = new AbortController();
list.addEventListener('click', (e) => {
  const button = e.target.closest('button[data-id]');
  if (button) remove(button.dataset.id);
}, { signal: controller.signal });
// later: controller.abort() removes every listener registered with this signal
```

## Web components
```js
class UserCard extends HTMLElement {
  #controller;
  connectedCallback() {
    this.#controller = new AbortController();
    this.addEventListener('click', this.#onClick, { signal: this.#controller.signal });
    this.render();
  }
  disconnectedCallback() { this.#controller.abort(); }
  static observedAttributes = ['name'];
  attributeChangedCallback() { this.render(); }
  #onClick = () => this.dispatchEvent(new CustomEvent('select', { bubbles: true, composed: true }));
  render() { this.textContent = this.getAttribute('name') ?? ''; }
}
customElements.define('user-card', UserCard);
```
- Attributes for configuration, properties for rich data, events out. Name with a hyphen and a project prefix.
- Form controls: `static formAssociated = true` and `this.attachInternals()` for value, validity and labels.
- Server-rendered components: `<template shadowrootmode="open">` so content shows before JavaScript.

## Security
- Untrusted text goes through `textContent` or attribute setters. Build URLs with `new URL()` and allow only `http:`/`https:` before assigning `href`.
- CSP with `script-src 'self'` and no `unsafe-inline`: no inline `on*` attributes or inline scripts. Add `require-trusted-types-for 'script'` and a single sanitizing policy where Trusted Types is supported.
- `localStorage` only for non-sensitive preferences; tokens in `HttpOnly` cookies.

## Testing
- Vitest browser mode (`@vitest/browser-playwright`) or jsdom for pure DOM logic; `@testing-library/dom` queries by role and label.
- Test custom elements by creating them in the document and asserting rendered output and dispatched events.
- Playwright E2E plus axe; run one pass with a throttled CPU and network.

## Pitfalls
- Listeners never removed when elements or components go away.
- Re-rendering a whole list on every change; focus lost after DOM replacement.
- Forms built without `<form>`, `<label>` and native validation.
- Newly available APIs used without feature detection; non-Baseline APIs without a fallback.

## Legacy to modern
| Legacy | Modern |
|---|---|
| jQuery, `$(document).ready` | DOM APIs, `type="module"` scripts (already deferred) |
| `var`, IIFEs, global namespaces | `const`/`let`, ES modules |
| `XMLHttpRequest`, callback pyramids | `fetch`, `async`/`await`, `AbortController` |
| `document.write`, inline `onclick=""` | DOM creation, `addEventListener` |
| `innerHTML` with user data | `textContent`, `<template>`, sanitizer under Trusted Types |
| manual `removeEventListener` bookkeeping | `{ signal }` with `AbortController` |
| custom modal, tooltip and accordion scripts | `<dialog>`, `popover`, `<details name>` |
| scroll listeners for lazy loading | `loading="lazy"`, `IntersectionObserver` |
| `keyCode`, `which`, user-agent sniffing | `event.key`, feature detection |
| Moment.js, Lodash for built-ins | `Intl`, native array, object, Set and iterator methods |
| polyfills for widely available features | none; delete them |
