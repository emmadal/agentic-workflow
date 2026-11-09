---
name: react-native
description: "Use when building, reviewing or testing React Native apps: TypeScript, navigation, FlatList and list performance, Reanimated, native modules, New Architecture, Hermes, Jest, Detox, Maestro. For Expo also load expo."
---
# React Native

Read the RN version, whether the New Architecture is on, and whether the project is Expo-managed before suggesting native changes. Verify unfamiliar APIs in current docs.

## Rules
1. TypeScript `strict`. Function components and hooks. Validate API data at the boundary (Zod).
2. Server state in TanStack Query. Local state in `useState`/`useReducer`. Global client state (Zustand, Redux Toolkit) only when shared.
3. Persist with MMKV or SQLite. Secrets in Keychain/Keystore (`expo-secure-store`, `react-native-keychain`), never AsyncStorage.
4. Lists: `FlashList` or `FlatList` with stable `keyExtractor`, memoized `renderItem`, no inline anonymous components, sized images.
5. Keep the JS thread free. Animate on the UI thread with Reanimated worklets and gesture-handler. No `setState` per frame.
6. Memoize with evidence from the Profiler, not by habit.
7. Safe areas and keyboard avoidance on every screen. Platform splits via `Platform.select` or `.ios.tsx`/`.android.tsx`.
8. Typed routes and params. Deep links configured and tested.
9. Native code: maintained libraries first; else TurboModules or Expo Modules with typed specs. Test both platforms.

## Test
- Jest + React Native Testing Library; query by role, label, text. Mock native modules at the edge; MSW for network.
- E2E on simulator, emulator, device: Maestro or Detox. Cover login, core journey, permissions, deep link, offline.
- CI: `tsc --noEmit`, ESLint, tests.

## Pitfalls
Judging performance on a debug build; OTA update that needs new native code; unmaintained native libs that break on New Architecture; fetch in `useEffect` without cancellation.

## Verify
Typecheck, lint, tests green. Release build run on an iOS simulator and an Android emulator; real device for performance, permissions, native modules. Depth: `references/guide.md`.
