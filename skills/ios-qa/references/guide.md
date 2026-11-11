# ios-qa: detailed guide

Loaded on demand from SKILL.md.

## Touch drivers
simctl has no tap or accessibility-tree command, so `ios-qa.sh` uses the first driver it finds (override with `IOS_QA_DRIVER=axe|idb|maestro`):

| Driver | Install | Notes |
|---|---|---|
| AXe | `brew tap cameroncooke/axe && brew install axe` | single binary, fast, tap by point, label or id; simulators only |
| idb | `brew install facebook/fb/idb-companion` and `pip install fb-idb` | simulators; device support is partial |
| Maestro | `curl -fsSL https://get.maestro.mobile.dev \| bash` | YAML flows, also Android; set `IOS_QA_BUNDLE` for flow app id |

Installing a driver changes the user's machine: ask first. Without one, `shot`, state changes, deep links and logs still work, and flows can be covered with XCUITest.

## Coordinates
`tree` and `tap` use points, not pixels. A screenshot of an iPhone 17 is 3x: divide pixel positions by 3 before tapping by coordinates. Prefer `tap-text` with an accessibility identifier.

## Reading the screen
- SwiftUI: `.accessibilityIdentifier("checkout.pay")` gives stable ids; labels come from `Text`, `Label` and `accessibilityLabel`.
- Flutter: semantics must be on (any accessibility feature, or `SemanticsBinding.instance.ensureSemantics()` in debug) for labels to appear.
- React Native: `testID` maps to the accessibility identifier; `accessibilityLabel` to the label.
- Empty tree or only the app window: the app is still launching, or a system alert is on top; take a screenshot.

## State changes and how to reset
| Command | Effect | Reset |
|---|---|---|
| `appearance dark` | dark mode | `appearance light` |
| `textsize accessibility-extra-extra-extra-large` | largest Dynamic Type | `textsize large` |
| `contrast on` | Increase Contrast | `contrast off` |
| `privacy revoke camera <bundle>` | permission denied (app is killed) | `privacy reset all <bundle>` |
| `location 37.33,-122.03` | simulated location | `location clear` |
| `statusbar clean` | 9:41, full bars, charged | `statusbar clear` |
| `push <bundle> payload.json` | delivers a notification (`{"aps":{"alert":"Hi"}}`) | none |

## Real devices
- `xcrun devicectl list devices` shows paired devices; set `IOS_QA_UDID`.
- Build for the device: `xcodebuild -scheme App -destination 'id=<UDID>' -derivedDataPath build/ios-qa build`, then `device-install build/ios-qa/Build/Products/Debug-iphoneos/App.app` and `device-launch <bundle>`.
- Screenshots: `device-shot` with pymobiledevice3 (iOS 17+ needs `sudo pymobiledevice3 remote tunneld` running), or XCUITest attachments, or Xcode's Devices window.
- Touch on device: drive flows with XCUITest (`xcodebuild test -destination 'id=<UDID>' -only-testing:AppUITests/QAFlows`), taking `XCUIScreen.main.screenshot()` attachments at each step. Read them from the `.xcresult` with `xcrun xcresulttool`.
- Logs: Console.app filtered by process, or `log collect --device-udid <UDID>`; crash reports in Xcode, Devices and Simulators, View Device Logs.

## Lifecycle checks
- State restoration: fill a form, `terminate`, `launch`; scene storage and drafts must come back where the product promises it.
- Background tasks: lock the device during an upload; it must finish (background `URLSession`) or resume.
- Interruptions: incoming push while editing, permission alert over a sheet, rotation mid-animation.

## Regression test choices
| Bug | Test |
|---|---|
| View model or service logic | Swift Testing with injected fakes |
| Screen state, navigation, accessibility | XCUITest with accessibility identifiers and launch arguments (`-ui-testing -seed empty`), plus `performAccessibilityAudit()` |
| Rendering differences (dark mode, Dynamic Type) | snapshot test of the view in each environment |
| Flutter, React Native, Expo | widget or Jest tests for logic; `integration_test`, Detox or Maestro for the flow |

## Pitfalls
- The first launch after boot is slow; wait for the screen before acting.
- `privacy` changes kill the app; relaunch before continuing.
- Simulator performance, camera, push delivery timing and biometrics differ from devices; confirm those on hardware.
- Do not leave the simulator in dark mode or giant text for the next task; restore state at the end.
