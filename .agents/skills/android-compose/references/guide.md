# android-compose: detailed guide

Loaded on demand from SKILL.md. Rules here expand the checklist.

Act as a senior Android UI engineer with 10+ years, fluent in Compose since 1.0. Pair with `kotlin-android` for architecture and `mobile-engineering` for cross-platform rules.

## Composable design
- A composable describes UI for a given state; it is free of side effects and may run often and in any order.
- Take `modifier: Modifier = Modifier` as the first optional parameter and apply it to the root. Pass `Modifier` chains in order; order matters.
- Small, stateless, previewable composables. Hoist state: `value` + `onValueChange` parameters, state owned by the lowest common ancestor.
- Screen composable takes a `UiState` and event lambdas; a stateful wrapper reads the ViewModel (`collectAsStateWithLifecycle()`) and passes state down.
- Prefer slot APIs (`content: @Composable () -> Unit`) over boolean flags.

## State and recomposition
- `remember` caches across recompositions; `rememberSaveable` survives config change and process death.
- Use stable, immutable parameter types. Annotate `@Immutable`/`@Stable` only when true; use `kotlinx.collections.immutable` for lists or rely on strong skipping (Compose compiler 2.0+).
- Defer reads: pass lambdas (`{ scrollOffset }`) so only the layout or draw phase invalidates. Use `derivedStateOf` for state derived from fast-changing state.
- Lazy lists: provide stable `key`, `contentType`; never nest same-direction scrollables; avoid heavy work in item scope.
- Measure with Layout Inspector recomposition counts, composition tracing, and Macrobenchmark. Release (R8) builds only for perf conclusions.

## Side effects
- `LaunchedEffect(key)` for suspend work tied to composition, `DisposableEffect` for register and cleanup, `rememberCoroutineScope` for event-driven launches, `SideEffect` for publishing state, `rememberUpdatedState` for latest lambdas. Never launch work in the body.

## Navigation
- Navigation Compose with type-safe routes (`@Serializable` route objects, 2.8+). Navigate with events up to the NavHost; do not pass the `NavController` deep into composables. Pass ids, not objects.

## Material 3 and theming
- Wrap the app in `MaterialTheme` with color scheme, typography, shapes; support dynamic color and dark theme. Use theme tokens, not hard-coded colors or sp values.
- Window insets and edge-to-edge via `WindowInsets` and `Scaffold` padding. Adaptive layouts with window size classes for phones, foldables and tablets.

## Accessibility
- `contentDescription` on meaningful images, `semantics { }` / `Modifier.clearAndSetSemantics` for custom controls, 48dp touch targets, font scale up to 200%, TalkBack traversal order, contrast.

## Testing
- `createComposeRule()`; find nodes by semantics (`onNodeWithText`, `onNodeWithTag`, `testTag` sparingly); assert `assertIsDisplayed`, `performClick`. Use `Modifier.testTag` only when semantics are insufficient.
- Screenshot tests (Paparazzi or Roborazzi) for design-system components. Previews with `@PreviewParameter` for state variants (loading, empty, error, long text, large font, dark).
- Run on an emulator or device: `./gradlew connectedDebugAndroidTest`. See `mobile-device-testing`.

## Done when
Previews cover all states, no unnecessary recomposition on hot paths, TalkBack checked, dark and large font verified, UI tests green on an emulator.
