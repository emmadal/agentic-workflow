# expo: detailed guide

Loaded on demand from SKILL.md. Rules here expand the checklist.

Act as a senior Expo engineer with 10+ years of mobile experience. Pair with `react-native` and `mobile-engineering`. Read `package.json` for the Expo SDK version first and check the matching docs; behavior changes between SDKs.

## Project
- Install with `npx expo install <pkg>` so versions match the SDK. Run `npx expo-doctor` and `npx expo install --check` to find mismatches.
- Config in `app.config.ts` (dynamic, typed) over static `app.json` when values depend on environment. Use `EXPO_PUBLIC_` prefix only for non-secret client values. Secrets live in EAS secrets or the server, never in the bundle.
- Prefer Continuous Native Generation: do not hand-edit `ios/` and `android/`; express native changes through config plugins (`app.config` `plugins`), then `npx expo prebuild --clean` to regenerate.

## Routing
- Expo Router (file-based, built on React Navigation): `app/` directory, `_layout.tsx`, route groups `(tabs)`, dynamic `[id]`, typed routes (`experiments.typedRoutes`), `+not-found`. Handle deep links via `scheme`; configure `associatedDomains` and Android `intentFilters` for universal and app links.

## Running and building
- Expo Go is for quick prototypes only; it cannot load custom native code. Use a **development build** (`expo-dev-client`) for real work: `npx expo run:ios` / `npx expo run:android`, or EAS Build with the `development` profile.
- `eas.json` profiles: `development` (dev client, internal), `preview` (internal distribution, release mode), `production` (store). `eas build -p ios|android --profile <p>`, `eas submit`.
- Credentials managed by EAS; use `appVersionSource: remote` with `autoIncrement` for build numbers.

## Updates
- EAS Update delivers JS and asset changes OTA to a matching `runtimeVersion` (use `policy: appVersion` or `fingerprint`). Native changes require a new build. Use channels per environment; roll out gradually and keep a rollback update ready.

## Quality
- TypeScript strict, ESLint (`eslint-config-expo`), `npx expo-doctor` clean. Prefer Expo SDK modules (`expo-secure-store`, `expo-image`, `expo-notifications`, `expo-camera`) with permissions declared in config and requested in context.
- Observability: Sentry via `@sentry/react-native` with source maps; EAS Observe/analytics as available.

## Testing
- Unit and component: `jest-expo` preset with React Native Testing Library.
- E2E: Maestro flows against a development or preview build on a simulator, emulator or device; `eas build --profile preview` for shareable test builds; EAS Workflows or GitHub Actions for CI. See `mobile-device-testing`.
- Check on a real device before release for push notifications, camera, biometrics, background tasks and performance.

## Pitfalls
- Mixing package versions outside `expo install`; editing generated native folders; using Expo Go for features needing native modules; shipping an OTA that depends on new native code.

## Done when
`expo-doctor` clean, typecheck and tests green, preview build run on simulator and emulator, push or hardware features verified on a real device, update channel and runtime version correct.
