---
name: kotlin-android
description: "Use when writing, reviewing or testing Android code in Kotlin outside pure UI: coroutines, Flow, ViewModel, Hilt, Room, DataStore, WorkManager, permissions, R8, JUnit, Espresso. For Compose UI also load android-compose."
---
# Kotlin and Android

Check `minSdk`, `targetSdk` and versions in `libs.versions.toml` before using an API.

## Rules
1. `val`, immutable data classes, sealed interfaces for state and results. No `!!`.
2. Coroutines: `viewModelScope`/`lifecycleScope`, never `GlobalScope`. Inject dispatchers. Rethrow `CancellationException`. `StateFlow` for UI state, `Channel` or `SharedFlow` for one-off events.
3. Collect with lifecycle awareness: `collectAsStateWithLifecycle()` or `repeatOnLifecycle(STARTED)`.
4. Architecture: UI (screen + ViewModel exposing one `UiState`), optional domain use cases, data (repositories). Room is the single source of truth. Hilt constructor injection. `SavedStateHandle` for process-death state.
5. Room: `exportSchema = true`, tested migrations, DAOs return `Flow`. DataStore, not SharedPreferences. Secrets via Keystore.
6. WorkManager for deferrable guaranteed work. Foreground services need a declared type and notification.
7. Manifest: explicit `android:exported`, minimal permissions, validated deep links, cleartext off, deliberate `allowBackup`.
8. Runtime permissions in context with rationale and denial path. Photo Picker over broad storage.
9. Edge-to-edge insets, predictive back, config change, Doze.

## Test
- Unit: `runTest`, Turbine for Flow, fakes over mocks. `./gradlew testDebugUnitTest`
- Instrumented: `./gradlew connectedDebugAndroidTest`; CI with Gradle Managed Devices.
- Lint, detekt or ktlint, StrictMode in debug, LeakCanary in debug.

## Pitfalls
Collecting Flow without lifecycle; swallowing `CancellationException`; R8 keep rules untested; blocking the main thread; exported components without permission.

## Verify
Lint and unit tests green; instrumented tests on an emulator; checked on a low-end real device. Depth in `references/guide.md`.
