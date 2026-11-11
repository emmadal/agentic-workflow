# Issue taxonomy

## Severity
| Severity | Meaning | Examples |
|---|---|---|
| critical | Core journey blocked, data loss or corruption, security hole, crash | checkout fails, data deleted without confirmation, another user's data visible, 500 on login |
| high | Major feature broken, no workaround | search returns wrong results, upload silently fails, redirect loop, API returns 200 with an error body |
| medium | Works with visible problems or a workaround | slow page (over 3 s), missing validation that the server still catches, layout broken only on mobile, confusing error |
| low | Cosmetic or polish | typo, 1px misalignment, inconsistent hover state |

Raise one level when the defect hits money, privacy, onboarding or a large share of users. Lower one level when it only affects an internal or admin page.

## Categories
1. **Functional**: dead controls, wrong results, broken links, state lost on refresh or back, double submit, race conditions, wrong redirects.
2. **Visual**: overlap, clipping, horizontal scroll, broken images, dark mode issues, z-index.
3. **UX**: no loading feedback, unclear errors, dead ends, no confirmation before destructive actions, inconsistent patterns.
4. **Content**: typos, placeholder text, truncation without ellipsis, wrong labels, missing empty states.
5. **Performance**: slow load, layout shift, jank, oversized images, excessive requests.
6. **Console and network**: uncaught exceptions, failed requests (4xx, 5xx), CORS, mixed content, CSP violations, deprecation warnings.
7. **Accessibility**: missing alt text or labels, keyboard traps, unreachable controls, focus not visible, poor contrast, wrong ARIA.
8. **Security**: secrets in responses or logs, missing authorization, IDs that can be guessed to read others' data, unsafe HTML rendering.
9. **API contract** (API and CLI targets): wrong status code, schema drift, unhelpful error, non-idempotent retry, wrong exit code, error on stdout instead of stderr.

## Per-page checklist (web)
1. Screenshot and look: layout, images, alignment.
2. Every interactive element does what it says.
3. Forms: empty, invalid, boundary, very long, unicode and emoji, paste, double submit.
4. Navigation: in and out, back button, deep link, refresh.
5. States: loading, empty, error, overflow (many items, long names).
6. Console and network after each interaction.
7. 375px and 768px widths.
8. Keyboard only: tab order, visible focus, escape closes dialogs.
9. Auth boundaries: signed out and other roles, using accounts the user provided; never sign the user out of their own session.

## Finding record
```
ISSUE-NNN  severity  category  page or command
Steps: 1. ... 2. ... 3. Observe ...
Expected: ...   Actual: ...
Evidence: evidence/issue-NNN-*.png, console line, request and response, command output
Confirmed: replayed once from the same starting state (yes or no)
```
