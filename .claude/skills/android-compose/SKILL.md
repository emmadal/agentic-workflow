---
name: android-compose
description: "Use when building or reviewing Jetpack Compose or Compose Multiplatform UI: state hoisting, recomposition, Material 3, type-safe navigation, lists, side effects, accessibility, previews, Compose UI tests."
---
# Jetpack Compose

## Rules
1. A composable renders state and has no side effects. It may run often, in any order.
2. `modifier: Modifier = Modifier` is the first optional parameter, applied to the root. Modifier order matters.
3. Hoist state: `value` + `onValueChange`. A stateful wrapper reads the ViewModel (`collectAsStateWithLifecycle()`); the screen composable takes `UiState` and event lambdas.
4. `remember` survives recomposition; `rememberSaveable` survives config change and process death.
5. Stable params only: immutable types, immutable collections, or strong skipping (Compose compiler 2.0+).
6. Defer reads: pass lambdas (`{ offset }`) so only layout or draw invalidates. `derivedStateOf` for state derived from fast-changing state.
7. Lazy lists: stable `key` and `contentType`. Never nest same-direction scrollables.
8. Effects: `LaunchedEffect(key)` for suspend work, `DisposableEffect` for cleanup, `rememberCoroutineScope` for event launches, `rememberUpdatedState` for latest lambdas. Never launch work in the body.
9. Navigation: type-safe `@Serializable` routes. Pass ids, not objects. Events go up to the NavHost; do not pass `NavController` down.
10. Theme tokens only: `MaterialTheme` colors, typography, shapes. Support dark and dynamic color. Adaptive layout via window size classes.
11. Semantics: `contentDescription`, 48dp targets, font scale to 200%, TalkBack order.

## Test
- `createComposeRule()`, find by semantics (`onNodeWithText`), `testTag` only as fallback. Screenshot tests with Paparazzi or Roborazzi.
- Previews cover loading, empty, error, long text, large font, dark.
- Run: `./gradlew connectedDebugAndroidTest`.

## Pitfalls
Unstable lambdas or lists causing recomposition; state read too high in the tree; side effect in composition; hard-coded colors.

## Verify
Previews for every state, no hot-path recomposition (Layout Inspector counts, release build), TalkBack and 200% font checked, UI tests green on an emulator. Depth: `references/guide.md`.
