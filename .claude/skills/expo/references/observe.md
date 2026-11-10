# expo: Expo Observe (`expo-observe`)

Verified against SDK 58 docs: `docs.expo.dev/versions/latest/sdk/observe.md` and `docs.expo.dev/eas/observe/introduction.md`. Library = `expo-observe`; service = Expo Observe. Export to any OTEL-compliant backend is supported.

## What it measures
Production performance, not dev profiling (dev: React Native DevTools, Expo Atlas):
- Startup: cold/warm launch, Time to First Render (TTR), Time to Interactive (TTI), bundle load time.
- Expo Update download times; per-route navigation metrics (cold_ttr, warm_ttr, tti) via integrations.
- JavaScript errors with symbolicated stack traces and native crashes (SDK 57+, in preview).
- User-defined events; network requests as trace spans (off by default — each span costs quota).

## Setup
```sh
npx expo install expo-observe
```
```tsx
import { ObserveRoot, useObserve } from 'expo-observe';
function RootLayout() {
  const { markInteractive } = useObserve();
  useEffect(() => { markInteractive(); }, [markInteractive]); // after init work
  return <Stack />;
}
export default ObserveRoot.wrap(RootLayout);
```
- Release builds work with no config; `markInteractive`/`ObserveInteractiveMarker` (fire-once on mount) records TTI.
- Declarative TTI: `<ObserveInteractiveMarker params={{...}} />` once the screen is interactive.
- `ObserveErrorBoundary` catches render-phase errors (they never reach `global.ErrorUtils`) with component stack; `ObserveRoot.errorBoundaryFallback` mounts one at the root. `Observe.reportError(e)` for caught errors.
- Requires a development or production build — **not available in Expo Go**.

## Configuration (`Observe.configure({})`)
- `environment` (default `process.env.NODE_ENV`), `dispatchingEnabled`, `dispatchInDebug` (debug builds never dispatch by default), `sampleRate` (deterministic per installation), `errorHandlingEnabled`, `networkTraces` (`true` or a filter object), `integrations.expo-router` / `.react-navigation` (with `filteredParams` for PII).
- Dispatch happens on background/app-resign (Android: background worker when network returns); flush manually with `await Observe.dispatchEvents()`.

## Events and attributes
- `Observe.logEvent(name, { body, attributes, severity, displayName })` — severity: trace|debug|info|warn|error|fatal.
- `Observe.setGlobalAttributes({...})` merged into every record; `Observe.clientId` = stable pseudonymous install id (`expo.eas_client.id`) to correlate with your own backend.

## Querying
- CLI: `eas observe:` commands. AI agents: Expo MCP Server (`docs.expo.dev/eas/observe/ai-agents.md`). Dashboard for release comparison and session drill-down.
- Quota: 100k events/month free, 500k on paid plans; retention 90 days; anonymous per-install user id (no PII).

## Pitfalls
Debug builds silently dropping metrics (`dispatchInDebug`); network traces left on and burning quota; unfiltered route params leaking query data; expecting metrics in Expo Go.
