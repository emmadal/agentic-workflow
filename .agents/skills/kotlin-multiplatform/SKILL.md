---
name: kotlin-multiplatform
description: "Use when sharing Kotlin across Android, iOS, desktop or server with KMP or Compose Multiplatform: source sets, expect/actual, Ktor, Room or SQLDelight, SKIE Swift interop, all-target tests."
---
# Kotlin Multiplatform

Follows JetBrains' KMP documentation and recommended project structure. First read `gradle/libs.versions.toml` (Kotlin, AGP, Compose Multiplatform), the module layout and how iOS consumes the framework. Check versions against official docs before touching build logic.

## Rules
1. Share logic first: domain, repositories, networking, persistence, validation. Share UI with Compose Multiplatform when the team accepts one toolkit; JetBrains recommends it to keep interop small. Platform UX, permissions and hardware stay native.
2. Structure: shared code in KMP library modules using the `com.android.kotlin.multiplatform.library` plugin (`android {}` block, `androidLibrary {}` in older AGP); app entry points in their own modules (`androidApp`, `desktopApp`) plus the `iosApp` Xcode project. Use the default hierarchy template (`iosMain`, `appleMain`); do not hand-write `dependsOn` trees.
3. Platform APIs: multiplatform library first, then interface + DI, then `expect fun`. `expect class` is Beta; avoid it in new code.
4. Libraries: Ktor client, kotlinx.serialization, coroutines, kotlinx-datetime, Room KMP or SQLDelight, DataStore, androidx ViewModel and Navigation for Compose Multiplatform, Koin. Resources through Compose Multiplatform `Res`.
5. `commonMain` has no platform imports. Libraries use explicit API mode and the binary compatibility validator.
6. Swift API: export a small facade with simple types; `@Throws` on every function Swift calls that can fail (otherwise the exception crashes the app); `@ObjCName`, `@HiddenFromObjC`, `@ShouldRefineInSwift` to shape names. Bridge `suspend` and `Flow` with SKIE or KMP-NativeCoroutines. Swift export is Alpha: evaluate, do not ship on it.
7. iOS integration: `embedAndSignAppleFrameworkForXcode` for local builds, an XCFramework via Swift Package Manager for distribution. CocoaPods is being phased out; do not start new projects on it.
8. Concurrency: suspend APIs are main-safe; inject dispatchers; never block the iOS main thread.

## Test
- `commonTest`: `kotlin.test`, `runTest`, Turbine, fakes for platform interfaces. Compose Multiplatform UI: `runComposeUiTest {}`.
- Every target: `./gradlew :shared:allTests` (JVM, Android host, `iosSimulatorArm64Test`). App UI tests per platform.
- CI needs macOS for iOS targets; cache Gradle and `~/.konan`.

## Pitfalls
Missing `@Throws`; Kotlin generics, sealed classes or default arguments leaking awkwardly into Swift; platform drift in locale, time zones, number formatting; iOS framework size and link time; unpinned versions.

## Verify
Shared tests pass on JVM and iOS simulator, both apps build and run on a simulator and an emulator, Swift call sites read idiomatically, framework size checked. Depth: `references/guide.md`.
