---
name: swift-ios
description: "Use when writing, reviewing or testing Swift, SwiftUI or UIKit code for iOS/iPadOS: Swift 6 concurrency, @Observable models, navigation, SwiftData or Core Data, Keychain, Swift Testing, XCTest, XCUITest."
---
# Swift and iOS

Follows Apple's Swift API Design Guidelines, the Swift 6 concurrency model and Human Interface Guidelines. First read the deployment target, Swift language mode, Xcode version and the target's default actor isolation (`SWIFT_DEFAULT_ACTOR_ISOLATION` or SwiftPM `.defaultIsolation`). Gate newer APIs with `#available`.

## Rules
1. Value types and `let` by default; `final class` otherwise. Enums with payloads so illegal states cannot exist. Names read clearly at the call site. No `!`, `try!` or `as!` outside tests.
2. Concurrency: Swift 6 language mode for new targets. App targets on Swift 6.2 default to `@MainActor`; mark CPU-heavy async work `@concurrent`. Actors for shared mutable state, `Sendable` across isolation boundaries. `@unchecked Sendable` and `nonisolated(unsafe)` need a written reason. Prefer `async let` and task groups over `Task.detached`; check cancellation.
3. Observation: `@Observable` models (iOS 17+), owned with `@State`, bound with `@Bindable`, injected with `@Environment(Model.self)`. `ObservableObject` only below iOS 17. Never create an owned model inside `body`.
4. Views: `body` pure and cheap; extract subviews (structs, not computed properties) so invalidation stays small; stable `id`s, no `AnyView`; `.task(id:)` for work tied to view lifetime; `#Preview` per state.
5. Navigation: `NavigationStack(path:)` with typed `Hashable` routes; `NavigationSplitView` for iPad and regular width; deep links drive the same router.
6. Data: SwiftData with `VersionedSchema` and a migration plan, or Core Data. `URLSession` async, `Codable`, timeouts, typed errors. Secrets in Keychain, never `UserDefaults`.
7. Platform: `PrivacyInfo.xcprivacy`, usage strings for every permission, ATS on. Standard components so iOS 26 Liquid Glass applies automatically; custom glass only behind `#available`.
8. Accessibility: system text styles and `@ScaledMetric` for Dynamic Type, VoiceOver labels and traits, Reduce Motion, Increase Contrast, 44pt targets.

## Test
- Swift Testing: `@Test`, `#expect`, `#require`, parameterized `arguments:`, `@Suite`. Inject clock and network behind protocols.
- XCUITest with accessibility identifiers and launch arguments; `performAccessibilityAudit()` (iOS 17+).
- `xcodebuild test -scheme <S> -destination 'platform=iOS Simulator,name=<device>' -resultBundlePath artifacts/ios.xcresult`; `swift test` for packages.
- Instruments on a real device: Time Profiler, Allocations, Hangs, SwiftUI.

## Pitfalls
Blocking the main actor with sync I/O; unstructured `Task {}` outliving the screen; silencing Sendable errors with `@unchecked`; heavy work in `body`; missing dSYMs; testing push or camera on a simulator.

## Verify
Zero warnings in Swift 6 mode, tests green, VoiceOver and largest Dynamic Type checked, run on a simulator plus a real device for hardware, push and performance. Depth on concurrency migration, SwiftData, architecture and release: `references/guide.md`.
