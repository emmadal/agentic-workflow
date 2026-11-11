---
name: kotlin-android
description: "Use when writing, reviewing or testing Android code in Kotlin outside pure UI: coroutines, Flow, ViewModel, Hilt, Room, DataStore, WorkManager, permissions, R8, JUnit, Espresso. For Compose UI also load android-compose."
---
# Kotlin and Android

Follows Google's app architecture guide. Check `minSdk`, `targetSdk` and versions in `libs.versions.toml` before using an API. Kotlin 2.x (K2), KSP for code generation (Room, Hilt, Moshi); kapt only for libraries without KSP support.

## Rules
1. `val`, immutable data classes, sealed interfaces for state and results. No `!!`.
2. Coroutines: `viewModelScope`/`lifecycleScope`, never `GlobalScope`. Inject dispatchers. Rethrow `CancellationException`. `StateFlow` for UI state, `Channel` or `SharedFlow` for one-off events.
3. Collect with lifecycle awareness: `collectAsStateWithLifecycle()` or `repeatOnLifecycle(STARTED)`.
4. Architecture: UI (screen + ViewModel exposing one `UiState`), optional domain use cases, data (repositories). Room is the single source of truth. Hilt constructor injection. `SavedStateHandle` for process-death state.
5. Room: `exportSchema = true`, tested migrations, DAOs return `Flow`. DataStore, not SharedPreferences. Secrets: Android Keystore keys, Tink for encrypted files or DataStore. Jetpack Security (`EncryptedSharedPreferences`, `MasterKey`) is deprecated.
6. WorkManager for deferrable guaranteed work. Foreground services need a declared type and notification.
7. Manifest: explicit `android:exported`, minimal permissions, validated deep links, cleartext off, deliberate `allowBackup`.
8. Runtime permissions in context with rationale and denial path. Photo Picker over broad storage. Sign-in and passkeys through Credential Manager, not the legacy Google Sign-In APIs.
9. Edge-to-edge insets (enforced from `targetSdk` 35), predictive back, config change, Doze. Native libraries 16 KB page-aligned (NDK r28+ does it; Google Play requires it for apps targeting API 35+). Target the API level Play requires this year.

## Test
- Unit: `runTest`, Turbine for Flow, fakes over mocks. `./gradlew testDebugUnitTest`
- Instrumented: `./gradlew connectedDebugAndroidTest`; CI with Gradle Managed Devices.
- Lint, detekt or ktlint, StrictMode in debug, LeakCanary in debug.

## Pitfalls
Collecting Flow without lifecycle; swallowing `CancellationException`; R8 keep rules untested; blocking the main thread; exported components without permission.

## Verify
Lint and unit tests green; instrumented tests on an emulator; checked on a low-end real device. Depth in `references/guide.md`.
