#!/usr/bin/env bash
# iOS simulator helper. Usage: ios-sim.sh <list|boot|install|launch|shot|log|erase> [args]
set -euo pipefail

command -v xcrun >/dev/null 2>&1 || { echo "error: xcrun not found (install Xcode and run xcode-select --install)" >&2; exit 1; }

cmd="${1:-}"
[ -n "$cmd" ] && shift || true

case "$cmd" in
  list)
    out="$(xcrun simctl list devices available)"
    printf '%s\n' "$out"
    if ! printf '%s' "$out" | grep -qE "\((Shutdown|Booted)\)"; then
      echo "error: no usable simulators. Install an iOS runtime: Xcode > Settings > Components, or 'xcodebuild -downloadPlatform iOS'." >&2
      exit 3
    fi
    ;;
  boot)
    device="${1:?usage: boot <name|udid>}"
    xcrun simctl boot "$device" 2>/dev/null || true
    open -a Simulator
    xcrun simctl bootstatus "$device" -b
    ;;
  install)
    app="${1:?usage: install <path/to/App.app>}"
    xcrun simctl install booted "$app"
    ;;
  launch)
    bundle_id="${1:?usage: launch <bundle id>}"
    xcrun simctl launch booted "$bundle_id"
    ;;
  shot)
    out="${1:-artifacts/ios-$(date +%Y%m%d-%H%M%S).png}"
    mkdir -p "$(dirname "$out")"
    xcrun simctl io booted screenshot "$out"
    echo "$out"
    ;;
  log)
    process="${1:?usage: log <process name>}"
    xcrun simctl spawn booted log stream --level debug --predicate "process == \"$process\""
    ;;
  erase)
    device="${1:?usage: erase <name|udid>}"
    xcrun simctl shutdown "$device" 2>/dev/null || true
    xcrun simctl erase "$device"
    ;;
  *)
    echo "usage: ios-sim.sh <list|boot|install|launch|shot|log|erase> [args]" >&2
    exit 2
    ;;
esac
