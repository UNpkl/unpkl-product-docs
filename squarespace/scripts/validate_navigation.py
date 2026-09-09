#!/usr/bin/env python3
"""Validate navigation.json against articles and page folders."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from navigation import load_navigation, nav_slugs, title_for_slug  # noqa: E402

ARTICLES_PATH = ROOT / "config" / "articles.json"
PAGES = ROOT / "blocks" / "pages"


def main() -> int:
    nav = load_navigation()
    articles = json.loads(ARTICLES_PATH.read_text(encoding="utf-8"))
    slugs = nav_slugs(nav)
    errors: list[str] = []

    for slug in slugs:
        if slug not in articles:
            errors.append(f"navigation slug '{slug}' missing from articles.json")
        page_dir = PAGES / slug
        if not (page_dir / "paste-into-code-block.html").is_file():
            errors.append(f"no paste file for '{slug}' (run ./build-pages.sh)")

    for slug in articles:
        if slug not in slugs:
            errors.append(
                f"articles.json has '{slug}' but it is not in navigation.json "
                f"(add slug or remove article)"
            )

    for slug in slugs:
        for other_slug in articles.get(slug, {}).get("related", []):
            if other_slug not in slugs:
                errors.append(
                    f"{slug} @related references '{other_slug}' which is not in navigation.json"
                )

    if errors:
        print("Navigation validation failed:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    print(f"OK: {len(slugs)} pages in navigation.json")
    for slug in slugs:
        print(f"  {slug} → {title_for_slug(slug, nav, articles)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
