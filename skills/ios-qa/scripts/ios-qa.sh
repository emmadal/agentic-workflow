#!/usr/bin/env bash
# iOS QA driver: simctl for app and device state, AXe, idb or Maestro for touch and the
# accessibility tree, devicectl for physical devices. Targets IOS_QA_UDID when set, else the
# first booted simulator. Run with no arguments for the command list.
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY=${PYTHON:-python3}
die() { echo "ios-qa: $*" >&2; exit 2; }
command -v xcrun >/dev/null 2>&1 || die "xcrun not found: install Xcode and run xcode-select --install"

usage() {
  cat <<'EOF'
ios-qa.sh <command> [args]
 setup     doctor | devices | boot <name|udid> | build <scheme> [simulator name]
           install <App.app> | launch <bundle-id> [args...] | terminate <bundle-id>
           uninstall <bundle-id> | erase (wipes the simulator)
 see       shot <file.png> | record <file.mp4> <seconds> | tree | find <label|id> | audit
 act       tap <x> <y> | tap-text <label|id> | type <text> | swipe <x1> <y1> <x2> <y2>
           home | openurl <url>
 states    appearance <light|dark> | textsize <category> | contrast <on|off>
           privacy <grant|revoke|reset> <service> <bundle-id> | push <bundle-id> <payload.json>
           location <lat,lon|clear> | statusbar <clean|clear>
 evidence  log <process-name> [seconds] | crashes [process-name]
 device    device-install <App.app> | device-launch <bundle-id> | device-shot <file.png>
Touch and tree need one driver: AXe (brew tap cameroncooke/axe && brew install axe),
idb (pip install fb-idb; brew install facebook/fb/idb-companion) or Maestro.
textsize categories: extra-small ... extra-extra-extra-large, accessibility-medium ...
accessibility-extra-extra-extra-large.
EOF
}

udid() {
  if [ -n "${IOS_QA_UDID:-}" ]; then echo "$IOS_QA_UDID"; return; fi
  xcrun simctl list devices booted -j | "$PY" -c 'import json,sys
d=json.load(sys.stdin)["devices"]
ids=[x["udid"] for v in d.values() for x in v if x.get("state")=="Booted"]
print(ids[0] if ids else "")'
}

default_sim() {
  # First available iPhone on the newest iOS runtime, so builds never depend on a fixed model.
  xcrun simctl list devices available -j | "$PY" -c 'import json,re,sys
d=json.load(sys.stdin)["devices"]
ver=lambda k:[int(n) for n in re.findall(r"\d+",k.rsplit("iOS",1)[-1])]
for key in sorted((k for k in d if "iOS" in k),key=ver,reverse=True):
    names=[x["name"] for x in d[key] if x["name"].startswith("iPhone")]
    if names:
        print(names[0]); break'
}

target() {
  local u
  u=$(udid)
  [ -n "$u" ] || die "no booted simulator: run 'ios-qa.sh boot \"<device name>\"' (see: ios-qa.sh devices) or set IOS_QA_UDID"
  echo "$u"
}

driver() {
  if [ -n "${IOS_QA_DRIVER:-}" ]; then echo "$IOS_QA_DRIVER"; return; fi
  for d in axe idb maestro; do command -v "$d" >/dev/null 2>&1 && { echo "$d"; return; }; done
  echo none
}

need_driver() {
  local d
  d=$(driver)
  [ "$d" != none ] || die "touch and tree need AXe, idb or Maestro (see: ios-qa.sh help)"
  echo "$d"
}

maestro_flow() {
  # $1 = flow body lines; runs against the target simulator.
  local flow bundle
  bundle=${IOS_QA_BUNDLE:-com.apple.springboard}
  flow=$(mktemp "${TMPDIR:-/tmp}/ios-qa-flow.XXXXXX.yaml")
  printf 'appId: %s\n---\n%s\n' "$bundle" "$1" >"$flow"
  maestro --device "$U" test "$flow" >/dev/null
  rm -f "$flow"
}

dump_tree() {
  local out
  out=$(mktemp "${TMPDIR:-/tmp}/ios-qa-tree.XXXXXX.json")
  case "$D" in
    axe) axe describe-ui --udid "$U" >"$out" ;;
    idb) idb ui describe-all --udid "$U" --json >"$out" ;;
    maestro) maestro --device "$U" hierarchy >"$out" ;;
  esac
  echo "$out"
}

tap_xy() {
  case "$D" in
    axe) axe tap -x "$1" -y "$2" --udid "$U" ;;
    idb) idb ui tap "$1" "$2" --udid "$U" ;;
    maestro) maestro_flow "- tapOn:
    point: \"$1,$2\"" ;;
  esac
}

cmd=${1:-help}
[ $# -gt 0 ] && shift
# Resolve the simulator and touch driver once, in this shell, so a failure stops the script.
U=""
D=""
case "$cmd" in
  doctor | devices | boot | build | crashes | device-* | help | -h | --help) ;;
  *) U=$(target) ;;
esac
case "$cmd" in
  tree | find | audit | tap | tap-text | type | swipe) D=$(need_driver) ;;
  home) D=$(driver) ;;
esac
case "$cmd" in
  doctor)
    echo "Xcode: $(xcodebuild -version 2>/dev/null | head -1 || echo missing)"
    echo "Driver: $(driver)"
    echo "Booted simulators:"; xcrun simctl list devices booted | grep -E '\(Booted\)' | sed 's/^ */  /' || echo "  none"
    echo "Physical devices:"; (xcrun devicectl list devices 2>/dev/null | tail -n +3 | grep -i physical | sed 's/^/  /') || echo "  none"
    ;;
  devices)
    xcrun simctl list devices available | grep -E 'iPhone|iPad' || true
    xcrun devicectl list devices 2>/dev/null || true
    ;;
  boot)
    name=${1:?usage: boot <name|udid>}
    xcrun simctl boot "$name" 2>/dev/null || true
    xcrun simctl bootstatus "$name" -b >/dev/null
    open -a Simulator >/dev/null 2>&1 || true
    echo "booted $name"
    ;;
  build)
    scheme=${1:?usage: build <scheme> [simulator name]}; sim=${2:-$(default_sim)}
    [ -n "$sim" ] || die "no iPhone simulator available: install an iOS runtime in Xcode"
    xcodebuild -scheme "$scheme" -destination "platform=iOS Simulator,name=$sim" \
      -derivedDataPath build/ios-qa -configuration Debug build -quiet
    find build/ios-qa/Build/Products -maxdepth 2 -name '*.app' -path '*iphonesimulator*' | head -3
    ;;
  install) [ -d "${1:-}" ] || die "usage: install <App.app>"; xcrun simctl install "$U" "$1" ;;
  launch)
    bundle=${1:?usage: launch <bundle-id> [args...]}; shift
    xcrun simctl launch --terminate-running-process "$U" "$bundle" "$@"
    ;;
  terminate) xcrun simctl terminate "$U" "${1:?usage: terminate <bundle-id>}" ;;
  uninstall) xcrun simctl uninstall "$U" "${1:?usage: uninstall <bundle-id>}" ;;
  erase)
    xcrun simctl shutdown "$U" 2>/dev/null || true; xcrun simctl erase "$U"; echo "erased $U (boot it again)"
    ;;
  shot)
    file=${1:?usage: shot <file.png>}; mkdir -p "$(dirname "$file")"
    xcrun simctl io "$U" screenshot --type=png "$file" >/dev/null 2>&1
    [ -s "$file" ] || die "screenshot failed"
    echo "$file"
    ;;
  record)
    file=${1:?usage: record <file.mp4> <seconds>}; secs=${2:-10}
    xcrun simctl io "$U" recordVideo --force "$file" >/dev/null 2>&1 & rp=$!
    sleep "$secs"; kill -INT "$rp" 2>/dev/null || true; wait "$rp" 2>/dev/null || true
    [ -s "$file" ] && echo "$file" || die "recording failed"
    ;;
  tree) t=$(dump_tree); "$PY" "$here/ax_tree.py" list "$t"; rm -f "$t" ;;
  find) t=$(dump_tree); rc=0; "$PY" "$here/ax_tree.py" find "$t" "${1:?usage: find <label|id>}" || rc=$?; rm -f "$t"; exit $rc ;;
  audit) t=$(dump_tree); "$PY" "$here/ax_tree.py" audit "$t"; rm -f "$t" ;;
  tap) tap_xy "${1:?usage: tap <x> <y>}" "${2:?usage: tap <x> <y>}" ;;
  tap-text)
    q=${1:?usage: tap-text <label|id>}
    t=$(dump_tree)
    if ! xy=$("$PY" "$here/ax_tree.py" find "$t" "$q"); then rm -f "$t"; exit 1; fi
    rm -f "$t"
    # shellcheck disable=SC2086
    tap_xy $xy && echo "tapped $q at $xy"
    ;;
  type)
    text=${1:?usage: type <text>}
    case "$D" in
      axe) axe type "$text" --udid "$U" ;;
      idb) idb ui text "$text" --udid "$U" ;;
      maestro) maestro_flow "- inputText: $("$PY" -c 'import json,sys; print(json.dumps(sys.argv[1]))' "$text")" ;;
    esac
    ;;
  swipe)
    x1=${1:?}; y1=${2:?}; x2=${3:?}; y2=${4:?usage: swipe x1 y1 x2 y2}
    case "$D" in
      axe) axe swipe --start-x "$x1" --start-y "$y1" --end-x "$x2" --end-y "$y2" --udid "$U" ;;
      idb) idb ui swipe "$x1" "$y1" "$x2" "$y2" --udid "$U" ;;
      maestro) maestro_flow "- swipe:
    start: \"$x1,$y1\"
    end: \"$x2,$y2\"" ;;
    esac
    ;;
  home)
    case "$D" in
      axe) axe button home --udid "$U" ;;
      idb) idb ui button HOME --udid "$U" ;;
      maestro) maestro_flow "- pressKey: Home" ;;
      *) die "home needs AXe, idb or Maestro" ;;
    esac
    ;;
  openurl) xcrun simctl openurl "$U" "${1:?usage: openurl <url>}" ;;
  appearance) xcrun simctl ui "$U" appearance "${1:?usage: appearance <light|dark>}" ;;
  textsize) xcrun simctl ui "$U" content_size "${1:?usage: textsize <category>}" ;;
  contrast)
    case "${1:-}" in on) v=enabled ;; off) v=disabled ;; *) die "usage: contrast <on|off>" ;; esac
    xcrun simctl ui "$U" increase_contrast "$v"
    ;;
  privacy)
    action=${1:-}; service=${2:-}; bundle=${3:-}
    [[ "$action" =~ ^(grant|revoke|reset)$ && -n "$service" && -n "$bundle" ]] || die "usage: privacy <grant|revoke|reset> <photos|camera|microphone|location|contacts|calendar|...> <bundle-id>"
    xcrun simctl privacy "$U" "$action" "$service" "$bundle"
    ;;
  push)
    bundle=${1:?usage: push <bundle-id> <payload.json>}; payload=${2:?usage: push <bundle-id> <payload.json>}
    [ -f "$payload" ] || die "payload not found: $payload"
    xcrun simctl push "$U" "$bundle" "$payload"
    ;;
  location)
    v=${1:?usage: location <lat,lon|clear>}
    if [ "$v" = clear ]; then xcrun simctl location "$U" clear; else xcrun simctl location "$U" set "$v"; fi
    ;;
  statusbar)
    case "${1:-}" in
      clean) xcrun simctl status_bar "$U" override --time 9:41 --dataNetwork wifi --wifiBars 3 --cellularBars 4 --batteryState charged --batteryLevel 100 ;;
      clear) xcrun simctl status_bar "$U" clear ;;
      *) die "usage: statusbar <clean|clear>" ;;
    esac
    ;;
  log)
    proc=${1:?usage: log <process-name> [seconds]}; secs=${2:-0}
    if [ "$secs" = 0 ]; then
      xcrun simctl spawn "$U" log show --last 2m --style compact --predicate "process == \"$proc\"" | tail -150
    else
      xcrun simctl spawn "$U" log stream --style compact --predicate "process == \"$proc\"" & lp=$!
      sleep "$secs"; kill "$lp" 2>/dev/null || true
    fi
    ;;
  crashes)
    dir="$HOME/Library/Logs/DiagnosticReports"
    find "$dir" -maxdepth 1 \( -name '*.ips' -o -name '*.crash' \) -mmin -120 2>/dev/null \
      | grep -i "${1:-.}" | head -10 || echo "no crash reports in the last 2 hours"
    ;;
  device-install)
    [ -n "${IOS_QA_UDID:-}" ] || die "set IOS_QA_UDID to the device id from: xcrun devicectl list devices"
    xcrun devicectl device install app --device "$IOS_QA_UDID" "${1:?usage: device-install <App.app>}"
    ;;
  device-launch)
    [ -n "${IOS_QA_UDID:-}" ] || die "set IOS_QA_UDID to the device id from: xcrun devicectl list devices"
    xcrun devicectl device process launch --device "$IOS_QA_UDID" "${1:?usage: device-launch <bundle-id>}"
    ;;
  device-shot)
    file=${1:?usage: device-shot <file.png>}
    command -v pymobiledevice3 >/dev/null 2>&1 || die "device screenshots need pymobiledevice3 (pip install pymobiledevice3) or an XCUITest attachment"
    pymobiledevice3 developer dvt screenshot "$file" && echo "$file"
    ;;
  help|-h|--help) usage ;;
  *) usage; exit 2 ;;
esac
