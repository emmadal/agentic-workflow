---
name: expo
description: "Use when working in an Expo project (expo dependency, app.json or app.config, Expo Router, EAS): npx expo install, config plugins, dev builds, prebuild, EAS Build, Submit, Update, SDK upgrades, testing on devices."
---
# Expo

Read the Expo SDK version in `package.json` and use the matching docs; behavior changes between SDKs. Pair with `react-native`.

## Rules
1. Install with `npx expo install <pkg>`. Check with `npx expo-doctor` and `npx expo install --check`.
2. Config in `app.config.ts` when values depend on environment. `EXPO_PUBLIC_` vars are public. Secrets go in EAS secrets or a server.
3. Continuous Native Generation: never hand-edit `ios/` or `android/`. Use config plugins, then `npx expo prebuild --clean`.
4. Expo Router: `app/`, `_layout.tsx`, groups `(tabs)`, dynamic `[id]`, typed routes. Configure `scheme`, associated domains and Android intent filters for links.
5. Expo Go is for prototypes. Real work uses a development build (`expo-dev-client`): `npx expo run:ios|android` or EAS Build profile `development`.
6. `eas.json` profiles: `development`, `preview` (internal, release mode), `production`. `eas build -p ios|android --profile <p>`, then `eas submit`.
7. EAS Update ships JS and assets only, to a matching `runtimeVersion` (policy `appVersion` or `fingerprint`). Native change means a new build. Channel per environment, gradual rollout, rollback update ready.
8. Prefer Expo SDK modules; declare permissions in config and request in context. Sentry with source maps.

## Test
- `jest-expo` + React Native Testing Library.
- Maestro against a dev or preview build on simulator, emulator, device. `eas build --profile preview` for shareable builds.

## Pitfalls
Mixed package versions; editing generated native folders; OTA update depending on new native code; Expo Go for native-module features.

## Verify
`expo-doctor` clean, typecheck and tests green, preview build on simulator and emulator, push or hardware verified on a real device, correct channel and runtime version. Depth: `references/guide.md`.
