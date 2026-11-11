#!/usr/bin/env bash
# Android QA driver over adb. Targets ANDROID_SERIAL when set, else the only device.
# Run with no arguments for the command list.
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY=${PYTHON:-python3}
die() { echo "android-qa: $*" >&2; exit 2; }
need() { command -v "$1" >/dev/null 2>&1 || die "$1 not found${2:+: $2}"; }
sh_() { adb shell "$@"; }

usage() {
  cat <<'EOF'
android-qa.sh <command> [args]
 setup     doctor | devices | start <avd> [--headless] | stop | build [module] [variant]
           install <apk> | launch <pkg>[/activity] | stop-app <pkg> | clear <pkg>
 see       shot <file.png> | record <file.mp4> <seconds> | tree [--all] | find <text|id>
           audit (unlabeled controls, targets under 48dp) | focus (current activity)
 act       tap <x> <y> | tap-text <text|id> | type <text> | key <BACK|HOME|ENTER|TAB|DEL|...>
           swipe <x1> <y1> <x2> <y2> [ms] | scroll <up|down> | openurl <uri> [pkg]
 states    dark <on|off> | fontscale <1.0|1.3|2.0> | displaysize <WxH|reset>
           density <dpi|reset> | rotate <0|1|2|3|auto> | locale <tag> | network <on|off>
           perm <grant|revoke> <pkg> <permission> | background | procdeath <pkg>
 evidence  log <pkg> [seconds] | crash | anr | startup <pkg> [runs] | jank <pkg> | mem <pkg>
           monkey <pkg> [events] [seed]
EOF
}

pid_of() { sh_ pidof "$1" 2>/dev/null | tr -d '\r' || true; }

dump_tree() {
  local out
  out=$(mktemp "${TMPDIR:-/tmp}/ui.XXXXXX.xml")
  sh_ uiautomator dump /sdcard/android-qa-ui.xml >/dev/null 2>&1 || die "uiautomator dump failed (screen off, locked or secure window?)"
  adb pull /sdcard/android-qa-ui.xml "$out" >/dev/null 2>&1
  echo "$out"
}

launcher_component() {
  sh_ cmd package resolve-activity --brief -c android.intent.category.LAUNCHER "$1" 2>/dev/null \
    | tr -d '\r' | tail -1 | grep '/' || true
}

escape_text() {
  # adb `input text`: spaces become %s, shell metacharacters are backslash-escaped.
  "$PY" - "$1" <<'PY'
import sys
special = set("\\\"'`$&|;<>()[]{}*?!~#%^")
print("".join("%s" if c == " " else ("\\" + c if c in special else c) for c in sys.argv[1]))
PY
}

cmd=${1:-help}
[ $# -gt 0 ] && shift
case "$cmd" in
  doctor)
    for t in adb emulator "$PY"; do
      if command -v "$t" >/dev/null 2>&1; then echo "ok      $t"; else echo "missing $t"; fi
    done
    command -v maestro >/dev/null 2>&1 && echo "ok      maestro (optional flows)" || echo "info    maestro not installed (optional)"
    echo "AVDs:"; (emulator -list-avds 2>/dev/null || true) | sed 's/^/  /'
    echo "Devices:"; adb devices -l | tail -n +2 | sed '/^$/d; s/^/  /'
    ;;
  devices) adb devices -l ;;
  start)
    need emulator "install the Android SDK emulator"
    avd=${1:-}; [ -n "$avd" ] || die "usage: start <avd> [--headless]"
    flags=(-avd "$avd" -no-snapshot-save -no-boot-anim -netdelay none -netspeed full)
    [ "${2:-}" = "--headless" ] && flags+=(-no-window -no-audio -gpu swiftshader_indirect)
    nohup emulator "${flags[@]}" >"${TMPDIR:-/tmp}/android-qa-emulator.log" 2>&1 &
    adb wait-for-device
    for _ in $(seq 1 180); do
      [ "$(sh_ getprop sys.boot_completed 2>/dev/null | tr -d '\r')" = "1" ] && { echo "booted $avd"; exit 0; }
      sleep 1
    done
    die "emulator did not finish booting in 180s (log: ${TMPDIR:-/tmp}/android-qa-emulator.log)"
    ;;
  stop) adb emu kill ;;
  build)
    module=${1:-app}; variant=${2:-Debug}
    [ -x ./gradlew ] || die "run from the Gradle project root (./gradlew not found)"
    ./gradlew ":$module:assemble$variant" --console=plain
    find "$module/build/outputs/apk" -name '*.apk' -newer ./gradlew 2>/dev/null | head -5
    ;;
  install) [ -f "${1:-}" ] || die "usage: install <apk>"; adb install -r -t "$1" ;;
  launch)
    target=${1:-}; [ -n "$target" ] || die "usage: launch <pkg>[/activity]"
    if [[ "$target" == */* ]]; then comp=$target; else comp=$(launcher_component "$target"); fi
    [ -n "$comp" ] || die "no launcher activity for $target (is it installed?)"
    sh_ am start -W -n "$comp" | tr -d '\r' | grep -E 'Status|Activity|TotalTime|WaitTime' || true
    ;;
  stop-app) sh_ am force-stop "${1:?usage: stop-app <pkg>}" ;;
  clear) sh_ pm clear "${1:?usage: clear <pkg>}" ;;
  shot)
    file=${1:?usage: shot <file.png>}
    mkdir -p "$(dirname "$file")"
    adb exec-out screencap -p >"$file"
    [ -s "$file" ] || die "screenshot is empty"
    echo "$file"
    ;;
  record)
    file=${1:?usage: record <file.mp4> <seconds>}; secs=${2:-10}
    sh_ screenrecord --time-limit "$secs" /sdcard/android-qa.mp4
    adb pull /sdcard/android-qa.mp4 "$file" >/dev/null 2>&1 && echo "$file"
    ;;
  tree)
    xml=$(dump_tree); "$PY" "$here/ui_tree.py" list "$xml" ${1:+"$1"}; rm -f "$xml"
    ;;
  find)
    xml=$(dump_tree); "$PY" "$here/ui_tree.py" find "$xml" "${1:?usage: find <text|id>}"; rc=$?; rm -f "$xml"; exit $rc
    ;;
  audit)
    density=$(sh_ wm density | tr -d '\r' | awk '/Override density/{o=$3} /Physical density/{p=$3} END{print (o?o:p)}')
    xml=$(dump_tree); "$PY" "$here/ui_tree.py" audit "$xml" --density "${density:-160}"; rm -f "$xml"
    ;;
  focus) sh_ dumpsys activity activities | tr -d '\r' | grep -m1 -E 'topResumedActivity|mResumedActivity' ;;
  tap) sh_ input tap "${1:?usage: tap <x> <y>}" "${2:?usage: tap <x> <y>}" ;;
  tap-text)
    xml=$(dump_tree)
    if ! xy=$("$PY" "$here/ui_tree.py" find "$xml" "${1:?usage: tap-text <text|id>}"); then rm -f "$xml"; exit 1; fi
    rm -f "$xml"
    # shellcheck disable=SC2086
    sh_ input tap $xy && echo "tapped $1 at $xy"
    ;;
  type) sh_ input text "$(escape_text "${1:?usage: type <text>}")" ;;
  key) sh_ input keyevent "KEYCODE_$(echo "${1:?usage: key <name>}" | tr '[:lower:]' '[:upper:]' | sed 's/^KEYCODE_//')" ;;
  swipe) sh_ input swipe "${1:?}" "${2:?}" "${3:?}" "${4:?usage: swipe x1 y1 x2 y2 [ms]}" "${5:-300}" ;;
  scroll)
    read -r w h < <(sh_ wm size | tr -d '\r' | awk -F'[ x]' '/size/{print $(NF-1), $NF}' | tail -1)
    x=$((w / 2)); top=$((h / 4)); bottom=$((h * 3 / 4))
    case "${1:-down}" in
      down) sh_ input swipe "$x" "$bottom" "$x" "$top" 300 ;;
      up) sh_ input swipe "$x" "$top" "$x" "$bottom" 300 ;;
      *) die "usage: scroll <up|down>" ;;
    esac
    ;;
  openurl)
    uri=${1:?usage: openurl <uri> [pkg]}
    sh_ am start -W -a android.intent.action.VIEW -d "'$uri'" ${2:+"$2"} | tr -d '\r' | grep -E 'Status|Activity|Error' || true
    ;;
  dark)
    case "${1:-}" in on) sh_ cmd uimode night yes ;; off) sh_ cmd uimode night no ;; *) die "usage: dark <on|off>" ;; esac
    ;;
  fontscale) sh_ settings put system font_scale "${1:?usage: fontscale <1.0|1.3|2.0>}" ;;
  displaysize) [ "${1:-}" = reset ] && sh_ wm size reset || sh_ wm size "${1:?usage: displaysize <WxH|reset>}" ;;
  density) [ "${1:-}" = reset ] && sh_ wm density reset || sh_ wm density "${1:?usage: density <dpi|reset>}" ;;
  rotate)
    if [ "${1:-}" = auto ]; then sh_ settings put system accelerometer_rotation 1; else
      sh_ settings put system accelerometer_rotation 0
      sh_ settings put system user_rotation "${1:?usage: rotate <0|1|2|3|auto>}"
    fi
    ;;
  locale) sh_ cmd locale set-system-locales "${1:?usage: locale <tag, e.g. ar-EG>}" 2>/dev/null || die "locale change needs Android 13+ (or change it in Settings)" ;;
  network)
    case "${1:-}" in
      off) sh_ svc wifi disable; sh_ svc data disable ;;
      on) sh_ svc wifi enable; sh_ svc data enable ;;
      *) die "usage: network <on|off>" ;;
    esac
    ;;
  perm)
    action=${1:-}; pkg=${2:-}; perm=${3:-}
    [[ "$action" =~ ^(grant|revoke)$ && -n "$pkg" && -n "$perm" ]] || die "usage: perm <grant|revoke> <pkg> <android.permission.X>"
    sh_ pm "$action" "$pkg" "$perm"
    ;;
  background) sh_ input keyevent KEYCODE_HOME ;;
  procdeath)
    pkg=${1:?usage: procdeath <pkg>}
    sh_ input keyevent KEYCODE_HOME; sleep 1
    sh_ am kill "$pkg"; sleep 1
    [ -z "$(pid_of "$pkg")" ] && echo "process killed; relaunch with: launch $pkg (state must be restored)" || echo "process still alive (foreground service?)"
    ;;
  log)
    pkg=${1:?usage: log <pkg> [seconds]}; secs=${2:-0}
    pid=$(pid_of "$pkg"); [ -n "$pid" ] || die "$pkg is not running"
    if [ "$secs" = 0 ]; then adb logcat -d --pid="$pid" | tail -200
    else adb logcat --pid="$pid" & lp=$!; sleep "$secs"; kill "$lp" 2>/dev/null || true; fi
    ;;
  crash) adb logcat -b crash -d | tail -80 ;;
  anr) adb logcat -d | grep -E -A6 'ANR in|Application Not Responding' | tail -60 || echo "no ANR in the current log buffer" ;;
  startup)
    pkg=${1:?usage: startup <pkg> [runs]}; runs=${2:-5}
    comp=$(launcher_component "$pkg"); [ -n "$comp" ] || die "no launcher activity for $pkg"
    times=()
    for _ in $(seq 1 "$runs"); do
      sh_ am force-stop "$pkg"; sleep 1
      t=$(sh_ am start -W -S -n "$comp" | tr -d '\r' | awk '/TotalTime/{print $2}')
      times+=("${t:-0}")
    done
    printf '%s\n' "${times[@]}" | sort -n | awk '{a[NR]=$1} END{printf "cold start TotalTime ms: median %d, min %d, max %d (n=%d, build type matters)\n", a[int((NR+1)/2)], a[1], a[NR], NR}'
    ;;
  jank)
    pkg=${1:?usage: jank <pkg>}
    if [ "${2:-}" = reset ]; then sh_ dumpsys gfxinfo "$pkg" reset >/dev/null; echo "counters reset; interact, then run: jank $pkg"; exit 0; fi
    sh_ dumpsys gfxinfo "$pkg" | tr -d '\r' | grep -E 'Total frames rendered|Janky frames|percentile|Number Slow' | head -12
    ;;
  mem) sh_ dumpsys meminfo "${1:?usage: mem <pkg>}" | tr -d '\r' | grep -E 'TOTAL PSS|TOTAL RSS|Java Heap|Native Heap' | head -6 ;;
  monkey)
    pkg=${1:?usage: monkey <pkg> [events] [seed]}
    sh_ monkey -p "$pkg" -s "${3:-42}" --throttle 120 --pct-syskeys 0 --ignore-security-exceptions -v "${2:-500}" | tail -15
    ;;
  help|-h|--help) usage ;;
  *) usage; exit 2 ;;
esac
