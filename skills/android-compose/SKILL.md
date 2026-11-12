---
name: android-compose
description: "Use when building or reviewing Jetpack Compose or Compose Multiplatform UI: state hoisting, recomposition, stability, Material 3, Navigation 3, window size classes, side effects, accessibility, UI/screenshot tests."
---
# Jetpack Compose

Follows the androidx Compose API guidelines and the Now in Android architecture. First read the Compose BOM, Kotlin version (strong skipping is on from 2.0.20), navigation library and `targetSdk`.

## Rules
1. A composable emits UI from state, has no side effects, and may run often, in any order. PascalCase for UI emitters; `remember*` factories for state holders.
2. `modifier: Modifier = Modifier` is the first optional parameter, applied once to the root. Slot lambdas over boolean flags.
3. Screen pattern: a stateful route reads the ViewModel (`collectAsStateWithLifecycle()`), a stateless `Screen(uiState, onAction)` renders. `UiState` is a sealed interface built with `stateIn(viewModelScope, WhileSubscribed(5_000), Loading)`. Never pass a ViewModel or `NavController` to leaf composables.
4. Hoist state to the lowest common owner. `rememberSaveable` for user input; plain state holder classes for complex UI logic; `derivedStateOf` only when the output changes less often than the input.
5. Stability: prefer immutable params and immutable collections; a stability config file for external types. Defer fast reads into lambda modifiers (`offset {}`, `graphicsLayer {}`, `drawBehind {}`).
6. Lazy lists: stable `key` and `contentType`. Never nest same-direction scrollables.
7. Effects: `LaunchedEffect(key)` for suspend work, `DisposableEffect` for cleanup, `rememberCoroutineScope` for event launches, `rememberUpdatedState` for latest lambdas.
8. Navigation: Navigation 3 (`NavDisplay`, a back stack you own) for new apps; Navigation 2.8+ `@Serializable` routes otherwise. Pass ids, not objects. Support predictive back.
9. Adaptive and edge-to-edge: window size classes, `NavigationSuiteScaffold`, `ListDetailPaneScaffold`; `enableEdgeToEdge()` and insets (enforced from `targetSdk` 35).
10. Material 3 tokens only (`MaterialTheme` color, type, shape), dark and dynamic color.
11. Accessibility: `contentDescription`, `semantics { role; stateDescription }`, `mergeDescendants`, 48dp targets, font scale 200%, TalkBack order.

## Test
- `createComposeRule()`; find by semantics (`onNodeWithText`, `onNodeWithContentDescription`), `testTag` as fallback; `mainClock.autoAdvance = false` for animations. Robolectric for fast JVM UI tests.
- Screenshot tests: Compose Preview Screenshot Testing, Roborazzi or Paparazzi, from multipreviews (`@PreviewLightDark`, `@PreviewFontScale`, `@PreviewScreenSizes`).
- Lint with Android lint and compose-rules. `./gradlew testDebugUnitTest connectedDebugAndroidTest`.

## Pitfalls
State read high in the tree; unstable lambdas or `List` params; side effects in composition; hard-coded colors and dp text; judging jank in debug builds.

## Verify
Previews for every state, screenshot tests current, recomposition counts checked in Layout Inspector, scrolling and startup measured in a release build with a baseline profile, TalkBack and 200% font verified, UI tests green on an emulator. Depth: `references/guide.md`.
