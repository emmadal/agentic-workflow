---
name: mobile-engineering
description: "Use when starting any mobile app task (iOS, Android, KMP, Flutter, React Native, Expo) or planning app architecture, offline support, old app versions: sets cross-platform rules and routes to the platform skill."
---
# Mobile engineering

Assume slow networks, old devices, old app versions, and users who kill the app mid-request.

## Route
Swift/SwiftUI `swift-ios` · Kotlin `kotlin-android` · Compose `android-compose` · shared Kotlin `kotlin-multiplatform` · Flutter/Dart `flutter` · RN `react-native` · Expo `expo` (SDK, Expo UI, Router, EAS Observe) · Figma to Expo `figma-to-expo` · run/test on simulator, emulator, device `mobile-device-testing` · find-and-fix QA on a running app `ios-qa`, `android-qa`.

## Rules
1. UI is a function of state. State down, events up. No business logic in views.
2. Local DB is the source of truth; network refreshes it. Show cache first.
3. Every request has a timeout. Retries use backoff and jitter and only for idempotent calls.
4. API is versioned. Old app versions keep working. Ship a minimum-version check.
5. Secrets in Keychain or Keystore. Never in prefs, logs, screenshots or the bundle.
6. Handle backgrounding, process death, rotation, permission denial and revocation.
7. Cancel work when the screen goes away. Heavy work off the main thread.
8. Accessibility: labels, font scaling, 44pt or 48dp targets, contrast.
9. Risky changes sit behind a flag or remote config. Release is staged. Crash and ANR monitoring is on.

## Pitfalls
| Excuse | Reality |
|---|---|
| "Works on my simulator" | Performance, push, camera, biometrics and thermals need a real device. |
| "Debug build is fast enough" | Measure release builds only. |
| "Users will update" | Many never do. Old versions hit your API for years. |

## Verify
Run it. State platform, device or emulator, OS version, build type and result. Load `references/guide.md` when designing architecture, release or offline sync.
