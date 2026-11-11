---
name: flutter
description: "Use when writing, reviewing or testing Flutter or Dart app code: widgets, MVVM with ChangeNotifier, Riverpod or Bloc, go_router, Pigeon platform channels, flavors, jank, widget, golden and integration_test tests."
---
# Flutter and Dart

Follows the Flutter team's app architecture guide and Effective Dart. First read `pubspec.yaml` (SDK constraints), `analysis_options.yaml`, `flutter --version` and the state management already in use. Keep the project's choice; do not mix a second one.

## Rules
1. `flutter analyze` clean with `flutter_lints` or stricter. `dart format`. Sound null safety: no `!` on unchecked values. Immutable models (`final` fields, `copyWith`, value equality or `freezed`). Dart 3 `sealed` classes and `switch` expressions for state and results.
2. Layers: UI = view (widget) + view model (`ChangeNotifier`); data = repositories (abstract class, source of truth) + services (HTTP, plugins). Data flows one way. No logic in widgets.
3. User actions go through commands that expose running, error and completed; disable the button while running. Return `Result<T>` across layers instead of throwing. Inject dependencies (`provider`, or the project's Riverpod or Bloc).
4. Widgets: small classes, not helper methods; `const` constructors; `Key`s for reorderable or stateful list items; `ListView.builder` or slivers for long lists. `build` stays pure and cheap: never create futures, controllers or streams in it.
5. Async: check `context.mounted` after every `await` before using `BuildContext`. Dispose controllers, cancel subscriptions and timers. Parsing or work over ~8 ms goes to `Isolate.run`.
6. Navigation: `go_router` with typed routes, `redirect` for auth, deep links tested.
7. Platform code: Pigeon for type-safe channels, `dart:ffi` for C. Adaptive UI with `LayoutBuilder`, `MediaQuery.sizeOf`, `SafeArea`; platform conventions on iOS and Android.
8. Theme: Material 3 `ColorScheme.fromSeed`, `Theme.of(context)` tokens, dark mode; `flutter gen-l10n` with ARB files, no string concatenation.
9. Accessibility: `Semantics` and `tooltip` labels, 48x48 targets, text scaling to 200%, contrast.
10. Secrets: `flutter_secure_storage`, never `shared_preferences` or `--dart-define`. Release builds use `--obfuscate --split-debug-info`.

## Test
- Unit: `test` + `mocktail` fakes. Widget: `testWidgets`, `pumpWidget`, find by key, text or semantics label, `pump` over `pumpAndSettle` for endless animations.
- Golden: `matchesGoldenFile` with bundled fonts, generated on one OS in CI.
- Device: `flutter test integration_test -d <device>`. `flutter test --coverage`.
- Gate: `flutter analyze && dart format --set-exit-if-changed . && flutter test`.

## Pitfalls
`setState` after dispose; `BuildContext` across async gaps; `shrinkWrap: true` on long lists; `Opacity` or clips inside animations; judging performance in debug mode.

## Verify
Analyzer and tests green; frame times checked in `--profile` mode on a real device with DevTools; run on an iOS simulator and an Android emulator. Code examples, folder layout, flavors, Pigeon and release steps: `references/guide.md`.
