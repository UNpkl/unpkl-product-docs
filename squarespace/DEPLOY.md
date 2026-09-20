# Deploying docs

## GitHub Pages (primary)

Docs publish automatically from `main` via GitHub Actions to:

**https://unpkl.github.io/unpkl-product-docs/**

```bash
# Local preview build
cd squarespace && ./build-site.sh
# Open dist/ locally (use a static server so /unpkl-product-docs base path works), e.g.:
#   cd .. && python3 -m http.server 8080
# then visit http://localhost:8080/unpkl-product-docs/
```

Config:

- [`config/navigation.json`](config/navigation.json) — `baseUrl` (`/unpkl-product-docs` for project Pages; set to `""` for a custom domain at site root), `homeUrl`, tree slugs
- Authoring: `blocks/pages/<slug>/*.txt` — see [`TEXT-FORMAT.md`](TEXT-FORMAT.md)
- Build: `./build-site.sh` → repo-root `dist/`

### Enable Pages (one-time)

1. Repo **Settings → Pages → Build and deployment → Source: GitHub Actions**
2. Push to `main` (or run the **Deploy GitHub Pages** workflow manually)
3. Wait for the workflow; site appears at the URL above

### Custom domain (later)

1. Add DNS CNAME (or A/ALIAS) for e.g. `docs.unpkl.com` → GitHub Pages
2. Set `"baseUrl": ""` in `navigation.json`
3. Optionally add `CNAME` file under `dist/` via the build
4. Rebuild and redeploy

## Squarespace (legacy / transition)

Flat paste files are still produced by `./build-pages.sh` for the old Code-block workflow. Prefer GitHub Pages for all new updates.

During cutover, replace Squarespace `/how-to` content with a short notice linking to the Pages URL (see [`CUTOVER.md`](CUTOVER.md)).
