#!/usr/bin/env bash
# Helper for the context-save skill.
#   context.sh state          print git state for the checkpoint
#   context.sh path "<title>" print a new, collision-free checkpoint path (creates the folder)
set -euo pipefail

root=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
dir="$root/.context/checkpoints"

case "${1:-}" in
  state)
    echo "branch: $(git -C "$root" rev-parse --abbrev-ref HEAD 2>/dev/null || echo none)"
    echo "head: $(git -C "$root" rev-parse --short HEAD 2>/dev/null || echo none)"
    echo "--- status"
    git -C "$root" status --short 2>/dev/null || true
    echo "--- recent commits"
    git -C "$root" log --oneline -5 2>/dev/null || true
    echo "--- diff stat"
    git -C "$root" diff --stat HEAD 2>/dev/null || true
    ;;
  path)
    title=${2:-checkpoint}
    slug=$(printf '%s' "$title" | tr '[:upper:]' '[:lower:]' | tr -cs 'a-z0-9' '-' | sed 's/^-//;s/-$//' | cut -c1-50)
    mkdir -p "$dir"
    # keep checkpoints out of git without touching the user's .gitignore
    exclude="$root/.git/info/exclude"
    if [ -d "$root/.git/info" ] && ! grep -qx '.context/' "$exclude" 2>/dev/null; then
      echo '.context/' >> "$exclude"
    fi
    base="$dir/$(date +%Y%m%d-%H%M%S)-${slug:-checkpoint}"
    file="$base.md"
    n=1
    while [ -e "$file" ]; do n=$((n + 1)); file="$base-$n.md"; done
    echo "$file"
    ;;
  *)
    echo "usage: context.sh state | path <title>" >&2
    exit 2
    ;;
esac
