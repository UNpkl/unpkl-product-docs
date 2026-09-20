# UNpkl Product Documentation

Product docs for UNpkl devices, SaaS, DNS firewall, and cloud management.

**Live site:** [https://unpkl.github.io/unpkl-product-docs/](https://unpkl.github.io/unpkl-product-docs/)

| Path | Role |
|------|------|
| [`squarespace/`](squarespace/) | Authoring (`.txt`), build scripts, assets; also legacy Squarespace paste output |
| [`dist/`](dist/) | Static site output from `./squarespace/build-site.sh` (gitignored; built in CI) |
| [`.github/workflows/pages.yml`](.github/workflows/pages.yml) | Deploy to GitHub Pages on push to `main` |

```bash
cd squarespace
./build-site.sh          # → ../dist
# optional legacy paste files:
./build-pages.sh
```

Markup: [`squarespace/TEXT-FORMAT.md`](squarespace/TEXT-FORMAT.md)  
Deploy: [`squarespace/DEPLOY.md`](squarespace/DEPLOY.md)  
Cutover from Squarespace: [`squarespace/CUTOVER.md`](squarespace/CUTOVER.md)
