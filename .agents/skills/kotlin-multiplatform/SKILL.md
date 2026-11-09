---
name: kotlin-multiplatform
description: "Use when sharing Kotlin across Android, iOS, desktop or server with KMP or Compose Multiplatform: source sets, expect/actual, Ktor, SQLDelight or Room KMP, Koin, Swift interop, testing on every target."
---
# Kotlin Multiplatform

Check current Kotlin, KMP and Compose Multiplatform versions in the version catalog and official docs before touching build logic.

## Rules
1. Share logic first (domain, use cases, repositories, networking, persistence, validation). Share UI (Compose Multiplatform) only if the team accepts one toolkit. Platform UX, permissions and hardware stay native.
2. `shared` module: `commonMain`, `androidMain`, `iosMain`, tests per source set. Keep platform code thin.
3. Prefer interfaces plus DI over `expect/actual`. Use `expect/actual` for small primitives (UUID, clock, secure storage, logging).
4. Multiplatform libraries only: Ktor (OkHttp on Android, Darwin on iOS), kotlinx.serialization, coroutines, kotlinx-datetime, SQLDelight or Room KMP, Koin.
5. No platform types in `commonMain`. Review imports.
6. iOS interop: export a small API with simple types. Bridge `suspend` and `Flow` with SKIE or KMP-NativeCoroutines. Watch retain cycles across the boundary.
7. Ship iOS as an XCFramework via SwiftPM or Gradle `embedAndSignAppleFrameworkForXcode`.

## Test
- Shared logic in `commonTest`: `kotlin.test`, `runTest`, Turbine, fakes for platform deps.
- Run every target: `./gradlew :shared:allTests`, `:shared:iosSimulatorArm64Test`. Add app-level UI tests per platform. CI needs macOS for iOS targets; cache `~/.konan`.

## Pitfalls
Behavior drift between platforms (locale, formatting, threading, time zones); leaking Kotlin generics into Swift; binary size and build time growth; unpinned versions.

## Verify
Shared tests pass on JVM and iOS simulator, both apps build and run on a simulator and an emulator, the Swift call sites look idiomatic. Depth: `references/guide.md`.
