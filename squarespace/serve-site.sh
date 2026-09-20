#!/usr/bin/env bash
# Serve ../dist under the project Pages base path for local preview.
# Usage: ./serve-site.sh [port]
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$ROOT/.." && pwd)"
DIST="$REPO/dist"
PORT="${1:-8080}"

if [[ ! -f "$DIST/index.html" ]]; then
  echo "No dist/ yet — run ./build-site.sh first" >&2
  exit 1
fi

BASE="$(python3 -c "
import sys
sys.path.insert(0, '$ROOT/scripts')
from navigation import load_navigation, base_url
print(base_url(load_navigation()).lstrip('/') or '.')
")"

PREVIEW="$(mktemp -d /tmp/unpkl-docs-preview.XXXXXX)"
cleanup() { rm -rf "$PREVIEW"; }
trap cleanup EXIT

if [[ "$BASE" == "." ]]; then
  TARGET="$PREVIEW"
else
  TARGET="$PREVIEW/$BASE"
  mkdir -p "$TARGET"
fi
cp -R "$DIST"/. "$TARGET"/

echo "Preview: http://127.0.0.1:${PORT}/$( [[ "$BASE" == "." ]] && echo '' || echo "$BASE/" )"
echo "Serving $TARGET"
cd "$PREVIEW"
exec python3 -m http.server "$PORT"
