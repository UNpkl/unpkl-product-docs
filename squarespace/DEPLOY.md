# Squarespace deploy guide

Squarespace does **not** support page subfolders. Use flat URLs:

- Hub: `/how-to`
- Articles: `/how-to-initial-setup`, `/how-to-search-and-command`, etc.

```bash
cd squarespace && ./build-pages.sh
```

## Hub

Paste **`blocks/hub-page/paste-into-code-block.html`** on the page with slug **`how-to`**.

## Article pages

See **`blocks/pages/manifest.txt`** — create one Squarespace page per row:

| Squarespace slug | Paste file |
|------------------|------------|
| `how-to-initial-setup` | `blocks/pages/initial-setup/paste-into-code-block.html` |
| `how-to-search-and-command` | `blocks/pages/search-and-command/...` |
| … | … |

Each page: one Code block, HTML mode, Display Source Code OFF.

### Copy buttons (`{copy}` code blocks)

Squarespace **removes `<script>` tags** from Code blocks, so copy buttons use an **inline `onclick` handler** on each button (generated at build time). After updating FAQ or any page with `{copy}` fences, re-paste that page’s HTML.

If Copy still does nothing on your site, paste **`blocks/site-footer-copy-snippet.html`** once into **Settings → Advanced → Code Injection → Footer**. Commands remain selectable in the textarea as a manual fallback (click the command, then ⌘C / Ctrl+C).

## Edit content

- **`config/navigation.json`** — **single source of truth** for the left tree, page slugs, and Squarespace URLs. Edit this file only; then run `./build-pages.sh` to refresh every page’s sidebar (no per-page slug edits).
- **`TEXT-FORMAT.md`** — article markup (sections, images, callouts)
- `blocks/pages/<slug>/<slug>.txt` — article body (synced to `articles.json` on build)
- `config/articles.json` — article content JSON

### Navigation (`navigation.json`)

Each article is listed once with a stable **`slug`** (folder name). URLs are derived at build time:

```json
{ "slug": "search-and-command", "title": "Search & command", "description": "…" }
```

→ Squarespace page `/how-to-search-and-command` (from `pageUrlPrefix` + slug).

**To change the tree:** edit section titles, reorder items, add/remove `{ "slug": "…", "title": "…" }` entries, then:

```bash
./build-pages.sh
python3 scripts/validate_navigation.py   # optional check
```

Re-paste updated `paste-into-code-block.html` files (all pages get the new sidebar from one config). Create new Squarespace pages using `blocks/pages/manifest.txt`.

You do **not** edit URLs inside each paste file or repeat `/how-to-*` paths in navigation — only `slug` + optional global `pageUrlPrefix` / `hubUrl`.
