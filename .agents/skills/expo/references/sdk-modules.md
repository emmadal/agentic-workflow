# expo: SDK module map (SDK 58)

Use this to reach for the first-party package instead of a community one. Full index with per-package docs: `docs.expo.dev/versions/latest/` (`.md` per page). Install with `npx expo install <pkg>`.

## Evergreen picks
- `expo-image`, `expo-video`, `expo-audio` — first-party media stack.
- `expo-secure-store` (Keychain/Keystore), `expo-sqlite`, `expo-file-system`.
- `expo-notifications`, `expo-task-manager`, `expo-background-task`, `expo-background-fetch`.
- `expo-camera`, `expo-image-picker`, `expo-media-library`, `expo-image-manipulator`.
- `expo-location` (and `expo-location/next` — the reworked API), `expo-sensors`, `expo-devicemotion`.
- `expo-font`, `expo-linear-gradient`, `expo-blur-view`, `expo-haptics`, `expo-splash-screen`, `expo-system-ui`.

## Newer surface worth knowing (SDK 55–58)
- `expo-observe` — production performance metrics and events → `observe.md`.
- `@expo/ui` — SwiftUI/Jetpack Compose from React → `expo-ui.md`.
- `expo-server` — server-side helpers for Expo Router server functions.
- `expo-widgets` — home-screen widgets; `expo-app-intents` — Siri/Shortcuts App Intents; `expo-live-photo`.
- `expo-glass-effect` — iOS Liquid Glass; `expo-mesh-gradient`, `expo-symbols` (SF Symbols).
- `expo-maps` — first-party maps; `expo-app-integrity`, `expo-tracking-transparency`.
- `expo-brownfield` — embed Expo modules in existing native apps; `expo-dev-client` / `expo-dev-menu`.

## Rule
Before adding a third-party library, check the SDK index — Expo ships a maintained first-party version for most device capabilities, with permissions declared in app config and requested in context. Legacy APIs (calendar, contacts, media-library, file-system, background task on some platforms) have non-legacy replacements; prefer them on new code.
