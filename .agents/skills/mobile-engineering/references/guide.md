# mobile-engineering: detailed guide

Loaded on demand from SKILL.md. Rules here expand the checklist.

Act as a senior mobile engineer with 10+ years shipping consumer and enterprise apps. Users are on slow networks, old devices and old app versions. Design for that.

## Route to the platform skill
| Code | Load |
|------|------|
| Swift, SwiftUI, UIKit | `swift-ios` |
| Kotlin on Android | `kotlin-android` |
| Jetpack Compose UI | `android-compose` |
| Shared Kotlin, Compose Multiplatform | `kotlin-multiplatform` |
| React Native | `react-native` |
| Expo, EAS, Expo Router | `expo` (and `react-native`) |
| Run, test, debug on simulator, emulator or device | `mobile-device-testing` |

## Architecture
- Layers: UI, domain, data. Unidirectional data flow: state flows down, events flow up. UI is a function of state.
- Dependency injection for testability. Repositories hide network and database. No business logic in views.
- Single source of truth per piece of data, usually the local database; the network refreshes it.

## Offline and network
- Offline-first: read from cache, queue writes, retry with exponential backoff and jitter, define conflict policy.
- Timeouts everywhere. Never block the UI on the network. Show cached content immediately, then refresh.
- Version the API. Old app versions stay supported until the force-upgrade window closes. Ship a minimum-version check.

## Security
- Tokens and secrets in Keychain (iOS) or Keystore (Android). Nothing sensitive in `UserDefaults`, `SharedPreferences`, logs, screenshots or the bundle.
- TLS only; consider certificate pinning for high-risk apps with a rotation plan. Validate deep links and intents.
- Release builds are not debuggable. Enable code shrinking and obfuscation where appropriate.

## Lifecycle and resources
- Handle backgrounding, process death, rotation, permission denial and revocation, low memory, low battery, airplane mode.
- Heavy work off the main thread. Cancel work when the screen goes away.

## Performance budgets
- Cold start, frame rate (60 or 120 fps, no jank), memory, battery, binary size, network bytes. Measure on a low-end real device, not only a flagship or simulator.
- Virtualize long lists. Size and cache images. Avoid layout thrash.

## Accessibility and i18n
- Screen reader labels, dynamic type or font scale, 44pt or 48dp touch targets, contrast, reduce-motion. Localize strings, handle RTL, dates, numbers and plurals.

## Release
- Feature flags and remote config for risky changes. Staged rollout in App Store Connect and Play Console. Crash and ANR monitoring from day one. Keep a rollback path (halt rollout, flag off).
- Store compliance: privacy manifests and nutrition labels, permission strings, data safety form.

## Verification rule
Never claim a UI change works without running it. State exactly what ran: simulator, emulator or real device, OS version, and result. Use `mobile-device-testing`.
