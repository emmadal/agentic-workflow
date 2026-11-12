# expo: Expo Router

Last verified on SDK 58 docs, Nov 2026; re-check on a newer SDK (`docs.expo.dev/versions/latest/sdk/router.md`; append `.md` for the API, `docs.expo.dev/router/introduction.md` for guides).

## Fundamentals
- File-based routing built on React Navigation: `app/` directory, `_layout.tsx`, route groups `(tabs)`, dynamic `[id]`, `+not-found`, typed routes (`experiments.typedRoutes`).
- Deep links via `scheme` in app config; universal links via `associatedDomains` (iOS) and `intentFilters` (Android); test both platforms.

## Navigation primitives (SDK 57 and later)
- **Native tabs** (`sdk/router/native-tabs.md`) — platform-native tab UI (UITabBarController/BottomNavigationView style) for app-level navigation.
- **Split view** (`sdk/router/split-view.md`) — two-column iPad-style layouts.
- Experimental stack (`sdk/router/experimental-stack.md`) and router UI components (`sdk/router/ui.md`) — check the current docs before adopting experimental APIs; behavior changes between SDKs.

## Conventions
- Pair with the `react-native` skill for navigation state patterns. Screens stay dumb: state down, events up.
- Route modules should stay small; colocate screen-specific components, push shared ones up.

## Pitfalls
Deep links configured for one platform only; mixing experimental stack with stable Stack on a production release; large `_layout.tsx`; forgetting that native tabs replace custom tab implementations rather than compose with them.
