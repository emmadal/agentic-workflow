# kotlin-multiplatform: detailed guide

Loaded on demand from SKILL.md. Sources: kotlinlang.org multiplatform docs (JetBrains), the recommended project structure guide, Kotlin/Native Objective-C and Swift interop docs, developer.android.com KMP pages. Pair with `kotlin-android`, `android-compose` and `swift-ios`.

## Recommended structure

```
androidApp/          Android application module (entry point only)
desktopApp/          optional JVM desktop entry point
iosApp/              Xcode project (entry point, SwiftUI or Compose host)
shared/              KMP library: commonMain, androidMain, iosMain, jvmMain, tests
feature-*/           optional KMP feature modules as the code base grows
build-logic/         convention plugins
gradle/libs.versions.toml
```

Shared library build file:

```kotlin
plugins {
    alias(libs.plugins.kotlinMultiplatform)
    alias(libs.plugins.androidMultiplatformLibrary)   // com.android.kotlin.multiplatform.library
    alias(libs.plugins.composeMultiplatform)          // only when sharing UI
    alias(libs.plugins.composeCompiler)
}

kotlin {
    android {                       // `androidLibrary {}` on older AGP versions
        namespace = "com.example.shared"
        compileSdk = libs.versions.android.compileSdk.get().toInt()
        minSdk = libs.versions.android.minSdk.get().toInt()
        withHostTest {}             // opt-in: src/androidHostTest
        withDeviceTest {}           // opt-in: src/androidDeviceTest
    }
    listOf(iosArm64(), iosSimulatorArm64()).forEach {
        it.binaries.framework { baseName = "Shared"; isStatic = true }
    }
    jvm()
    sourceSets {
        commonMain.dependencies { /* ktor, serialization, coroutines, koin */ }
        commonTest.dependencies { implementation(kotlin("test")) }
        androidMain.dependencies { implementation(libs.ktor.client.okhttp) }
        iosMain.dependencies { implementation(libs.ktor.client.darwin) }
    }
}
```

The older `androidTarget()` + `com.android.library` setup still works; migrate when touching build logic. The default hierarchy template creates `iosMain`, `appleMain`, `nativeMain` automatically.

## Platform APIs, in order of preference
1. A multiplatform library (Ktor, DataStore, Room KMP, kotlinx-datetime).
2. An interface in `commonMain`, implemented in `androidMain` and `iosMain` (or in Swift) and wired with DI:
   ```kotlin
   interface SecureStore { fun put(key: String, value: String); fun get(key: String): String? }
   // androidMain: Android Keystore key + Tink (EncryptedSharedPreferences is deprecated); iosMain: Keychain via platform.Security
   ```
3. `expect fun` / `expect val` for tiny primitives (UUID, platform name, clock source).
4. `expect class` only when unavoidable (Beta).

## Data and state
- Networking: one `HttpClient` with `ContentNegotiation` (kotlinx.serialization JSON), `HttpTimeout`, retry for idempotent calls, logging off in release.
- Persistence: Room KMP (`androidx.room` with the KSP plugin and `BundledSQLiteDriver`) or SQLDelight (SQL-first, typesafe queries, migrations as `.sqm` files). Test migrations.
- State: androidx `ViewModel` and `viewModelScope` work in common code; expose `StateFlow<UiState>`.
- DI: Koin modules per layer; platform modules supply implementations.
- Compose Multiplatform resources: files under `composeResources/` accessed as `Res.string.title`, `Res.drawable.logo`; localization through `values-<locale>` folders.

## Swift interop
- The Kotlin compiler produces an Objective-C framework today. Design the exported surface:
  - Keep it small: a facade per feature, simple types, no Kotlin collections of generics in signatures when avoidable.
  - `@Throws(CancellationException::class, IOException::class)` on suspend and failing functions called from Swift; unchecked Kotlin exceptions crash the app.
  - `@ObjCName("Session")` for Swift-friendly names, `@HiddenFromObjC` for internals, `@ShouldRefineInSwift` when you wrap an API in a Swift extension.
  - Sealed classes and enums map poorly without SKIE (exhaustive Swift `switch` needs it).
- Coroutines: SKIE turns `Flow` into `AsyncSequence` and suspend functions into `async`, with cancellation, and needs no Swift dependency (check SKIE's supported Kotlin version before upgrading Kotlin). KMP-NativeCoroutines is the alternative with async/await, Combine and RxSwift support.
- Swift export (Alpha) generates Swift directly without the Objective-C layer. Try it in a branch; keep production on the Objective-C bridge until it is stable.
- Memory: the Kotlin/Native memory manager is garbage collected; avoid retain cycles between Swift closures and Kotlin objects (use `[weak self]` in Swift callbacks).

## iOS integration
- Local development: Xcode run-script phase `./gradlew :shared:embedAndSignAppleFrameworkForXcode`.
- Distribution to a separate iOS repo: build an XCFramework (`assembleSharedXCFramework` or KMMBridge) and publish it as a Swift Package binary target.
- Importing Swift packages into Kotlin: the Swift Package Manager import support in the Kotlin Gradle plugin, or wrap them on the Swift side behind a Kotlin interface.
- CocoaPods integration is legacy; migrate existing projects when convenient.

## Testing
- `commonTest` for logic: `runTest`, `TestScope`, `StandardTestDispatcher` injected; Turbine for Flow; fakes implement the platform interfaces.
- Platform tests in `androidHostTest` / `androidDeviceTest` (KMP library plugin, opt in with `withHostTest {}` / `withDeviceTest {}`) or `androidUnitTest` / `androidInstrumentedTest` (legacy setup), and `iosTest`.
- Compose Multiplatform UI tests in `commonTest`:
  ```kotlin
  @OptIn(ExperimentalTestApi::class)
  @Test fun showsTitle() = runComposeUiTest {
      setContent { GreetingScreen(title = "Hi") }
      onNodeWithText("Hi").assertExists()
  }
  ```
- Commands: `./gradlew :shared:allTests`, `:shared:jvmTest`, `:shared:iosSimulatorArm64Test`; iOS app tests with `xcodebuild test`.

## Build performance
- Gradle configuration cache and build cache on; Kotlin/Native caches in `~/.konan` cached on CI.
- Only enable targets you ship. Debug iOS builds link one architecture (simulator arm64 on Apple silicon).
- Watch framework size: `isStatic = true`, avoid large transitive dependencies, strip unused code with release linking.

## Pitfalls
- Locale, time zone, `Double` formatting and string comparison differ between JVM and Native; test on both.
- `Dispatchers.Main` in tests needs `Dispatchers.setMain`; on iOS the main dispatcher is the main queue.
- Mixed Kotlin, AGP and Compose Multiplatform versions break builds; upgrade them together using the compatibility table.

## Done when
Shared tests pass on JVM and iOS simulator, both apps build and run, the Swift API reads idiomatically (`@Throws` everywhere it should be), framework size and startup checked.
