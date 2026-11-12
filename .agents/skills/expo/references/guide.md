# expo: detailed guide

Loaded on demand from SKILL.md. Rules here expand the checklist.

Act as a senior Expo engineer with 10+ years of mobile experience. Pair with `react-native` and `mobile-engineering`. Version policy, never pinned to one SDK:
- Target the latest stable Expo SDK: the npm `latest` tag (`npm view expo version`). `next`, `beta` and `canary` are pre-releases: only when the user asks.
- Each SDK pins one React Native, React and minimum Node version (table "Each Expo SDK version depends on a React Native version" in `docs.expo.dev/versions/latest.md`). `npx expo install --fix` aligns them. Never bump `react-native` past the SDK's pin, even when a newer React Native is out.
- New app: `npx create-expo-app@latest`. Existing app: read its SDK in `package.json` and use that SDK's docs (`docs.expo.dev/versions/v<N>.0.0/`); behavior changes between SDKs. Offer upgrades one SDK at a time (`docs.expo.dev/workflow/upgrading-expo-sdk-walkthrough.md`): `npm install expo@^<N>.0.0` (or the project's package manager), `npx expo install --fix`, then `npx expo-doctor`, with the release notes in `expo.dev/changelog`.
- Facts in these references were last verified on SDK 58 (Nov 2026). On a newer SDK, re-check them in the docs before relying on them.

Expo docs serve agent-readable Markdown: append `.md` to any docs.expo.dev URL; full tree at `docs.expo.dev/llms.txt`. Official agent skills also exist at `github.com/expo/skills` (expo-ui, eas-observe) — ours cover the same ground; verify API details in the docs, not in memory.

## Project
- Install with `npx expo install <pkg>` so versions match the SDK. Run `npx expo-doctor` and `npx expo install --check` to find mismatches.
- Config in `app.config.ts` (dynamic, typed) over static `app.json` when values depend on environment. Use `EXPO_PUBLIC_` prefix only for non-secret client values. Secrets live in EAS secrets or the server, never in the bundle.
- Prefer Continuous Native Generation: do not hand-edit `ios/` and `android/`; express native changes through config plugins (`app.config` `plugins`), then `npx expo prebuild --clean` to regenerate.
- Module map: `sdk-modules.md` — first-party packages for most device capabilities.

## Routing
- Expo Router: `app/` directory, `_layout.tsx`, route groups `(tabs)`, dynamic `[id]`, typed routes, `+not-found`. Deep links via `scheme`; `associatedDomains` and `intentFilters` for universal and app links. Native tabs, split view and the router UI set are covered in `router.md`.

## Running and building
- Expo Go is for quick prototypes only; it cannot load custom native code. Use a **development build** (`expo-dev-client`) for real work: `npx expo run:ios` / `npx expo run:android`, or EAS Build with the `development` profile.
- Build, submit, credentials and OTA updates are detailed in `eas.md`.

## Observability
- Sentry via `@sentry/react-native` with source maps for errors and tracing.
- EAS Observe (`expo-observe`) for production startup/navigation performance and events: `observe.md`.

## Quality
- TypeScript strict, ESLint (`eslint-config-expo`), `npx expo-doctor` clean. Prefer Expo SDK modules with permissions declared in config and requested in context.

## Testing
- Unit and component: `jest-expo` preset with React Native Testing Library.
- E2E: Maestro flows against a development or preview build on a simulator, emulator or device; `eas build --profile preview` for shareable test builds; EAS Workflows or GitHub Actions for CI. See `mobile-device-testing`.
- Check on a real device before release for push notifications, camera, biometrics, background tasks and performance.

## Pitfalls
- Mixing package versions outside `expo install`; editing generated native folders; using Expo Go for features needing native modules; shipping an OTA that depends on new native code.

## Done when
`expo-doctor` clean, typecheck and tests green, preview build run on simulator and emulator, push or hardware features verified on a real device, update channel and runtime version correct.
