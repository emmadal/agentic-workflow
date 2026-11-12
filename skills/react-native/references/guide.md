# react-native: detailed guide

Loaded on demand from SKILL.md. Rules here expand the checklist.

Act as a senior React Native engineer with 10+ years in mobile and web. Pair with `mobile-engineering`. Check the project's React Native version and whether it uses Expo before suggesting native changes. Since 0.82 the New Architecture is the only one (legacy code is being removed from 0.84 on); apps still on 0.81 or Expo SDK 54 must migrate before upgrading. Verify unfamiliar APIs in the current docs. Target the latest stable release (npm `latest` tag, not `next` or RCs). In Expo apps React Native comes from the SDK: upgrade through the `expo` skill (`npx expo install --fix`), never bump `react-native` alone.

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
- Hermes on. New Architecture (Fabric, Turbo Modules, JSI) only; audit every native dependency for support (reactnative.directory) before upgrading.
- Lists: FlashList v2 (New Architecture, automatic sizing, no `estimatedItemSize`) or `FlatList` with stable `keyExtractor` and `getItemLayout` when heights are fixed; no anonymous components or large images in rows.
- Keep the JS thread free: heavy work off the UI path; animations on the UI thread with Reanimated 4 (CSS animations and transitions for simple cases, worklets for gestures) and gesture-handler; avoid `setState` per frame.
- Enable the React Compiler (default in new Expo projects) and drop hand-written memoization it makes redundant; keep `React.memo`, `useMemo`, `useCallback` only where the Profiler proves a gain. Measure with React Native DevTools (the Profiler and Performance panels), Perfetto, Xcode Instruments, release builds only. Flipper is no longer supported.
- Optimize images (size, format, caching with expo-image), reduce bundle (Metro, inline requires, remove unused deps).

## Native code
- Prefer maintained libraries. For custom native code use TurboModules/Expo Modules API with typed specs (Codegen). Keep native surface small; test on both platforms.

## Testing
- Unit and component: Jest + React Native Testing Library (`render`, `screen`, `userEvent`); query by role, label and text, not test IDs by default. Mock native modules at the boundary; use MSW for network.
- E2E on simulator/emulator/device: Maestro (YAML flows) or Detox (gray-box). Cover login, core journey, permissions, deep link, offline. See `mobile-device-testing`.
- Type check and lint in CI: `tsc --noEmit`, ESLint, Prettier.

## Release
- OTA updates with EAS Update (CodePush ended with App Center's retirement) only for JS changes compatible with the installed native runtime; version by `runtimeVersion`. Source maps uploaded to the crash reporter. Hermes bytecode and ProGuard/R8 verified on a release build.

## Done when
Typecheck, lint and tests green; release build run on an iOS simulator and an Android emulator, plus one real device for performance, permissions or native modules.
