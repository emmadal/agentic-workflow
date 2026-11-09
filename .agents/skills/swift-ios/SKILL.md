---
name: swift-ios
description: "Use when writing, reviewing or testing Swift, SwiftUI or UIKit code for iOS/iPadOS: concurrency, state ownership, navigation, SwiftData or Core Data, Keychain, Swift Testing, XCTest, XCUITest."
---
# Swift and iOS

Read the deployment target and Swift version first. Gate newer APIs with `#available`.

## Rules
1. `struct` and `let` by default; `final class` otherwise. Enums with payloads for state. No `!` or `try!` outside tests.
2. Concurrency: `async/await`, actors for shared state, `@MainActor` on UI and view models, `Sendable` across boundaries. Enable Swift 6 strict concurrency on new code. Check `Task.isCancelled`; store and cancel long tasks.
3. `[weak self]` only in escaping closures that outlive the owner. Prefer async APIs over callbacks.
4. SwiftUI state: `@State` local, `@Binding` passed down, `@Observable` (iOS 17+) or `ObservableObject` for models, `@Environment` for dependencies. Create owned models with `@State` or `@StateObject`, never inside `body`.
5. `body` is pure and cheap. Stable `id`s in lists. `.task` for async work tied to view lifetime.
6. Navigation: `NavigationStack` with a typed path.
7. `URLSession` async, `Codable`, timeouts, typed errors. Secrets in Keychain, never `UserDefaults`.
8. Ship `PrivacyInfo.xcprivacy`, usage strings for every permission, ATS on.
9. Dynamic Type, VoiceOver labels, Dark Mode, Reduce Motion.

## Test
- Unit: Swift Testing (`@Test`, `#expect`) or XCTest. Inject clock and network behind protocols.
- UI: XCUITest with accessibility identifiers and launch arguments to stub state.
- `xcodebuild test -scheme <S> -destination 'platform=iOS Simulator,name=iPhone 16'`
- Profile on a real device with Instruments: Time Profiler, Allocations, Hangs.

## Pitfalls
Re-creating an `ObservableObject` on every render; heavy work in `body`; unstructured `Task {}` that outlives the screen; forgetting dSYM upload; testing push or camera on a simulator.

## Verify
Zero warnings, tests green, run on simulator plus a real device for hardware, push, performance. `references/guide.md` has depth on data, release and architecture.
