#!/usr/bin/env bash
# Build the static GitHub Pages site into ../../dist (repo root).
#
# Usage:
#   ./build-site.sh
#   ./build-site.sh --generate-search
#   ./build-site.sh --skip-compress
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
exec python3 scripts/build_site.py "$@"
