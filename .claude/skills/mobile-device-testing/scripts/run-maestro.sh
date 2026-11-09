#!/usr/bin/env bash
# Run Maestro flows and store artifacts. Usage: run-maestro.sh <flow.yaml|dir> [extra maestro args]
set -euo pipefail

command -v maestro >/dev/null 2>&1 || { echo "error: maestro not found (see https://maestro.mobile.dev)" >&2; exit 1; }

target="${1:?usage: run-maestro.sh <flow.yaml|dir> [extra maestro args]}"
shift || true

out="artifacts/maestro-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$out"

maestro test "$target" --format junit --output "$out/report.xml" --debug-output "$out/debug" "$@"
echo "artifacts: $out"
