# figma-to-expo: Figma to Expo mapping

Target the latest stable Expo SDK and the React Native it pins (version policy in the `expo` skill). Last verified Nov 2026 on SDK 58 (`docs.expo.dev/versions/latest/sdk/ui/universal.md`) and React Native 0.88 style props. On a newer SDK, re-check changed components and props in `docs.expo.dev/versions/latest` before relying on this table; on an older one, in that SDK's docs. The `@expo/ui` root import, `List.ForEach` and `useNativeState` need SDK 58 or later.

Install what the screens need with `npx expo install` (never hand-pinned versions): `@expo/ui`, `expo-image`, `expo-font`, `react-native-safe-area-context`, and as used `@shopify/flash-list`, `react-native-svg`, `@expo/material-symbols`, `expo-blur`, `react-native-reanimated`.

## Fidelity policy (hybrid)
- Interactive controls: `@expo/ui`, so they behave natively. Apply Figma values through `style` (padding, background, border, radius, opacity, width, height) and `textStyle` (color, fontFamily, fontSize, fontWeight, letterSpacing, lineHeight, textAlign only). Beyond that, `modifiers` from `@expo/ui/swift-ui/modifiers` and `@expo/ui/jetpack-compose/modifiers`, chosen per platform with `Platform.select`.
- Layout and custom visuals (cards, hero, shadows, gradients, illustrations): React Native `View`, `Text`, `expo-image`.
- `Pressable` (with `accessibilityRole="button"`, pressed and disabled states) only for tappable cards and for buttons whose look `@expo/ui` cannot reach (gradient, shadow, custom shape). Record it as a divergence.
- Project already built on a UI kit or its own components: reuse them; `@expo/ui` only for controls they lack. Unclear which wins: ask.
- Anything that cannot match exactly goes in the hand-off as "Divergences: <node> — <why> — <what we did>". Never hide it.

## `@expo/ui` facts that change the code
- Universal components import from the package root: `import { Host, Column, Row, Button, Text } from '@expo/ui'`. Platform packages (`@expo/ui/swift-ui`, `@expo/ui/jetpack-compose`) only for controls the universal set lacks.
- Every subtree starts at `Host`. `Host` takes RN layout styles; inside it there is no flexbox: use `Column`/`Row` (`spacing`, `alignment: 'start' | 'center' | 'end'`) and `Spacer flexible`.
- Size every `Host`: `matchContents`, `{ vertical: true }` plus `style={{ width: '100%' }}`, `flex: 1`, or an explicit size. Without one it can collapse to zero height.
- RN view inside a `Host` subtree: `RNHostView` (one child). `@expo/ui` control inside an RN view: a new `Host`, even if an outer `Host` exists.
- `TextInput` takes `value` as `useNativeState('')`, not a string. On Android it is an unstyled field: draw the Figma border and fill with `style`.
- `Host seedColor` themes native controls from one brand color; `Host colorScheme` forces light or dark.

## Layout (auto layout)
| Figma | Outside `Host` (RN) | Inside `Host` |
|---|---|---|
| Vertical / horizontal | `flexDirection: 'column' / 'row'` | `Column` / `Row` |
| Gap | `gap` (wrap: `rowGap`, `columnGap`) | `spacing` |
| Padding | `padding*` | `style.padding*` |
| Primary axis: start / end / center | `justifyContent` | `Spacer flexible` after / before / on both sides |
| Primary axis: space between | `justifyContent: 'space-between'` | `Spacer flexible` between children |
| Counter axis alignment | `alignItems` | `alignment` |
| Fill container | `flex: 1` on the main axis, `alignSelf: 'stretch'` on the cross axis | fill modifier: Compose `fillMaxWidth()`, SwiftUI `frame` with `maxWidth` |
| Hug contents | no size | `Host matchContents` |
| Fixed | `width` / `height` | `style.width` / `style.height` |
| Min / max size | `minWidth`, `maxWidth`, ... | build that part in RN |
| Wrap | `flexWrap: 'wrap'` | build that part in RN |
| Absolute position | `position: 'absolute'` + offsets | build that part in RN |
| Clip content | `overflow: 'hidden'` | clip modifier: SwiftUI `clipped()`/`clipShape`, Compose `clip(shape)` |

- Frames without auto layout: translate constraints into flex (left and right → stretch; center → centered container; scale → percentage). Absolute coordinates only for overlays.
- The Figma frame width (390, 393, 402...) is a sample, not a constant. No screen-width scale helpers: use flex, `maxWidth` for tablets, `useWindowDimensions` for breakpoints.
- Safe areas: `react-native-safe-area-context`. Android is edge to edge: the design's status bar area is an inset, not padding.

## Visual properties
| Figma | Expo / React Native |
|---|---|
| Solid fill | `backgroundColor` from a token; fill opacity in the color alpha; layer opacity → `opacity` |
| Linear / radial gradient | `backgroundImage: 'linear-gradient(...)'` / `'radial-gradient(...)'` |
| Angular / diamond gradient | no RN equivalent: export the node as an image, or Skia; divergence |
| Image fill | `expo-image` with `contentFit`: fill → `cover`, fit → `contain`, crop → `cover` + `contentPosition`; tile → divergence |
| Corner radius, per corner | `borderRadius`, `borderTopLeftRadius`, ... |
| Corner smoothing | `borderCurve: 'continuous'` (iOS only) |
| Stroke inside | `borderWidth` + `borderColor`; one side → `borderTopWidth`, ...; dashed → `borderStyle: 'dashed'` |
| Stroke outside / center | `outlineWidth`, `outlineColor`, `outlineOffset` (outside); center: half as border, half as outline |
| Drop / inner shadow, several shadows | `boxShadow: 'x y blur spread color'`, `inset` for inner, comma-separated for several |
| Layer blur | Android 12+ only (`filter: 'blur(n)'`); on images `expo-image` `blurRadius`; else divergence |
| Background blur | `expo-blur` `BlurView`; Android needs the content in `BlurTargetView` passed as `blurTarget` plus a `blurMethod`; rounded corners need `overflow: 'hidden'`. Figma radius and `intensity` differ: tune against the screenshot |
| Blend mode | `mixBlendMode` (Android 10+) |
| Mask | export as image, or the MaskedView drop-in (`expo` skill) |

## Legacy banned
Class components, `defaultProps`, `Dimensions.get` (use `useWindowDimensions`), `ListView`, RN `SafeAreaView`, `shadowColor`/`shadowOffset`/`shadowOpacity`/`shadowRadius` and `elevation` for designed shadows (use `boxShadow`), gradient libraries where `backgroundImage` works, `experimental_` props when the stable one exists, width-ratio scale helpers, adding a UI kit for controls `@expo/ui` covers, Tailwind or web code pasted from Figma, hex values outside the theme module.

## Text
- Figma text style → typography token: `fontFamily`, `fontSize`, `fontWeight`, `lineHeight`, `letterSpacing`, `textAlign`, plus `textTransform` and `textDecorationLine` for RN `Text`. `@expo/ui` `textStyle` accepts only its subset: pick those fields, never spread the whole token.
- Line height in px → same number; in % → `fontSize * pct / 100`; "auto" → omit. Letter spacing in % → `fontSize * pct / 100`.
- Custom fonts: embed with the `expo-font` config plugin; each Figma family and weight maps to a loaded face. Check on Android that bold renders the bold file, not a synthesized one.
- Fixed-width text box → `width`; truncation → `numberOfLines`. Keep font scaling on; cap with `maxFontSizeMultiplier` only where the layout breaks.

## Tokens
- One module (for example `theme/tokens.ts`): `colors` per mode, `spacing`, `radius`, `typography`. Names come from the Figma variable names (`color/bg/primary` → `colors.bgPrimary`).
- No variables in the file: extract the repeated literal values into the same module once. No hex outside it.
- Variable modes light and dark → `useColorScheme()` picks the set; `userInterfaceStyle: 'automatic'` in app config.

## Components
- Figma component set → one typed component: variant properties become union props (`variant: 'primary' | 'secondary'`), boolean properties boolean props, text properties string props, instance swaps `ReactNode` slots.
- Code Connect mapping or an existing project component → reuse it, do not rebuild.

| Figma element | Build with |
|---|---|
| Button | `@expo/ui` `Button` (`variant`, `style`, custom children for icon + label); look out of reach → `Pressable` (policy above) |
| Text field, search field | `@expo/ui` `TextInput` |
| Toggle, checkbox, slider | `Switch`, `Checkbox`, `Slider` |
| Dropdown, select, segmented | `Picker`; segmented → SegmentedControl drop-in |
| Date or time input | DateTimePicker drop-in |
| Bottom sheet, action sheet | `BottomSheet` |
| Overflow or context menu | `Menu` |
| Accordion | `Collapsible` |
| Settings-style grouped rows | `FieldGroup`, or `List` + `ListItem` |
| Native-styled long list | `List` + `List.ForEach` (recycled rows keep local state; stable render function, `useCallback` only when the React Compiler is off) |
| Custom-designed list or grid cards | FlashList v2 with RN rows |
| Carousel, pager | PagerView drop-in |
| SF Symbol or Material Symbol icon | `@expo/ui` `Icon` with `Icon.select` (no web; `accessibilityLabel` is Android only, so label the parent control) |
| Custom icon, illustration | downloaded SVG as a `react-native-svg` component when it needs color props, else `expo-image` |
| Photo, raster | `expo-image` with the downloaded file |
| Tab bar | Expo Router tabs (native tabs where the design allows) |
| Navigation bar, header | Expo Router `Stack` screen options; custom header only when the design demands it |
| Modal | Expo Router modal route |

## Screens and flows
- One Figma screen frame → one Expo Router route (`app/(tabs)/home.tsx`, `app/item/[id].tsx`). Repeated frames → shared components.
- Prototype links → `Link` / `router.push`; back arrows → the router stack, not manual state.
- States drawn as separate frames (empty, loading, error, pressed, disabled) → props or state on one component, not separate screens.

## Motion
`get_motion_context` keyframes → Reanimated 4 (CSS-style animations and transitions, or shared values). Duration, easing and delay from the data. Smart Animate between frames → layout animations or shared element transitions only when both are stable in the project's versions.

## Accessibility
- Labels come from the visible text or the action ("Add to cart"). Use a layer name only when it reads as a human label; never ship generated names like "Frame 427" or "icon/chevron-right". Icon-only buttons always get a label.
- Touch target under 44 pt (iOS) or 48 dp (Android): on RN tap areas extend with `hitSlop`; on `@expo/ui` controls grow the control through `style` (padding, width, height). Record the divergence.
- Check contrast of text tokens; flag failures to the designer, do not silently change colors.

## Verify
- iOS simulator and Android emulator, at the frame's logical width when a device matches. Scale each capture to the frame width at 1x, then overlay or diff it against `get_screenshot`.
- Spacing and sizes from the overlay; colors by comparing code tokens with `get_variable_defs`, never by sampling screenshot pixels (color management shifts them).
