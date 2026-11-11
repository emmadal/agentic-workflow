# android-compose: detailed guide

Loaded on demand from SKILL.md. Sources: androidx Compose API guidelines, developer.android.com Compose docs (performance, stability, navigation, adaptive, testing), Now in Android sample. Pair with `kotlin-android` for data and DI.

## Screen pattern (Now in Android)

```kotlin
@HiltViewModel
class TopicViewModel @Inject constructor(
    savedStateHandle: SavedStateHandle,
    repository: TopicsRepository,
) : ViewModel() {
    private val topicId = savedStateHandle.toRoute<TopicRoute>().id
    val uiState: StateFlow<TopicUiState> = repository.observe(topicId)
        .map<Topic, TopicUiState>(TopicUiState::Success)
        .catch { emit(TopicUiState.Error) }
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), TopicUiState.Loading)

    fun onFollow(followed: Boolean) = viewModelScope.launch { repository.setFollowed(topicId, followed) }
}

sealed interface TopicUiState {
    data object Loading : TopicUiState
    data object Error : TopicUiState
    data class Success(val topic: Topic) : TopicUiState
}

@Composable
fun TopicRoute(onBack: () -> Unit, viewModel: TopicViewModel = hiltViewModel()) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()
    TopicScreen(uiState = uiState, onFollow = viewModel::onFollow, onBack = onBack)
}

@Composable
internal fun TopicScreen(
    uiState: TopicUiState,
    onFollow: (Boolean) -> Unit,
    onBack: () -> Unit,
    modifier: Modifier = Modifier,
) { /* stateless, previewable, testable */ }
```

## API guidelines (androidx)
- Composables that emit UI return `Unit`, are PascalCase nouns, take `modifier` once and apply it to the root.
- Parameter order: required params, `modifier`, optional params, trailing `content` slot.
- Do not expose `MutableState` parameters; take value + callback. Do not take `Flow` or `LiveData` params in reusable components.
- State holders: `class FooState` + `@Composable fun rememberFooState(...)` that uses `rememberSaveable` with a `Saver` when the state must survive process death.
- Default values come from a `FooDefaults` object, not hard-coded inside the composable.

## Recomposition and stability
- Strong skipping (default from Kotlin 2.0.20): composables with unstable params can still skip when instances are equal by reference, and lambdas are remembered automatically. Stability still matters: a new `List` instance every emission defeats skipping.
- Make UI models immutable `data class` with `kotlinx.collections.immutable` (`ImmutableList`), or annotate `@Immutable` when true.
- Stability config file for types from modules without the Compose compiler:
  ```kotlin
  composeCompiler { stabilityConfigurationFile = rootProject.layout.projectDirectory.file("stability_config.conf") }
  ```
- Investigate with Layout Inspector recomposition counts and Compose compiler reports (`reportsDestination`, `metricsDestination`). Fix with deferred reads:
  ```kotlin
  Box(Modifier.offset { IntOffset(0, scrollState.value / 2) })   // layout phase only
  Box(Modifier.graphicsLayer { alpha = progress() })              // draw phase only
  ```
- `derivedStateOf { listState.firstVisibleItemIndex > 0 }` for a boolean derived from a fast-changing value.

## Performance in production
- Measure release builds with R8. Baseline Profiles (`androidx.baselineprofile` plugin) for startup and critical scrolling; Macrobenchmark for startup and frame timing (`FrameTimingMetric`).
- Lazy lists: `key = { it.id }`, `contentType = { it.type }`, no heavy work in item scope, images sized with Coil `size`.
- Avoid `SubcomposeLayout`-heavy patterns and `BoxWithConstraints` in list items.

## Side effects
| Need | API |
|---|---|
| Suspend work keyed to state | `LaunchedEffect(key)` |
| Register and unregister | `DisposableEffect(key) { onDispose { } }` |
| Launch from a click | `rememberCoroutineScope()` |
| Long-lived effect, latest callback | `rememberUpdatedState(onTimeout)` |
| Compose state to Flow | `snapshotFlow { state.value }` |
| Publish to non-Compose code each commit | `SideEffect` |

## Navigation
- Navigation 3: the back stack is state you own (`rememberNavBackStack(Home)`), `NavDisplay(backStack, entryProvider = entryProvider { entry<Home> { ... } })`. Add with `backStack.add(Detail(id))`, pop with `removeLastOrNull()`. Scenes support list-detail and adaptive layouts; `rememberViewModelStoreNavEntryDecorator` scopes ViewModels to entries.
- Navigation 2.8+: `@Serializable data class Detail(val id: String)`, `composable<Detail> { backStackEntry -> backStackEntry.toRoute<Detail>() }`, `navController.navigate(Detail(id))`.
- Either way: events go up to the host; pass ids and load from the repository; test predictive back (`enableOnBackInvokedCallback`).

## Adaptive layouts and insets
- `currentWindowAdaptiveInfo().windowSizeClass` drives layout; never branch on device type.
- `NavigationSuiteScaffold` switches bottom bar, rail and drawer; `ListDetailPaneScaffold` and `SupportingPaneScaffold` for two-pane.
- Edge-to-edge is enforced when targeting SDK 35: call `enableEdgeToEdge()`, use `Scaffold` content padding or `WindowInsets.safeDrawing`, and `imePadding()` for forms. Test with gesture and 3-button navigation.
- Foldables: hinge-aware layouts via `WindowInfoTracker` when relevant.

## Theming
- `MaterialTheme(colorScheme, typography, shapes)`; dynamic color on Android 12+ with a branded fallback; light and dark schemes generated from the design tokens.
- Text sizes in `sp` via typography; spacing in `dp` from a dimens object; no raw hex colors in features.

## Accessibility
- Images: `contentDescription`, or `null` for decoration. Icon buttons need a label.
- `Modifier.semantics(mergeDescendants = true) {}` for cards read as one item; `clearAndSetSemantics` for custom controls with `role`, `stateDescription`, `onClick(label = ...)`.
- `minimumInteractiveComponentSize()` (48dp), `traversalIndex` for reading order, `heading()` for section titles, `liveRegion` for status changes.
- Android 14 non-linear font scaling up to 200%: test with `@PreviewFontScale` and on device.

## Testing
- Compose tests: `composeTestRule.setContent { TopicScreen(uiState = TopicUiState.Success(fake), onFollow = {}, onBack = {}) }`, then `onNodeWithText("Follow").performClick()` and assert callbacks or state.
- `useUnmergedTree = true` when asserting children of merged nodes; `waitUntil { }` for async; `mainClock.advanceTimeBy()` for animations.
- Run Compose tests on the JVM with Robolectric (`@RunWith(AndroidJUnit4::class)` + `@Config`) for speed; keep a smaller instrumented suite.
- Screenshot testing: Compose Preview Screenshot Testing plugin (`updateDebugScreenshotTest`, `validateDebugScreenshotTest`) or Roborazzi (`recordRoborazziDebug`, `verifyRoborazziDebug`). Cover light, dark, font scale and screen sizes.
- Accessibility checks: enable the Accessibility Test Framework in Compose UI tests where available (`enableAccessibilityChecks()`), plus Accessibility Scanner on device.

## Lint
- Android lint with `warningsAsErrors` on CI, compose-rules for detekt or ktlint (modifier order, naming, unstable collections, `remember` misuse).

## Done when
Previews and screenshot tests cover loading, empty, error, long text, large font, dark and wide screens; no avoidable recomposition on hot paths; baseline profile in place; TalkBack and 200% font verified; UI tests green on an emulator.
