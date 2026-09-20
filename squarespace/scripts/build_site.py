#!/usr/bin/env python3
"""Build the static GitHub Pages site into dist/.

Writes:
  dist/index.html
  dist/<slug>/index.html
  dist/assets/*
  dist/<slug>/*.(jpg|png|…)  (page images referenced by articles)
  dist/.nojekyll
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent
sys.path.insert(0, str(ROOT / "scripts"))

from document_shell import render_hub_body, wrap_document  # noqa: E402
from navigation import (  # noqa: E402
    hub_url,
    load_navigation,
    nav_slugs,
    render_hub_overview_html,
    render_hub_quick_reference_html,
)
from render_article import render_article_document  # noqa: E402
from render_sidebar import render_sidebar  # noqa: E402

DEFAULT_DIST = REPO_ROOT / "dist"
BLOCKS_PAGES = ROOT / "blocks" / "pages"
ASSETS = ROOT / "assets"
ARTICLES_PATH = ROOT / "config" / "articles.json"
IMG_SRC_RE = re.compile(
    r'<img\b[^>]*\bsrc="([^":/][^"]*)"',
    re.IGNORECASE,
)


def ensure_image_venv() -> Path:
    venv_python = ROOT / ".venv" / "bin" / "python"
    if not venv_python.is_file():
        subprocess.check_call([sys.executable, "-m", "venv", str(ROOT / ".venv")])
        subprocess.check_call(
            [
                str(ROOT / ".venv" / "bin" / "pip"),
                "install",
                "-r",
                str(ROOT / "requirements.txt"),
                "-q",
            ]
        )
    return venv_python


def compress_slug_images(slug: str) -> None:
    page_dir = BLOCKS_PAGES / slug
    if not page_dir.is_dir():
        return
    images = list(page_dir.glob("*.png")) + list(page_dir.glob("*.jpg"))
    images += list(page_dir.glob("*.jpeg")) + list(page_dir.glob("*.webp"))
    if not images:
        return
    python = ensure_image_venv()
    subprocess.check_call([str(python), str(ROOT / "scripts" / "compress_page_images.py"), slug])


def sync_articles(generate_search: bool = False) -> None:
    if generate_search:
        gen = ROOT / "scripts" / "generate_search_and_command_txt.py"
        if gen.is_file():
            subprocess.check_call(
                [
                    sys.executable,
                    str(gen),
                    "--app-root",
                    str(Path.home() / "unpkl-app"),
                    "--wireless-root",
                    str(Path.home() / "unpkl-github" / "yh" / "yhioe" / "yh-wireless"),
                ]
            )
    subprocess.check_call([sys.executable, str(ROOT / "scripts" / "sync_txt_to_articles.py")])


def copy_assets(dist: Path) -> None:
    dest = dist / "assets"
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(ASSETS, dest)


def copy_page_images(slug: str, html: str, dest_dir: Path) -> None:
    page_dir = BLOCKS_PAGES / slug
    dest_dir.mkdir(parents=True, exist_ok=True)
    for match in IMG_SRC_RE.finditer(html):
        filename = match.group(1)
        src = page_dir / filename
        if src.is_file():
            shutil.copy2(src, dest_dir / filename)


def build_hub(nav: dict, dist: Path) -> None:
    sidebar = render_sidebar(nav, hub_url(nav), linked_assets=True)
    overview = render_hub_overview_html(nav)
    quick_ref = render_hub_quick_reference_html(nav)
    body = render_hub_body(nav, sidebar, overview, quick_ref)
    title = nav.get("hubTitle") or "How to UN-pickle"
    doc = wrap_document(
        f"{title} · UNpkl Docs",
        body,
        nav,
        description="Product documentation for UNpkl devices, SaaS, DNS firewall, and cloud management.",
    )
    (dist / "index.html").write_text(doc, encoding="utf-8")


def build_articles(nav: dict, articles: dict, dist: Path) -> list[str]:
    built: list[str] = []
    for slug in nav_slugs(nav):
        if slug not in articles:
            raise SystemExit(f"Missing article for nav slug: {slug}")
        doc = render_article_document(slug, nav, articles)
        out_dir = dist / slug
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "index.html").write_text(doc, encoding="utf-8")
        copy_page_images(slug, doc, out_dir)
        built.append(slug)
    return built


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dist",
        type=Path,
        default=DEFAULT_DIST,
        help=f"Output directory (default: {DEFAULT_DIST})",
    )
    parser.add_argument(
        "--generate-search",
        action="store_true",
        help="Regenerate search-and-command.txt before sync",
    )
    parser.add_argument(
        "--skip-compress",
        action="store_true",
        help="Skip image compression step",
    )
    args = parser.parse_args()
    dist: Path = args.dist.resolve()

    nav = load_navigation()
    slugs = nav_slugs(nav)

    if not args.skip_compress:
        for slug in slugs:
            compress_slug_images(slug)

    sync_articles(generate_search=args.generate_search)
    articles = json.loads(ARTICLES_PATH.read_text(encoding="utf-8"))

    if dist.exists():
        shutil.rmtree(dist)
    dist.mkdir(parents=True)

    copy_assets(dist)
    build_hub(nav, dist)
    built = build_articles(nav, articles, dist)
    (dist / ".nojekyll").write_text("", encoding="utf-8")

    print(f"Wrote site → {dist}")
    print(f"  hub: index.html")
    print(f"  articles: {len(built)}")
    for slug in built:
        print(f"    {slug}/")


if __name__ == "__main__":
    main()
