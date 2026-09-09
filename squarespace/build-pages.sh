#!/usr/bin/env bash
# Build hub + one paste file per article page (hyphenated slugs under /how-to/).
#
# Usage:
#   ./build-pages.sh                    # sync all .txt → articles.json, render HTML
#   ./build-pages.sh --generate-search  # regenerate search-and-command.txt from app/firmware sources first
#
# Manual edits to blocks/pages/<slug>/<slug>.txt are preserved unless you pass --generate-search
# (search-and-command only) or set GENERATE_SEARCH_AND_COMMAND=1.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
CSS="$ROOT/assets/unpkl-docs.css"
NAV="$ROOT/config/navigation.json"
TEMPLATES="$ROOT/templates"
BLOCKS="$ROOT/blocks"
RENDER_SIDEBAR="$ROOT/scripts/render_sidebar.py"
RENDER_ARTICLE="$ROOT/scripts/render_article.py"
SYNC_TXT="$ROOT/scripts/sync_txt_to_articles.py"
COMPRESS_IMAGES="$ROOT/scripts/compress_page_images.py"
GENERATE_SEARCH="$ROOT/scripts/generate_search_and_command_txt.py"

GENERATE_SEARCH_AND_COMMAND="${GENERATE_SEARCH_AND_COMMAND:-0}"
for arg in "$@"; do
  case "$arg" in
    --generate-search)
      GENERATE_SEARCH_AND_COMMAND=1
      ;;
  esac
done

ensure_image_venv() {
  if [[ ! -x "$ROOT/.venv/bin/python" ]]; then
    python3 -m venv "$ROOT/.venv"
    "$ROOT/.venv/bin/pip" install -r "$ROOT/requirements.txt" -q
  fi
}

mkdir -p "$BLOCKS/hub-page" "$BLOCKS/pages"

# Compress page images before sync so articles.json references .jpg outputs.
compress_slug_images() {
  local slug="$1"
  local slug_dir="$BLOCKS/pages/$slug"
  if [[ ! -d "$slug_dir" ]]; then
    return
  fi
  shopt -s nullglob
  local slug_images=( "$slug_dir"/*.png "$slug_dir"/*.jpg "$slug_dir"/*.jpeg "$slug_dir"/*.webp )
  shopt -u nullglob
  if [[ ${#slug_images[@]} -gt 0 ]]; then
    ensure_image_venv
    "$ROOT/.venv/bin/python" "$COMPRESS_IMAGES" "$slug"
  fi
}

pre_compress_slugs="$(python3 -c "
import sys
sys.path.insert(0, '$ROOT/scripts')
from navigation import load_navigation, nav_slugs
print('\n'.join(nav_slugs(load_navigation())))
")"
while IFS= read -r slug; do
  [[ -z "$slug" ]] && continue
  compress_slug_images "$slug"
done <<< "$pre_compress_slugs"

if [[ -x "$SYNC_TXT" ]] || [[ -f "$SYNC_TXT" ]]; then
  if [[ "$GENERATE_SEARCH_AND_COMMAND" == "1" ]] && [[ -f "$GENERATE_SEARCH" ]]; then
    python3 "$GENERATE_SEARCH" \
      --app-root "${UNPKL_APP_ROOT:-$HOME/unpkl-app}" \
      --wireless-root "${YH_WIRELESS_ROOT:-$HOME/unpkl-github/yh/yhioe/yh-wireless}"
  fi
  python3 "$SYNC_TXT"
fi

prepare_hub_body() {
  local sidebar
  sidebar="$(python3 "$RENDER_SIDEBAR" "$NAV" "/how-to")"
  local overview
  overview="$(python3 -c "
import sys
sys.path.insert(0, '$ROOT/scripts')
from navigation import load_navigation, render_hub_overview_html
print(render_hub_overview_html(load_navigation()))
")"
  quick_ref="$(python3 -c "
import sys
sys.path.insert(0, '$ROOT/scripts')
from navigation import load_navigation, render_hub_quick_reference_html
print(render_hub_quick_reference_html(load_navigation()))
")"
  local body
  body="$(cat "$TEMPLATES/hub-page.html")"
  body="${body//<!-- UNPKL_SIDEBAR -->/$sidebar}"
  body="${body//<!-- UNPKL_HUB_OVERVIEW -->/$overview}"
  body="${body//<!-- UNPKL_HUB_QUICK_REF -->/$quick_ref}"
  body="$(python3 -c "
import re, sys
print(re.sub(r'<!--.*?-->', '', sys.stdin.read(), flags=re.DOTALL).strip())
" <<< "$body")"
  printf '%s' "$body"
}

write_paste_file() {
  local out_path="$1"
  local body="$2"
  mkdir -p "$(dirname "$out_path")"
  cat > "$out_path" <<EOF
<style>
$(cat "$CSS")
</style>

$body
EOF
}

hub_body="$(prepare_hub_body)"
write_paste_file "$BLOCKS/hub-page/paste-into-code-block.html" "$hub_body"

# All article slugs from navigation.json (single source of truth)
slugs="$(python3 -c "
import sys
sys.path.insert(0, '$ROOT/scripts')
from navigation import load_navigation, nav_slugs, article_url
nav = load_navigation()
for slug in nav_slugs(nav):
    print(slug)
")"

manifest="$BLOCKS/pages/manifest.txt"
: > "$manifest"

while IFS= read -r slug; do
  [[ -z "$slug" ]] && continue
  compress_slug_images "$slug"
  body="$(python3 "$RENDER_ARTICLE" "$slug")"
  out_dir="$BLOCKS/pages/$slug"
  write_paste_file "$out_dir/paste-into-code-block.html" "$body"
  title="$(python3 -c "import json; a=json.load(open('$ROOT/config/articles.json')); print(a['$slug']['title'])")"
  page_url="$(python3 -c "
import sys
sys.path.insert(0, '$ROOT/scripts')
from navigation import load_navigation, article_url
print(article_url('$slug', load_navigation()))
")"
  echo "$slug | $page_url | $title" >> "$manifest"
done <<< "$slugs"

# Remove page folders not listed in navigation.json (stale builds)
python3 -c "
import shutil
import sys
from pathlib import Path
sys.path.insert(0, '$ROOT/scripts')
from navigation import load_navigation, nav_slugs
pages = Path('$BLOCKS/pages')
allowed = set(nav_slugs(load_navigation()))
for folder in pages.iterdir():
    if not folder.is_dir() or folder.name.startswith('.'):
        continue
    if folder.name not in allowed:
        shutil.rmtree(folder)
        print(f'Removed stale page folder: {folder.name}')
"

rm -rf "$BLOCKS/article-page"

echo "Wrote hub: blocks/hub-page/paste-into-code-block.html"
echo "Wrote $(echo "$slugs" | grep -c .) article pages under blocks/pages/<slug>/"
echo "Squarespace page list: blocks/pages/manifest.txt"
