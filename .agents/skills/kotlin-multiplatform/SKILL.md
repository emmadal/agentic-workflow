---
name: kotlin-multiplatform
description: "Use when sharing Kotlin code across Android, iOS, desktop or server with Kotlin Multiplatform (KMP) or Compose Multiplatform: project structure, source sets, expect/actual, Ktor, SQLDelight or Room KMP, Koin, kotlinx libraries, iOS interop with Swift, and testing shared code on every target."
---
# Kotlin Multiplatform

Act as a senior engineer with 10+ years, experienced shipping KMP in production. Pair with `kotlin-android`, `android-compose` and `swift-ios`. Check current KMP, Kotlin and Compose Multiplatform versions in the Gradle version catalog and official docs before changing build logic.

## What to share
- Share business logic first: domain models, use cases, repositories, networking, persistence, validation, analytics events. Share UI (Compose Multiplatform) only when the team accepts one UI toolkit; native UI is a valid choice.
- Do not force sharing. Platform-specific UX, permissions and hardware stay native.

## Structure
- `shared` module with `commonMain`, `androidMain`, `iosMain` (plus `commonTest`, `androidUnitTest`, `iosTest`). Use hierarchical source sets and default hierarchy template. Keep platform code thin.
- `expect/actual` for platform APIs; prefer interfaces plus dependency injection and provide implementations from each platform. Use `expect/actual` for small primitives (UUID, clock, secure storage, logging).
- Modularize by feature when large. Convention plugins, version catalog, explicit API mode for libraries.

## Libraries (multiplatform-ready)
- Networking: Ktor client with engines `OkHttp` (Android) and `Darwin` (iOS), `ContentNegotiation` + kotlinx.serialization.
- Persistence: SQLDelight or Room KMP; settings with multiplatform-settings or DataStore KMP; secrets via platform Keychain/Keystore behind an interface.
- Async: kotlinx.coroutines and Flow. Dates: kotlinx-datetime. DI: Koin or kotlin-inject.
- State: ViewModel (androidx lifecycle KMP) or plain state holders exposing `StateFlow`.

## iOS interop
- Kotlin/Native exports an Objective-C framework. Keep the exported API small, use simple types, avoid exposing generics and suspend functions directly where Swift ergonomics suffer: use SKIE or KMP-NativeCoroutines for `async`/`Flow` bridging.
- Memory: new Kotlin/Native memory manager is the default; avoid freezing concepts. Watch for retain cycles across the boundary.
- Distribute via XCFramework with Swift Package Manager, or the Gradle `embedAndSignAppleFrameworkForXcode` task in an Xcode build phase.

## Testing
- Test shared logic in `commonTest` with `kotlin.test`, `kotlinx-coroutines-test`, Turbine; use fakes for platform dependencies.
- Run on every target: `./gradlew :shared:allTests`, `:shared:testDebugUnitTest`, `:shared:iosSimulatorArm64Test`. Add platform UI tests in each app (Compose tests, XCUITest). See `mobile-device-testing`.
- CI needs macOS runners for iOS targets; cache Gradle and Kotlin/Native (`~/.konan`).

## Pitfalls
- Behavior differences: string formatting, locale, floating point, threading, date and time zones. Test on both platforms.
- Binary size and build time grow; keep dependencies lean. Pin versions.
- Leaking platform types into `commonMain` breaks the model; review imports.

## Done when
Shared tests pass on JVM and iOS simulator, both apps build and run, interop API is idiomatic from Swift, size and startup checked.
