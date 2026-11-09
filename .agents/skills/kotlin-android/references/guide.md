# kotlin-android: detailed guide

Loaded on demand from SKILL.md. Rules here expand the checklist.

Act as a senior Android engineer with 10+ years. Read `mobile-engineering` for cross-platform rules. Check `minSdk`, `targetSdk` and library versions in the Gradle version catalog before using APIs.

## Kotlin language
- `val` over `var`; immutable data classes; sealed interfaces for state and results; `when` exhaustive on sealed types.
- Null safety: avoid `!!`; use `?.`, `?:`, `requireNotNull` with a message at boundaries.
- Coroutines: structured concurrency, `viewModelScope` / `lifecycleScope`, never `GlobalScope`. Inject dispatchers; do blocking IO on `Dispatchers.IO`. Rethrow `CancellationException`. Prefer `Flow` for streams, `StateFlow` for UI state, `SharedFlow`/`Channel` for one-off events.
- Collect lifecycle-aware: `collectAsStateWithLifecycle()` in Compose, `repeatOnLifecycle(STARTED)` in Views.

## Architecture (Google recommended)
- UI layer (screen + ViewModel exposing a single `UiState`), domain layer for reusable use cases when needed, data layer (repositories, data sources). Unidirectional data flow. Single source of truth in Room.
- DI with Hilt (or Koin). ViewModels get dependencies by constructor injection. Use `SavedStateHandle` for process-death-safe state.
- Multi-module by feature and layer for build speed and boundaries. Convention plugins and a version catalog (`libs.versions.toml`).

## Data and background
- Room with migrations and `exportSchema = true`; return `Flow` from DAOs; test migrations. DataStore replaces SharedPreferences. Secrets with Android Keystore / EncryptedFile.
- WorkManager for deferrable guaranteed work with constraints; foreground services only with declared type and notification.
- Networking: Retrofit + kotlinx.serialization or Ktor, OkHttp timeouts and interceptors, map DTOs to domain models, typed result wrapper for errors.

## Platform correctness
- Runtime permissions requested in context with rationale and denial handling. Scoped storage and Photo Picker instead of broad storage access.
- Handle configuration change and process death. Edge-to-edge insets. Predictive back. Respect battery and Doze.
- Manifest hygiene: `exported` set explicitly, minimal permissions, deep links validated, `android:allowBackup` decided deliberately, cleartext traffic off.

## Quality
- Static analysis: ktlint/detekt, Android Lint, StrictMode in debug. R8 shrinking and obfuscation on for release with tested keep rules.
- Performance: Baseline Profiles and Macrobenchmark for startup and jank; Android Studio Profiler; LeakCanary in debug.

## Testing
- Unit: JUnit5/JUnit4, `kotlinx-coroutines-test` (`runTest`, `StandardTestDispatcher`), Turbine for Flow, MockK or fakes.
- Instrumented/UI: Espresso for Views, Compose test APIs for Compose, Hilt test rules. Run `./gradlew testDebugUnitTest` and `./gradlew connectedDebugAndroidTest`; use Gradle Managed Devices for CI. See `mobile-device-testing`.

## Release
- App Bundle (AAB), Play App Signing, staged rollout, Android vitals (crash and ANR rate), mapping file uploaded for deobfuscation, data safety form current.

## Done when
Lint and unit tests green, instrumented tests run on an emulator, checked on a real low-end device, manifest and permissions reviewed.
