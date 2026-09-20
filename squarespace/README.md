# Squarespace product docs (authoring + builds)

Microsoft Learn-style tree navigation. The left sidebar, page list, and URLs all come from **`config/navigation.json`** — one edit + build updates the whole site.

```bash
./build-site.sh                 # GitHub Pages static site → ../dist
./build-pages.sh                # legacy Squarespace paste HTML (optional)
python3 scripts/validate_navigation.py
```

| Output | Use |
|--------|-----|
| `../dist/` | GitHub Pages (CI deploys this) |
| `blocks/hub-page/paste-into-code-block.html` | Legacy Squarespace hub paste |
| `blocks/pages/<slug>/paste-into-code-block.html` | Legacy Squarespace article paste |
| `blocks/pages/manifest.txt` | Slug checklist |

**Navigation:** list each page once with `"slug": "search-and-command"` in `navigation.json`. For GitHub Pages, URLs are `{baseUrl}/{slug}/` (see `baseUrl` in that file).

Article body: `blocks/pages/<slug>/<slug>.txt`. Markup: [`TEXT-FORMAT.md`](TEXT-FORMAT.md).

See [`DEPLOY.md`](DEPLOY.md) and [`CUTOVER.md`](CUTOVER.md).
