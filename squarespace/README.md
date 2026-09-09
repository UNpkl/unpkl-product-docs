# Squarespace product docs

Microsoft Learn-style tree navigation. The left sidebar, page list, and URLs all come from **`config/navigation.json`** — one edit + `./build-pages.sh` updates every page.

```bash
./build-pages.sh
python3 scripts/validate_navigation.py   # check nav ↔ articles ↔ paste files
```

| Output | Use |
|--------|-----|
| `blocks/hub-page/paste-into-code-block.html` | `/how-to` hub |
| `blocks/pages/<slug>/paste-into-code-block.html` | Each article (`pageUrlPrefix` + slug) |
| `blocks/pages/manifest.txt` | Slug → URL → title checklist for Squarespace |

**Navigation:** list each page once with `"slug": "search-and-command"` and `"title": "…"` in `navigation.json`. Do not repeat full `/how-to-*` URLs.

Article body: `blocks/pages/<slug>/<slug>.txt` or `config/articles.json`. Markup: [`TEXT-FORMAT.md`](TEXT-FORMAT.md).

See [`DEPLOY.md`](DEPLOY.md).
