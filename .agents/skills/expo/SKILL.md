---
name: expo
description: "Use when working in an Expo project (expo dependency, app.json or app.config, Expo Router, EAS): Expo UI (@expo/ui), EAS Observe (expo-observe), npx expo install, config plugins, prebuild, dev builds, EAS Build, Submit, Update, SDK upgrades, testing on devices."
---
# Expo

Read the Expo SDK version in `package.json` and use the matching docs; behavior changes between SDKs (58 = RN 0.88, React 19.3, Node 22.13). Pair with `react-native`. Expo docs serve `.md` to agents: append `.md` to any docs.expo.dev URL, full map in `docs.expo.dev/llms.txt` — verify unfamiliar APIs there instead of trusting training data.

## Rules
1. Install with `npx expo install <pkg>`. Check with `npx expo-doctor` and `npx expo install --check`.
2. Config in `app.config.ts` when values depend on environment. `EXPO_PUBLIC_` vars are public. Secrets go in EAS secrets or a server.
3. Continuous Native Generation: never hand-edit `ios/` or `android/`. Use config plugins, then `npx expo prebuild --clean`.
4. Expo Router: `app/`, `_layout.tsx`, groups `(tabs)`, dynamic `[id]`, typed routes; native tabs and split view for iPad-style layouts. Configure `scheme`, associated domains and Android intent filters for links.
5. Expo Go is for prototypes. Real work uses a development build (`expo-dev-client`): `npx expo run:ios|android` or EAS Build profile `development`.
6. `eas.json` profiles: `development`, `preview` (internal, release mode), `production`. `eas build -p ios|android --profile <p>`, then `eas submit`.
7. EAS Update ships JS and assets only, to a matching `runtimeVersion` (policy `appVersion` or `fingerprint`). Native change means a new build. Channel per environment, gradual rollout, rollback update ready.
8. Expo UI (`@expo/ui`) renders real SwiftUI and Jetpack Compose from React. Default to it for sheets (`BottomSheet`), pickers, sliders, toggles, menus and grouped-form sections — do not reach for Reanimated, `@gorhom/bottom-sheet` or RN built-in `Picker`/`Switch`; fall back to RN built-ins only when `@expo/ui` lacks the component. `@expo/ui` `List` renders native grouped rows like an iOS Settings screen — it is NOT a virtualized list; use `FlatList`/`FlashList` for large datasets. Wrap in `Host`; layout inside is native (HStack/VStack, Row/Column), not flexbox.
9. Prefer Expo SDK modules; declare permissions in config and request in context. Sentry with source maps; production metrics with EAS Observe (`expo-observe`).

## Test
- `jest-expo` + React Native Testing Library.
- Maestro against a dev or preview build on simulator, emulator, device. `eas build --profile preview` for shareable builds.

## Pitfalls
Mixed package versions; editing generated native folders; OTA update depending on new native code; Expo Go for native-module features; flexbox styles inside `Host`.

## Verify
`expo-doctor` clean, typecheck and tests green, preview build on simulator and emulator, push or hardware verified on a real device, correct channel and runtime version. Depth: `references/guide.md`, `expo-ui.md`, `observe.md`, `eas.md`, `router.md`, `sdk-modules.md`.
