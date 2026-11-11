#!/usr/bin/env bash
# QA run helper (bash, git, curl).
#   qa-run.sh init <label> [dir]   create <dir or artifacts/qa>/<label>-<UTC>/ with report.md,
#                                  print branch, base, tree state and changed files
#   qa-run.sh ports                list local dev servers that answer HTTP
#   qa-run.sh issue <run-dir>      print the next free ISSUE-NNN id for that run
#   qa-run.sh scope                files changed on this branch versus the base branch
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

die() { echo "qa-run: $*" >&2; exit 2; }

base_branch() {
  local ref
  ref=$(git symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null || true)
  if [ -n "$ref" ]; then echo "${ref#origin/}"; return; fi
  for b in main master develop; do
    if git show-ref --verify --quiet "refs/heads/$b" || git show-ref --verify --quiet "refs/remotes/origin/$b"; then
      echo "$b"; return
    fi
  done
  echo ""
}

changed_files() {
  local base
  base=$(base_branch)
  [ -n "$base" ] || { echo "(no base branch found)"; return; }
  local ref="$base"
  git show-ref --verify --quiet "refs/remotes/origin/$base" && ref="origin/$base"
  git diff --name-only "$ref"...HEAD 2>/dev/null | head -200
}

cmd=${1:-help}
case "$cmd" in
  init)
    label=${2:-}
    [ -n "$label" ] || die "usage: qa-run.sh init <label> [dir]"
    label=$(printf '%s' "$label" | tr '[:upper:]' '[:lower:]' | tr -cs 'a-z0-9' '-' | sed 's/^-*//; s/-*$//' | cut -c1-40)
    [ -n "$label" ] || die "label must contain letters or digits"
    git rev-parse --is-inside-work-tree >/dev/null 2>&1 || die "not inside a git repository"
    root=$(git rev-parse --show-toplevel)
    dirty=$(git status --porcelain | wc -l | tr -d ' ')
    # Keep QA evidence out of commits without touching the project's .gitignore.
    exclude="$(git rev-parse --git-path info/exclude)"
    if ! git check-ignore -q "$root/artifacts/qa/x" 2>/dev/null; then
      mkdir -p "$(dirname "$exclude")"
      echo "artifacts/qa/" >> "$exclude"
    fi
    parent=${3:-"$root/artifacts/qa"}
    stamp=$(date -u +%Y%m%dT%H%M%SZ)
    run="$parent/$label-$stamp"
    n=1
    while [ -e "$run" ]; do n=$((n + 1)); run="$parent/$label-$stamp-$n"; done
    mkdir -p "$run/evidence"
    cp "$here/../references/report-template.md" "$run/report.md"
    echo "RUN_DIR=$run"
    echo "BRANCH=$(git branch --show-current 2>/dev/null || echo detached)"
    echo "COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo none)"
    echo "BASE=$(base_branch)"
    if [ "$dirty" = "0" ]; then echo "TREE=clean"; else echo "TREE=dirty ($dirty paths): commit or stash before fixing"; fi
    echo "CHANGED_FILES:"
    changed_files | sed 's/^/  /'
    ;;
  ports)
    found=0
    for p in 3000 3001 4000 4173 4200 5000 5173 5174 8000 8080 8081 8888 9000; do
      code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 2 "http://localhost:$p/" 2>/dev/null || true)
      if [ -n "$code" ] && [ "$code" != "000" ]; then echo "http://localhost:$p/ HTTP $code"; found=1; fi
    done
    [ "$found" = 1 ] || echo "no local server answered on common ports"
    ;;
  issue)
    run=${2:-}
    [ -d "$run" ] || die "usage: qa-run.sh issue <run-dir>"
    last=$( (grep -rhoE 'ISSUE-[0-9]{3,}' "$run" 2>/dev/null || true) | sed 's/ISSUE-//' | sort -n | tail -1)
    printf 'ISSUE-%03d\n' $((10#${last:-0} + 1))
    ;;
  scope)
    git rev-parse --is-inside-work-tree >/dev/null 2>&1 || die "not inside a git repository"
    echo "BASE=$(base_branch)"
    changed_files
    ;;
  help|-h|--help)
    sed -n '2,7p' "$0" | sed 's/^# \{0,1\}//'
    ;;
  *)
    die "unknown command: $cmd (try help)"
    ;;
esac
