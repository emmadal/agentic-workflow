# swift-ios: detailed guide

Loaded on demand from SKILL.md. Sources: Swift API Design Guidelines, The Swift Programming Language, Swift Concurrency Migration Guide, Apple Human Interface Guidelines and WWDC sessions. Check the project's deployment target and Swift version before using newer APIs.

## Swift language
- Clarity at the point of use: `remove(at:)`, `makeIterator()`, Boolean properties read as assertions (`isEmpty`). Omit needless words; name by role, not type.
- Model state with enums so impossible states do not compile:
  ```swift
  enum LoadState<Value> { case idle, loading, loaded(Value), failed(any Error) }
  ```
- Typed throws (`throws(NetworkError)`) for closed error sets inside a module; untyped `throws` at public API boundaries that may grow.
- `guard` for early exit. `some Protocol` over `any Protocol` unless you need heterogeneity.

## Concurrency (Swift 6 and 6.2)
- Swift 6 language mode makes data-race safety an error. Migrate module by module: enable complete checking in Swift 5 mode, fix, then switch the mode.
- Swift 6.2 "approachable concurrency": new app targets set default actor isolation to `MainActor` (`-default-isolation MainActor`, SwiftPM `swiftSettings: [.defaultIsolation(MainActor.self)]`). Unannotated code runs on the main actor; opt out per type with `nonisolated`.
- `NonisolatedNonsendingByDefault`: nonisolated `async` functions run on the caller's actor. Mark functions that must leave the actor `@concurrent`:
  ```swift
  nonisolated struct ImageDecoder {
      @concurrent func decode(_ data: Data) async throws -> CGImage { /* CPU work */ }
  }
  ```
- Actors protect mutable state; keep actor methods small and avoid `await` in the middle of invariants (reentrancy).
- `Sendable`: value types of Sendable members are implicit. Classes need `final` + immutable state, or an actor, or a lock (`Mutex` from the Synchronization module, iOS 18+). `@unchecked Sendable` only with a comment explaining the lock.
- Tasks: `.task {}` on views (cancelled automatically), `async let` for fixed fan-out, `withThrowingTaskGroup` for dynamic fan-out. Store long-lived `Task` handles and cancel them. `Task.detached` almost never.
- `AsyncStream` to bridge delegate or callback APIs; finish the continuation on cancellation (`onTermination`).

## SwiftUI and Observation
- `@Observable final class` view models; properties are tracked per access, so views only re-render for what they read. Use `@ObservationIgnored` for caches.
- Ownership: `@State private var model = Model()` in the owning view; pass the instance down; `@Bindable var model` where bindings are needed; `@Environment(Model.self)` for app-wide dependencies.
- Identity: stable `id` in `ForEach`; avoid conditional view identity flips (`if` that swaps whole hierarchies) when a modifier would do.
- Lists: `List` or `LazyVStack` for large data; avoid `GeometryReader` in rows.
- Previews: `#Preview` with fixtures for loading, empty, error, long text, largest Dynamic Type, dark mode; `@Previewable @State` for interactive previews.
- UIKit bridge: `UIViewRepresentable` / `UIViewControllerRepresentable` only when SwiftUI lacks the capability; coordinators hold delegates.

## Navigation
```swift
enum Route: Hashable { case detail(Item.ID), settings }
@Observable final class Router { var path: [Route] = [] }

NavigationStack(path: $router.path) {
    HomeView()
        .navigationDestination(for: Route.self) { route in
            switch route {
            case .detail(let id): DetailView(id: id)
            case .settings: SettingsView()
            }
        }
}
```
Deep links parse into `[Route]` and assign `router.path`, so the same code path is tested. Use `NavigationSplitView` for sidebar layouts on iPad and Mac.

## Data and networking
- SwiftData: `@Model` classes, `ModelContainer` in the app, `@Query` in views for simple reads, a `ModelActor` for background writes. Every shipped schema is a `VersionedSchema`; changes go through a `SchemaMigrationPlan`, tested on a copy of real data.
- Core Data: lightweight migrations where possible, `NSPersistentContainer` background contexts, never pass managed objects across contexts.
- Networking: one `APIClient` with `URLSession` async, request timeouts, retries with backoff and jitter only for idempotent requests, `Codable` with explicit `CodingKeys` and date strategies.
- Keychain: `kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly` for tokens unless background access needs otherwise; wrap in a small type with tests.

## Platform features
- Background: `BGTaskScheduler` (refresh and processing); background `URLSession` for large transfers.
- Push: APNs with token refresh handling; silent pushes are throttled and not guaranteed.
- App Intents for Shortcuts, Siri, Spotlight and widgets. WidgetKit timelines are budgeted.
- iOS 26 Liquid Glass: standard bars, sheets, tab views and controls adopt it when built with the iOS 26 SDK. Test legibility over busy content; respect Reduce Transparency. Use `.glassEffect()` only for custom controls, gated by `#available(iOS 26, *)`.

## Accessibility
- Dynamic Type: system text styles (`.body`, `.headline`), `@ScaledMetric` for custom sizes, layouts that switch to vertical at accessibility sizes (`ViewThatFits` or `dynamicTypeSize.isAccessibilitySize`).
- VoiceOver: `accessibilityLabel`, `accessibilityValue`, `accessibilityHint`, traits, `accessibilityElement(children: .combine)` for cells, custom actions instead of hidden gestures.
- Check with Accessibility Inspector and in UI tests: `try app.performAccessibilityAudit()`.

## Testing
- Swift Testing:
  ```swift
  @Suite struct PriceFormatterTests {
      @Test(arguments: [(0, "$0.00"), (1999, "$19.99")])
      func formats(cents: Int, expected: String) { #expect(PriceFormatter().string(cents) == expected) }
  }
  ```
  `#require` unwraps or stops the test; traits `.tags`, `.timeLimit`, `.enabled(if:)`; tests run in parallel by default, so no shared mutable state.
- XCTest still owns UI tests (`XCUIApplication`) and performance tests (`measure(metrics:)`).
- UI tests: launch arguments and environment (`-ui-testing`, `-seed empty`) to stub the backend and reset state; query by accessibility identifier; wait with `waitForExistence(timeout:)`, never `sleep`.
- Run: `xcodebuild test -scheme App -destination 'platform=iOS Simulator,name=<device>' -resultBundlePath artifacts/ios.xcresult`. Read failures with `xcrun xcresulttool`.

## Architecture and tooling
- MVVM with `@Observable` view models and protocol-based dependencies is the default; TCA for teams that want strict reducers. Feature modules as local Swift packages (Feature, Domain, Data, DesignSystem) to speed builds and enforce boundaries.
- swift-format or SwiftLint in CI; treat warnings as errors on CI; strict concurrency checking on every module.

## Release
- Automatic signing or fastlane match. TestFlight internal, then external, then phased release.
- Upload dSYMs; crash and hang reporting on (MetricKit or a vendor SDK).
- Update `PrivacyInfo.xcprivacy` when adding SDKs or required-reason APIs.

## Done when
Builds with zero warnings in Swift 6 mode, tests green, VoiceOver and largest Dynamic Type checked, accessibility audit passes, run on a simulator and a real device, privacy declarations updated.
