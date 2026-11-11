#!/usr/bin/env bash
# Android emulator/device helper. Usage: android-emu.sh <list|start|stop|install|launch|shot|log|crash> [args]
set -euo pipefail

need() { command -v "$1" >/dev/null 2>&1 || { echo "error: $1 not found (set ANDROID_HOME and add platform-tools and emulator to PATH)" >&2; exit 1; }; }

wait_for_boot() {
  adb wait-for-device
  until [ "$(adb shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')" = "1" ]; do
    sleep 2
  done
}

cmd="${1:-}"
[ -n "$cmd" ] && shift || true

case "$cmd" in
  list)
    need emulator
    echo "AVDs:"; emulator -list-avds
    need adb
    echo "Connected:"; adb devices
    ;;
  start)
    need emulator; need adb
    avd="${1:?usage: start <avd name>}"
    nohup emulator -avd "$avd" -no-snapshot-save >/dev/null 2>&1 &
    wait_for_boot
    echo "booted: $avd"
    ;;
  stop)
    need adb
    adb emu kill >/dev/null 2>&1 || true
    echo "emulator stopped"
    ;;
  install)
    need adb
    apk="${1:?usage: install <path/to/app.apk>}"
    adb install -r "$apk"
    ;;
  launch)
    need adb
    pkg="${1:?usage: launch <package name>}"
    out="$(adb shell monkey -p "$pkg" -c android.intent.category.LAUNCHER 1 2>&1 || true)"
    if printf '%s' "$out" | grep -qiE "monkey aborted|No activities found|Error"; then
      echo "error: could not launch $pkg (is it installed?)" >&2
      exit 1
    fi
    ;;
  shot)
    need adb
    out="${1:-artifacts/android-$(date +%Y%m%d-%H%M%S).png}"
    mkdir -p "$(dirname "$out")"
    adb exec-out screencap -p > "$out"
    echo "$out"
    ;;
  log)
    need adb
    pkg="${1:?usage: log <package name>}"
    pid="$(adb shell pidof -s "$pkg" 2>/dev/null | tr -d '\r' || true)"
    [ -n "$pid" ] || { echo "error: $pkg is not running" >&2; exit 1; }
    adb logcat -v time --pid="$pid"
    ;;
  crash)
    need adb
    adb logcat -b crash -d
    ;;
  *)
    echo "usage: android-emu.sh <list|start|stop|install|launch|shot|log|crash> [args]" >&2
    exit 2
    ;;
esac
