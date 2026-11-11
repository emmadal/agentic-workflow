---
name: android-qa
description: "Use when asked to QA or find and fix bugs in a running Android app on an emulator or device: drive it over adb, check font scale, rotation, process death, TalkBack labels, ANRs and crashes, fix with tests."
---
# Android QA: explore, fix, verify

Drive the real app, look at every screen, fix bugs with proof. Works for Kotlin, Compose, Flutter, React Native and Expo apps. Driver: `scripts/android-qa.sh` (bash, adb, Python 3.9+); no app changes needed. Test suites and CI: `mobile-device-testing`.

## Setup
1. Clean git tree before fixes (ask: commit, stash, abort). Tier `quick`, `standard` or `exhaustive` as in the `qa` skill.
2. `android-qa.sh doctor`; `start <avd> --headless` boots an emulator. Real device (USB debugging) for camera, Bluetooth, biometrics, performance. Set `ANDROID_SERIAL` when several are attached.
3. Read the source first: screens and navigation graph, deep links (manifest `intent-filter`s), runtime permissions, feature flags, debug menus. Write one charter per screen: contract, risk, how to reach it.
4. `build`, `install <apk>`, `launch <pkg>`. Evidence goes to `artifacts/android-qa/<run>/`.

## Explore loop (one action per step)
1. `shot <run>/NNN.png` and look at it; `tree` lists labels, ids and tap centers.
2. Decide the next action from the screen and the charter.
3. Act: `tap-text "<label or id>"`, `tap x y`, `type "<text>"`, `key BACK`, `scroll down`, `openurl <deep link>`.
4. Shot again, compare, record defects with steps and screenshots. After anything odd: `crash`, `anr`, `log <pkg>`.

Cover each core screen under: first launch and upgrade install; `perm grant|revoke`; `dark on`; `fontscale 2.0`; `rotate 1`; `displaysize 720x1280` (small) and a tablet AVD; `network off`; `background` then relaunch; `procdeath <pkg>` (state must survive); `locale ar-EG` for RTL; back and predictive back; deep links; `audit` for unlabeled controls and targets under 48dp. Measure `startup <pkg>` and `jank <pkg>` on a release build. `monkey` only with test data.

## Fix loop
Same as `qa`: failing regression test first (JVM unit test, Compose UI test or Espresso with Robolectric or on the emulator), minimal fix, rebuild, reinstall, replay the exact steps, commit `fix(android-qa): ISSUE-NNN <summary>`. Stop and ask after 2 reverts or every 5 fixes.

## Report
Use the `qa` report shape: device, Android version, build type, issues with screenshots, fixes with SHAs, what still needs a real device. Restore settings you changed (`dark off`, `fontscale 1.0`, `rotate auto`, `displaysize reset`, `network on`).

## Rules
Never use production accounts, payments or real user data. `clear` and `monkey` wipe or scramble app data: emulator or test device only. A fix is verified only after replaying on the emulator or device. Command details and pitfalls: `references/guide.md`.
