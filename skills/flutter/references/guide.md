# flutter: detailed guide

Loaded on demand from SKILL.md. Source: Flutter team app architecture guide (docs.flutter.dev/app-architecture), Effective Dart, Flutter performance and testing docs. Re-check versions in `pubspec.yaml` before using an API.

## Folder layout (Flutter architecture case study)

```
lib/
  config/            dependency wiring, environment
  routing/           go_router config, typed routes
  ui/
    core/            theme, shared widgets
    <feature>/
      view_models/   <feature>_view_model.dart
      widgets/       <feature>_screen.dart and parts
  domain/models/     immutable models used by the UI
  data/
    repositories/    abstract + implementations (source of truth)
    services/        API clients, platform plugins, local DB
    model/           API and DB transfer objects
  utils/             result.dart, command.dart
test/                mirrors lib/
testing/fakes/       fake repositories and services shared by tests
integration_test/
```

## Result and Command

```dart
sealed class Result<T> {
  const Result();
  const factory Result.ok(T value) = Ok<T>;
  const factory Result.error(Exception error) = Error<T>;
}
final class Ok<T> extends Result<T> { const Ok(this.value); final T value; }
final class Error<T> extends Result<T> { const Error(this.error); final Exception error; }
```

A command wraps one async action, exposes `running`, `error`, `completed`, and refuses to start again while running (prevents double taps). Use `Command0` for no argument and `Command1<T, A>` for one argument, as in the Flutter docs' command pattern.

## View model and view

```dart
class BookingViewModel extends ChangeNotifier {
  BookingViewModel({required BookingRepository repository}) : _repository = repository {
    load = Command0(_load)..execute();
    cancel = Command1<void, String>(_cancel);
  }
  final BookingRepository _repository;
  late final Command0<void> load;
  late final Command1<void, String> cancel;

  List<Booking> _bookings = const [];
  List<Booking> get bookings => _bookings;

  Future<Result<void>> _load() async {
    final result = await _repository.getBookings();
    switch (result) {
      case Ok(:final value): _bookings = value;
      case Error(): break; // command exposes the error to the view
    }
    notifyListeners();
    return result;
  }

  Future<Result<void>> _cancel(String id) async { /* ... */ }
}
```

The screen listens with `ListenableBuilder(listenable: viewModel.load, builder: ...)`: running shows a spinner, error shows retry (`viewModel.load.execute`), completed shows data. Widgets call commands; they never call repositories.

## Repositories and services
- Repository = single source of truth per data type; caches, merges local and remote, retries with backoff for idempotent calls, maps transfer objects to domain models.
- Service = thin wrapper around one external source (HTTP, `shared_preferences`, a plugin). No business logic. Easy to fake.
- Abstract repository classes so tests and flavors swap implementations: `BookingRepositoryRemote`, `BookingRepositoryLocal`, `FakeBookingRepository`.

## Dependency injection
`MultiProvider` at the root with `Provider<ApiClient>`, `ChangeNotifierProvider`, or Riverpod `Provider`s. Create view models in the route builder, passing repositories from `context.read<T>()`. No global singletons.

## State management choice
| Project already uses | Keep it |
|---|---|
| nothing (new app) | `ChangeNotifier` + `provider` per the Flutter guide; Riverpod 3 if the team knows it |
| Riverpod | `Notifier`/`AsyncNotifier`, `ref.watch` in build, `ref.read` in callbacks |
| Bloc | events in, states out, `BlocBuilder`/`BlocListener`, `bloc_test` |

## Navigation (go_router)
- One `GoRouter` with `redirect` for auth, `refreshListenable` bound to the auth repository.
- Typed routes via `go_router_builder` (`@TypedGoRoute`) so parameters are compile-checked.
- `StatefulShellRoute.indexedStack` for bottom navigation that keeps tab state.
- Test deep links: `xcrun simctl openurl booted myapp://path`, `adb shell am start -a android.intent.action.VIEW -d "myapp://path"`.

## Platform integration
- Pigeon: define the API in a Dart file, generate Dart, Kotlin and Swift; never hand-write `MethodChannel` string protocols for new code.
- Permissions: `Info.plist` usage strings and `AndroidManifest.xml` entries for each plugin; handle denial and "don't ask again".
- Platform views (maps, web views) cost performance; use hybrid composition only where needed.

## Performance (profile mode on a real device)
- `flutter run --profile`, DevTools Performance view; frame budget 16 ms at 60 Hz, 8 ms at 120 Hz. Impeller is the default renderer on iOS and Android.
- Rebuild less: `const` widgets, split widgets so `setState` touches a small subtree, `ValueListenableBuilder` or `select` for narrow listening.
- Avoid `saveLayer`: `Opacity` (use `FadeTransition` or color alpha), `ShaderMask`, `ClipRRect` in animated subtrees. `RepaintBoundary` around independently animating regions, measured not guessed.
- Images: `cacheWidth`/`cacheHeight`, precache hero images, correct resolution variants.
- Startup: defer heavy init until after first frame; measure with `flutter run --trace-startup --profile`.
- App size: `flutter build apk --analyze-size`, deferred components on Android.

## Testing details
- Widget test pumps the screen with fake repositories: `pumpWidget(MultiProvider(providers: [...fakes], child: MaterialApp(home: Screen(viewModel: vm))))`.
- Find by `find.byKey(const ValueKey('save'))`, `find.bySemanticsLabel('Save')`, `find.text`. Prefer semantics so tests also cover accessibility.
- Accessibility guidelines in widget tests: `await expectLater(tester, meetsGuideline(androidTapTargetGuideline));` plus `textContrastGuideline` and `labeledTapTargetGuideline`.
- Golden tests: load bundled fonts with `FontLoader` in `test/flutter_test_config.dart` (otherwise text renders as boxes), fix `tester.view.physicalSize` and `devicePixelRatio`, update with `flutter test --update-goldens`, and generate goldens on one OS because font rasterization differs.
- Integration tests: `IntegrationTestWidgetsFlutterBinding.ensureInitialized()`, run on emulator and simulator in CI (Firebase Test Lab for device coverage).

## Flavors and configuration
- `flutter run --flavor staging -t lib/main_staging.dart --dart-define-from-file=config/staging.json`.
- Android `productFlavors`, iOS schemes and xcconfigs per flavor; different bundle IDs and app names.
- Config is not secret: anything in the binary can be extracted.

## Release
- Android: `flutter build appbundle --release --obfuscate --split-debug-info=build/symbols`, upload symbols to the crash reporter, staged rollout on Play.
- iOS: `flutter build ipa --release --obfuscate --split-debug-info=build/symbols`, upload dSYMs, TestFlight then phased release.
- Keep `version: x.y.z+build` in `pubspec.yaml` monotonic.

## Done when
`flutter analyze` and `flutter test` green, goldens current, integration tests pass on an emulator and a simulator, profile-mode frame times within budget on a real low-end device, accessibility guideline tests pass.
