---
name: mobile-device-testing
description: "Use when you must run, test, debug or capture evidence for a mobile app on an iOS simulator, Android emulator or real device: booting devices, installing and launching builds, xcodebuild and Gradle test runs, Maestro, Detox, XCUITest, Espresso and Compose tests, screenshots, logs, crash collection, performance profiling and cloud device farms. Works for Swift, Kotlin, KMP, React Native and Expo."
---
# Mobile device testing

Act as a senior mobile QA/automation engineer with 10+ years. Never claim an app change works until you ran it. Report exactly what ran: platform, device or emulator, OS version, build type, command, result.

## Pick the target
| Need | Use |
|------|-----|
| Logic and UI smoke, fast loop | Simulator (iOS) or Emulator (Android) |
| Permissions, push, camera, biometrics, Bluetooth, sensors, real performance, thermal, battery | Real device (a low-end one for performance) |
| Many OS versions and models | Device farm: Firebase Test Lab, BrowserStack, AWS Device Farm, Maestro Cloud |
Simulators do not run APNs push, real camera or most hardware. Emulators lack real GPU, thermal and OEM behavior. Release-mode builds only for performance conclusions.

## Helper scripts (in `scripts/` of this skill)
- `ios-sim.sh list|boot|install|launch|shot|log|erase`: wraps `xcrun simctl`.
- `android-emu.sh list|start|install|launch|shot|log|crash`: wraps `emulator` and `adb`, waits for boot.
- `run-maestro.sh <flow.yaml|dir>`: runs Maestro flows and saves artifacts to `artifacts/`.
Run them with `bash`. They fail loudly if a required tool is missing; install the tool or report it, do not fake a result.

## iOS
1. `bash scripts/ios-sim.sh list`, then `boot "iPhone 16"`.
2. Build and test: `xcodebuild test -scheme <Scheme> -destination 'platform=iOS Simulator,name=iPhone 16' -resultBundlePath artifacts/ios.xcresult`.
3. Run the app: `xcodebuild build ... -derivedDataPath build`, then `ios-sim.sh install <path/App.app>` and `launch <bundle id>`.
4. Real device: connect, trust, enable Developer Mode, sign with a team; list with `xcrun xctrace list devices` or `xcrun devicectl list devices`; run with Xcode or `xcodebuild -destination 'id=<UDID>'`.
5. Logs and crashes: `ios-sim.sh log <process>`; crash logs in Xcode Devices window or `~/Library/Logs/DiagnosticReports`. Profile with Instruments on device.

## Android
1. `bash scripts/android-emu.sh list`, then `start <avd>` (create one with `avdmanager` or Android Studio; use a Google APIs/Play image matching `targetSdk`, plus an old and a low-RAM profile).
2. Unit: `./gradlew testDebugUnitTest`. Instrumented (Espresso, Compose): `./gradlew connectedDebugAndroidTest`. CI without a window: Gradle Managed Devices (`./gradlew <device>DebugAndroidTest`) or `emulator -no-window -no-audio -gpu swiftshader_indirect`.
3. Install and launch: `android-emu.sh install app-debug.apk`, `launch <package>`.
4. Real device: enable Developer options and USB debugging, accept the RSA prompt, `adb devices`; wireless with `adb pair` / `adb connect`.
5. Logs and crashes: `android-emu.sh log <package>`, `crash`; ANRs in `adb bugreport`; `adb shell dumpsys meminfo <package>`, `dumpsys gfxinfo <package>`; Android Studio Profiler; Perfetto for traces.

## Cross-platform E2E
- **Maestro** (recommended default): declarative YAML, works on iOS simulators, Android emulators and devices, framework-agnostic (native, RN, Expo, Flutter). `maestro test flows/login.yaml`; `maestro studio` to explore; use `testID` / accessibility ids; add `clearState`, `launchApp`, `assertVisible`, `tapOn`, `inputText`, `runFlow`. See `references/maestro-example.yaml`.
- **Detox** for React Native gray-box E2E with automatic synchronization: `detox build -c ios.sim.debug`, `detox test -c ios.sim.debug`.
- **XCUITest** (iOS) and **Espresso / Compose UI test** (Android) for native suites. **Appium** when one suite must drive many frameworks.
- Make tests independent: fresh install or `clearState`, seeded accounts, mock or stage the backend, no fixed sleeps (use waits on visible state).

## What to cover
Fresh install and upgrade from the previous version; first-run and permission prompts (allow, deny, revoke later); airplane mode and flaky network; background and foreground return; process kill and restore; rotation and split screen; dark mode; large font and TalkBack/VoiceOver; low storage and low battery; deep links and push taps; small and large screens; RTL and long-string locales; old and new OS versions.

## Evidence
Save to `artifacts/`: screenshots (`ios-sim.sh shot`, `android-emu.sh shot`), screen recordings (`xcrun simctl io booted recordVideo`, `adb shell screenrecord`), logs, result bundles, JUnit XML. Attach summary to the PR.

## Troubleshooting
- iOS simulator stuck: `xcrun simctl shutdown all`, `ios-sim.sh erase`, restart CoreSimulatorService.
- `adb: device offline` or unauthorized: `adb kill-server && adb start-server`, re-accept the prompt.
- Emulator slow: use hardware acceleration (HVF on macOS, KVM on Linux), arm64 images on Apple silicon, enough RAM.
- Flaky E2E: replace sleeps with condition waits, reset state, pin OS and device images, record video on failure.

## Done when
Tests pass on at least one simulator and one emulator, hardware-dependent features verified on a real device, artifacts saved, and the report states what was and was not run.
