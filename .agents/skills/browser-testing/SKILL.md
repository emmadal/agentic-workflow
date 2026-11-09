---
name: browser-testing
description: "Use when verifying or debugging web UI in a real browser: Playwright or DevTools, E2E flows, console and network errors, screenshots, accessibility checks, visual regressions."
---
# Browser testing

1. **Reproduce in a real browser**, not by reading code. Open the page, run the flow, watch console and network.
2. **Playwright** for repeatable E2E: locate by role, label or text (`getByRole`), not CSS or XPath. Auto-waiting assertions (`expect(locator).toBeVisible()`), never `waitForTimeout`.
3. **Isolation**: fresh context per test, seeded data, mock or stage third parties, no ordering between tests.
4. **Cover** the critical journey, error and empty states, keyboard-only use, mobile viewport (320 and 390 px), slow network throttling.
5. **Accessibility**: run axe, then tab through the page manually.
6. **Evidence**: trace, screenshot and video on failure. `npx playwright show-trace`.
7. **DevTools** for diagnosis: Console (errors and warnings), Network (failed, slow, large), Performance and Lighthouse for Web Vitals, Elements for layout.
8. Fix flakiness at the cause: await the real condition, stabilize data, do not add retries.

## Red flags
`sleep` or fixed timeouts · selectors tied to DOM structure · tests that depend on each other · "passes locally" with no CI run.

## Verify
Flow passes on 3 consecutive runs in CI; console has no unexpected errors; axe reports no serious violations; a failing run leaves a trace.
