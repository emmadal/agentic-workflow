---
name: mobile-device-testing
description: "Use when you must run, test, debug or capture evidence for a mobile app on an iOS simulator, Android emulator or real device: xcodebuild, Gradle, Maestro, Detox, screenshots, logs, crashes."
---
# Mobile device testing

Never claim an app change works until you ran it. Report platform, device or emulator, OS, build type, command, result.

## Target
Simulator or emulator for logic and UI. Real device for permissions, push, camera, biometrics, Bluetooth, sensors, performance, thermals. Device farm (Firebase Test Lab, BrowserStack) for OS and model coverage. Performance conclusions need a release build.

## Scripts (`scripts/`, run with bash; they fail loudly when a tool is missing)
- `ios-sim.sh list|boot|install|launch|shot|log|erase`
- `android-emu.sh list|start|stop|install|launch|shot|log|crash`
- `run-maestro.sh <flow|dir>` saves JUnit and debug output to `artifacts/`

## iOS
`xcodebuild test -scheme <S> -destination 'platform=iOS Simulator,name=<device>' -resultBundlePath artifacts/ios.xcresult` (`xcrun simctl list devices available` for names). Device: `xcrun devicectl list devices`, then `-destination 'id=<UDID>'`. Crashes: Xcode Devices or `~/Library/Logs/DiagnosticReports`.

## Android
`./gradlew testDebugUnitTest`; `./gradlew connectedDebugAndroidTest`. Headless: `emulator -no-window -no-audio -gpu swiftshader_indirect` or Gradle Managed Devices. Device: USB debugging, `adb devices`. Diagnose: `adb logcat -b crash -d`, `dumpsys meminfo|gfxinfo <pkg>`, Perfetto.

## Flutter
`flutter test` for unit and widget tests; `flutter test integration_test -d <device-id>` on a simulator, emulator or device; `flutter devices` lists ids.

## E2E
Maestro by default (YAML, any framework; `references/maestro-example.yaml`). Detox for RN gray-box. XCUITest, Espresso, Compose tests for native suites. Fresh state per test, stubbed backend, condition waits instead of sleeps.

## Cover
Fresh install and upgrade; permission allow, deny, revoke; airplane mode and bad network; background and kill-restore; rotation; dark mode; large font and screen reader; low storage; deep links and push taps; small screens; RTL; oldest and newest supported OS.

## Fix
Simulator stuck: `xcrun simctl shutdown all`, `erase`. `adb offline`: `adb kill-server`. Slow emulator: use arm64 images on Apple silicon. Flaky E2E: replace sleeps, reset state, record video.

## Verify
Save screenshots, logs and result files in `artifacts/`; state what was and was not run. More detail: `references/guide.md`.
