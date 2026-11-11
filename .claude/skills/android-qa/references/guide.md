# android-qa: detailed guide

Loaded on demand from SKILL.md.

## Reading the screen
- `tree` runs `uiautomator dump` and prints one line per meaningful node: `"label" #resource-id Class [click,checked,focus,disabled] @ x y`. The `@ x y` center is what `tap` needs.
- `find "<text|id>"` prints the center of the best match: exact text, content description or resource id first, then a case-insensitive substring; a clickable ancestor is preferred.
- Compose: text and `contentDescription` appear; `Modifier.testTag` appears as resource-id only when the app sets `testTagsAsResourceId = true` (debug builds are fine).
- Flutter: the tree shows semantics labels only when semantics are enabled (any accessibility service on, or `SemanticsBinding.instance.ensureSemantics()` in debug); otherwise tap by coordinates from the screenshot.
- Secure windows (`FLAG_SECURE`) block screenshots and dumps. Use a debug build without the flag.

## Coordinates
Screenshots are full resolution; `tap` uses the same pixels. On a 1080x2424 screen the center is `540 1212`. Status and navigation bars are part of the image.

## State changes and how to reset
| Command | Effect | Reset |
|---|---|---|
| `dark on` | system night mode | `dark off` |
| `fontscale 2.0` | 200% font (Android 14 non-linear scaling) | `fontscale 1.0` |
| `displaysize 720x1280` | small screen | `displaysize reset` |
| `density 480` | density change | `density reset` |
| `rotate 1` | landscape, auto-rotate off | `rotate auto` |
| `locale ar-EG` | RTL language (Android 13+) | `locale en-US` |
| `network off` | Wi-Fi and mobile data off | `network on` |
| `perm revoke <pkg> android.permission.CAMERA` | permission revoked (app process restarts) | `perm grant ...` |

## Lifecycle checks
- Configuration change: `rotate 1` while a form is half filled; input must survive (`rememberSaveable`, `SavedStateHandle`).
- Process death: `procdeath <pkg>` sends the app home, kills the process and leaves the task in recents. `launch <pkg>` restores it; the screen and inputs must come back, not the start screen with lost data.
- Background limits: put the app in the background for 30 s during an upload; it must finish (WorkManager) or resume cleanly.

## Evidence
- `crash` reads the crash buffer (`logcat -b crash`). `anr` greps the main log. Full report when needed: `adb bugreport artifacts/android-qa/bugreport.zip`.
- `startup <pkg> 5` force-stops and cold-starts five times and prints the median `TotalTime`. Compare release builds only; debug builds are several times slower.
- `jank <pkg> reset`, scroll the list with `scroll down` a few times, then `jank <pkg>` for janky frame percentage and 90th, 95th, 99th percentile frame times.
- `mem <pkg>` shows PSS and heap sizes; repeat after navigating back and forth to spot leaks (pair with LeakCanary in debug).
- `record file.mp4 15` captures a 15 s video for flaky or animated bugs.

## Regression test choices
| Bug | Test |
|---|---|
| ViewModel or repository logic | JVM unit test with `runTest`, Turbine, fakes |
| Compose screen state or semantics | Compose UI test (`createComposeRule`) on Robolectric or emulator |
| View-based screen | Espresso |
| Lifecycle (rotation, process death) | `ActivityScenario.recreate()` or `StateRestorationTester` for Compose |
| Cross-screen journey | Maestro flow or instrumented test; run on the emulator in CI |
| Flutter | widget test or `integration_test` |
| React Native or Expo | Jest for logic, Maestro or Detox for the flow |

## Pitfalls
- `input text` cannot type emoji or most non-ASCII characters; paste through a debug intent or test those inputs in instrumented tests.
- Taps right after navigation can land on the old screen; take a new `shot` or `tree` before each tap.
- `pm clear` also revokes permissions and resets onboarding; use it deliberately.
- Emulator performance is not device performance; confirm jank and startup on a mid-range real device.
