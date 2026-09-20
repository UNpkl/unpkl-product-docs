# Squarespace → GitHub Pages cutover

Published docs: **https://unpkl.github.io/unpkl-product-docs/**

## After the first successful Actions deploy

1. **Verify** hub + a few articles (nav, images, copy buttons, Zero Trust, EasyMesh).
2. **Squarespace `/how-to` hub** — replace the Code block with a short notice, for example:

   ```html
   <p>UNpkl product documentation has moved.</p>
   <p><a href="https://unpkl.github.io/unpkl-product-docs/">Open the docs on GitHub Pages</a></p>
   ```

3. **Optional:** On each old `/how-to-*` Squarespace page, paste the same notice (or delete those pages once analytics show traffic has moved).
4. **Update links** that still point at `unpkl.io/how-to` or `/how-to-*`:
   - Marketing site / footer
   - App help / “Learn more” URLs
   - README badges
5. **Stop editing** Squarespace Code blocks for docs. Edit `.txt` / `navigation.json` in this repo and push `main`.
6. Keep `./build-pages.sh` only if you still need paste HTML temporarily; day-to-day use `./build-site.sh` / CI.

## URL mapping

| Old (Squarespace) | New (GitHub Pages) |
|-------------------|--------------------|
| `/how-to` | `/unpkl-product-docs/` |
| `/how-to-initial-setup` | `/unpkl-product-docs/initial-setup/` |
| `/how-to-search-and-command` | `/unpkl-product-docs/search-and-command/` |
| `/how-to-zero-trust` | `/unpkl-product-docs/zero-trust/` |
| `/how-to-<slug>` | `/unpkl-product-docs/<slug>/` |
