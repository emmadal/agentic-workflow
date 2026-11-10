# expo: Expo UI (`@expo/ui`)

Verified against SDK 58 docs: `docs.expo.dev/versions/latest/sdk/ui.md` (append `.md` to any URL for agent-readable docs; full map at `docs.expo.dev/llms.txt`).

## What it is
- Not another design system: Expo UI exposes real **Jetpack Compose** (Android) and **SwiftUI** (iOS) primitives to JavaScript, one-to-one with their native counterparts.
- Component-level integration: write an entire app with it or adopt one screen at a time. Mix React Native components, DOM components, and Skia drawing in the same tree.
- Platforms: Android, iOS, tvOS; included in Expo Go. Install with `npx expo install @expo/ui`.

## Choose the import
- `@expo/ui/universal` — one component tree for Android, iOS **and web**. Default choice.
- `@expo/ui/swift-ui` — iOS only (SwiftUI does not exist on Android/web).
- `@expo/ui/jetpack-compose` — Android only, Material 3.
- Drop-in replacements — API-compatible swaps for community libs: BottomSheet (`@gorhom/bottom-sheet`), DateTimePicker, MaskedView, Menu, PagerView, Picker, SegmentedControl, Slider.

## The `Host` bridge
- Every Expo UI component must be wrapped in `Host`; it is the bridge to the native toolkit (like `<svg>` or Skia's `<Canvas>`). Cross-platform `Host` in `universal/`.
- Flexbox applies to `Host` itself only. Inside the native context Yoga is unavailable: lay out with `Row`/`Column` (Compose) or `HStack`/`VStack` (SwiftUI).
- `RNHostView` embeds React Native views back inside the native tree; to add Expo UI components again after React Native, introduce a new `Host`.
- React Native components can be JSX children of Expo UI components (auto `UIViewRepresentable`), but SwiftUI controls `center`, `bounds`, `frame`, `transform` — keep boundaries clean and layouts self-contained.

## Key APIs
- `useNativeState()` — observable state shared between JS and the native side.
- `Modifiers` — per-platform modifiers for appearance/behavior.
- Universal set covers: BottomSheet, Button, Checkbox, Collapsible, Column/Row, FieldGroup, Host, Icon (SF Symbols / Material Symbols), List + ListItem, Picker, RNHostView, ScrollView, Slider, Spacer, Switch, Text, TextInput.
- Custom components: extend the toolkit via the docs pages "Custom SwiftUI components" and "Custom Jetpack Compose components".
- Material 3 colors (incl. dynamic color) readable from JS on Android.

## Catalog
Browse per-component docs under `docs.expo.dev/versions/latest/sdk/ui/jetpack-compose.md`, `.../swift-ui.md`, `.../universal.md` (Button, Form, List, NavigationStack/SplitView, TabView, TopAppBar, LazyColumn/LazyRow, ModalBottomSheet, SearchBar, and many more). Examples: `github.com/expo/expo/tree/main/apps/native-component-list/src/screens/UI` and the `expo/hot-chocolate` demo.

## Pitfalls
Using `swift-ui` on Android or web; expecting flexbox inside `Host`; fighting SwiftUI layout from React props; reaching for platform imports when the universal set suffices.
