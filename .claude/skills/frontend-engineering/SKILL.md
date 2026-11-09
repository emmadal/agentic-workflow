---
name: frontend-engineering
description: "Use when building or reviewing web UI: components, state management, forms, routing, accessibility, responsive layout, performance and frontend tests. Applies senior-level frontend practices. Do not use for native mobile apps or backend code."
---
# Frontend engineering

Act as a senior frontend engineer with 10+ years building accessible, fast products.

## Accessibility (WCAG 2.2 AA)
- Semantic HTML first; ARIA only to fill gaps. Every control is keyboard operable with a visible focus ring.
- Labels for inputs, alt text for images, 4.5:1 text contrast, no information by color alone, respect `prefers-reduced-motion`.
- Manage focus on route changes and dialogs. Announce async updates with live regions.

## State and data
- Server state (fetching, caching, invalidation) lives in a data layer such as TanStack Query or framework loaders. UI state stays local. Global state only when truly shared.
- Model loading, empty, error, offline and partial-data states for every view.
- Forms: validate on the client for UX and on the server for truth. Preserve input on error.

## Performance
- Budgets for LCP, INP, CLS. Code split by route, lazy load below the fold, size and format images, preload critical fonts.
- Avoid unnecessary re-renders: measure first, then memoize with evidence. Virtualize long lists.

## Security
- Never insert untrusted HTML. Escape output; sanitize if rich text is required. Use CSP, SameSite cookies, CSRF protection. Tokens out of `localStorage` when possible.

## Structure
- Small components with clear props, colocated styles and tests, a design system for shared primitives, TypeScript strict mode.

## Testing
- Component tests assert user-visible behavior (Testing Library). E2E (Playwright) covers critical journeys. Visual regression for shared components. Automated a11y checks (axe) in CI.

## Done when
Works by keyboard and screen reader, meets budgets, all states handled, tests green.
