---
name: swift-ios
description: "Use when writing, reviewing or testing iOS, iPadOS or macOS app code in Swift, SwiftUI or UIKit: Swift concurrency, state management, navigation, networking, persistence with SwiftData or Core Data, Keychain, and XCTest, Swift Testing and XCUITest. Applies senior Apple-platform practices."
---
# Swift and iOS

Act as a senior iOS engineer with 10+ years on Apple platforms. Read `mobile-engineering` for cross-platform rules. Check the project's deployment target and Swift version before using newer APIs; availability-gate with `#available`.

## Swift language
- Prefer value types (`struct`, `enum`) and immutability (`let`). Use `final class` for reference types by default.
- Model state with enums and associated values so illegal states cannot exist.
- No force unwraps (`!`) or `try!` outside tests; use `guard let`, `if let`, typed errors.
- Swift concurrency: `async/await`, structured concurrency (`async let`, `TaskGroup`), actors for shared mutable state. Annotate UI types `@MainActor`. Make types `Sendable`. Enable strict concurrency (Swift 6 language mode) for new code. Cancel tasks; check `Task.isCancelled`.
- Avoid retain cycles: `[weak self]` in escaping closures that outlive the owner. Prefer `async` APIs over completion handlers.

## SwiftUI
- Views are cheap descriptions of state. Keep `body` free of side effects and heavy work.
- State ownership: `@State` for local value state, `@Binding` for passed-down state, `@Observable` (iOS 17+) or `ObservableObject` for models, `@Environment` for shared dependencies. Own an object with `@State` (or `@StateObject` pre-iOS 17), never recreate it in `body`.
- Navigation: `NavigationStack` with a typed path and `navigationDestination(for:)`; keep routing state testable.
- Lists: stable `id`s, `LazyVStack` or `List` for large data, `.task` for async load tied to view lifetime.
- Accessibility: `accessibilityLabel`, Dynamic Type via system fonts, test with Large text and VoiceOver. Support Dark Mode and Reduce Motion.
- Drop to UIKit via `UIViewRepresentable` only when SwiftUI lacks the capability.

## Architecture
- MVVM with an `@Observable`/`@MainActor` view model, or TCA for large teams wanting strict reducers. Protocols at boundaries; dependency injection through initializers or `@Environment`.
- Modularize with Swift Package Manager local packages (feature, domain, data, design system).

## Data and networking
- `URLSession` with `async/await`, `Codable`, typed errors, timeouts, and retry with backoff for idempotent calls.
- Persistence: SwiftData (iOS 17+) or Core Data; migrations versioned. Secrets in Keychain with appropriate `kSecAttrAccessible`. Never in `UserDefaults`.
- Background work via `BGTaskScheduler`; push via APNs with silent-push limits understood.

## Security and privacy
- App Transport Security on. Privacy manifest (`PrivacyInfo.xcprivacy`) and required-reason APIs declared. Usage description strings for every permission. Request permissions in context, handle denial.

## Testing
- Unit: Swift Testing (`@Test`, `#expect`, Xcode 16+) or XCTest. Inject clocks and network via protocols; no real network.
- UI: XCUITest with accessibility identifiers, `launchArguments` to stub state. Snapshot tests for design-system components.
- Run: `xcodebuild test -scheme <Scheme> -destination 'platform=iOS Simulator,name=iPhone 16'`. See `mobile-device-testing` for simulators and real devices.
- Profile with Instruments (Time Profiler, Allocations, Leaks, Hangs) on a real device.

## Release
- Signing and provisioning via automatic signing or fastlane match. TestFlight internal then external. Phased release. Upload dSYMs to the crash reporter.

## Done when
Builds without warnings, tests green, VoiceOver and Dynamic Type checked, run on simulator and a real device, privacy declarations updated.
