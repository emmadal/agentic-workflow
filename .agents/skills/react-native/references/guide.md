# react-native: detailed guide

Loaded on demand from SKILL.md. Rules here expand the checklist.

Act as a senior React Native engineer with 10+ years in mobile and web. Pair with `mobile-engineering`. Check the project's React Native version, whether the New Architecture is enabled, and whether it is Expo-managed before suggesting native changes. Verify unfamiliar APIs in the current docs.

## Code
- TypeScript `strict`. Function components and hooks. Small components; colocate styles and tests. No inline anonymous components in render paths of lists.
- Platform differences with `Platform.select` or `.ios.tsx`/`.android.tsx` files, not scattered conditionals.
- Styles via `StyleSheet.create` or the project's styling lib; use theme tokens; respect safe areas (`react-native-safe-area-context`) and keyboard avoidance.

## State and data
- Server state with TanStack Query (cache, retry, invalidation, offline persistence). Local UI state with `useState`/`useReducer`; shared client state with Zustand or Redux Toolkit only when needed.
- Persist with MMKV or SQLite (op-sqlite, WatermelonDB). Secrets in Keychain/Keystore via `expo-secure-store` or `react-native-keychain`, never `AsyncStorage`.
- Validate API data at the boundary (Zod). Handle loading, empty, error, offline.

## Navigation
- React Navigation or Expo Router. Typed routes and params. Deep links and universal links configured and tested. Lazy-load heavy screens.

## Performance
- Hermes on. New Architecture (Fabric, TurboModules) is the default in current versions; check native library compatibility.
- Lists: `FlashList` or `FlatList` with stable `keyExtractor`, `getItemLayout` when fixed height, memoized `renderItem`, avoid anonymous functions and large images in rows.
- Keep the JS thread free: heavy work off the UI path; animations on the UI thread with Reanimated worklets and gesture-handler; avoid `setState` per frame.
- Memoize with evidence (`React.memo`, `useCallback`, `useMemo`), use the React Compiler if adopted. Measure with the React DevTools Profiler, Perfetto, Xcode Instruments, Flipper alternatives, and release builds only.
- Optimize images (size, format, caching with expo-image), reduce bundle (Metro, inline requires, remove unused deps).

## Native code
- Prefer maintained libraries. For custom native code use TurboModules/Expo Modules API with typed specs (Codegen). Keep native surface small; test on both platforms.

## Testing
- Unit and component: Jest + React Native Testing Library (`render`, `screen`, `userEvent`); query by role, label and text, not test IDs by default. Mock native modules at the boundary; use MSW for network.
- E2E on simulator/emulator/device: Maestro (YAML flows) or Detox (gray-box). Cover login, core journey, permissions, deep link, offline. See `mobile-device-testing`.
- Type check and lint in CI: `tsc --noEmit`, ESLint, Prettier.

## Release
- OTA updates (EAS Update or CodePush alternatives) only for JS changes compatible with the installed native runtime; version by runtime. Source maps uploaded to the crash reporter. Hermes bytecode and ProGuard/R8 verified on a release build.

## Done when
Typecheck, lint and tests green; release build run on an iOS simulator and an Android emulator, plus one real device for performance, permissions or native modules.
