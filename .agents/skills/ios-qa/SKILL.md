---
name: ios-qa
description: "Use when asked to QA or find and fix bugs in a running iOS app on iPhone or iPad (simulator/device): drive screens with simctl, check Dynamic Type, VoiceOver labels, deep links, push, crash logs, fix with XCUITest."
---
# iOS QA: explore, fix, verify

Drive the real app, see every screen, fix with proof. Works for SwiftUI, UIKit, Flutter, React Native and Expo. Driver: `scripts/ios-qa.sh` (macOS, Xcode, Python 3.9+). simctl covers app and device state; touch and accessibility need AXe, idb or Maestro (`doctor` says which). Suites and CI: `mobile-device-testing`.

## Setup
1. Clean git tree before fixes (ask: commit, stash, abort). Tier `quick`, `standard` or `exhaustive` as in the `qa` skill.
2. `doctor`, then `boot "iPhone 17"`. Real device (`devices`, set `IOS_QA_UDID`) for push, camera, biometrics, performance.
3. Read the source first: screens and navigation (`NavigationStack` destinations, view controllers), deep links (`onOpenURL`, URL types, associated domains), launch arguments, permissions in `Info.plist`. One charter per screen: contract, risk, how to reach it.
4. `build <scheme>`, `install <App.app>`, `launch <bundle-id> [-args]`. Evidence goes to `artifacts/ios-qa/<run>/`.

## Explore loop (one action per step)
1. `shot <run>/NNN.png` and look at it; `tree` lists labels, ids and tap points.
2. Decide the next action from the screen and the charter.
3. Act: `tap-text "<label or id>"`, `tap x y`, `type "<text>"`, `swipe`, `openurl <deep link>`. No touch driver: reach screens via deep links and launch arguments, or write an XCUITest for the flow.
4. Shot again, compare, record defects with steps and screenshots. After anything odd: `crashes`, `log <process>`.

Cover each core screen under: fresh install and upgrade; `privacy grant|revoke|reset`; `appearance dark`; `textsize accessibility-extra-extra-extra-large`; `contrast on`; `audit` for unlabeled controls and targets under 44pt; rotation and iPad split view; offline (Network Link Conditioner or airplane mode); `terminate` then `launch` (state restore); `push`, `location`, deep links; smallest and largest devices. `statusbar clean` for screenshots.

## Fix loop
Same as `qa`: failing regression test first (Swift Testing for logic, XCUITest with accessibility identifiers for UI), minimal fix, rebuild, reinstall, replay the steps, commit `fix(ios-qa): ISSUE-NNN <summary>`. Stop and ask after 2 reverts or 5 fixes.

## Report
Use the `qa` report shape: device, iOS version, build config, issues with screenshots, fixes with SHAs, what needs a real device. Restore state (`appearance light`, `textsize large`, `contrast off`, `statusbar clear`).

## Rules
Sandbox accounts and test data only, never production payments. `erase` wipes the simulator: ask first. Debug-only hooks stay behind `#if DEBUG`. A fix is verified only after replaying it on simulator or device. Drivers, real devices and pitfalls: `references/guide.md`.
