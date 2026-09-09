#!/usr/bin/env python3
"""Render a full article page body from articles.json."""
from __future__ import annotations

import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from render_sidebar import render_sidebar  # noqa: E402
from navigation import article_url, hub_url, load_navigation, nav_slugs, title_for_slug  # noqa: E402
from inline_images import inline_slug_images  # noqa: E402


def heading_tag(level: int) -> str:
    level = max(2, min(4, level))
    return f"h{level}"


def render_callout(callout: dict) -> str:
    ctype = html.escape(callout.get("type", "note"))
    title = html.escape(callout.get("title", "Note"))
    body = callout.get("html", "")
    return (
        f'<div class="unpkl-docs-callout unpkl-docs-callout--{ctype}">'
        f'<p class="unpkl-docs-callout__title">{title}</p>{body}</div>'
    )


def render_sections(article: dict) -> str:
    callouts_by_anchor = {}
    intro_callouts: list[str] = []
    trailing_callouts: list[str] = []
    for callout in article.get("callouts", []):
        block = render_callout(callout)
        if callout.get("position") == "intro":
            intro_callouts.append(block)
            continue
        after = callout.get("after")
        if after:
            callouts_by_anchor.setdefault(after, []).append(block)
        else:
            trailing_callouts.append(block)

    parts: list[str] = list(intro_callouts)
    for section in article.get("sections", []):
        tag = heading_tag(section.get("level", 2))
        sid = html.escape(section["id"])
        title = html.escape(section["title"])
        parts.append(f'<{tag} id="{sid}">{title}</{tag}>')
        parts.append(section.get("html", ""))
        for block in callouts_by_anchor.get(section["id"], []):
            parts.append(block)

    parts.extend(trailing_callouts)
    return "\n".join(parts)


def render_toc(sections: list[dict]) -> str:
    items = []
    for section in sections:
        level = section.get("level", 2)
        level_attr = ' data-level="3"' if level >= 3 else ""
        sid = html.escape(section["id"])
        title = html.escape(section["title"])
        items.append(f'<li><a href="#{sid}"{level_attr}>{title}</a></li>')
    return (
        '<aside class="unpkl-docs-toc unpkl-docs-toc--inline" aria-label="In this article">'
        '<p class="unpkl-docs-toc__title">In this article</p>'
        f"<ul>{''.join(items)}</ul></aside>"
    )


def render_related(related_slugs: list[str], articles: dict, nav: dict) -> str:
    if not related_slugs:
        return ""

    nav_slug_set = set(nav_slugs(nav))
    links = []
    for slug in related_slugs:
        if slug not in nav_slug_set or slug not in articles:
            continue
        url = html.escape(article_url(slug, nav))
        label = html.escape(title_for_slug(slug, nav, articles))
        links.append(f'<li><a href="{url}">{label}</a></li>')

    if not links:
        return ""

    return (
        '<section class="unpkl-docs-related"><h2>Related content</h2>'
        f"<ul>{''.join(links)}</ul></section>"
    )


def render_article_page(slug: str, nav: dict, articles: dict) -> str:
    article = articles[slug]
    url = article_url(slug, nav)
    hub = html.escape(hub_url(nav))
    title = html.escape(article["title"])
    lead = article.get("lead", "")
    sidebar = render_sidebar(nav, url)
    toc = render_toc(article.get("sections", []))
    body = render_sections(article)
    related = render_related(article.get("related", []), articles, nav)

    return inline_slug_images(
        slug,
        f"""<div class="unpkl-docs-root unpkl-docs-root--dark unpkl-docs-root--article" data-docs-page="article">

  <nav class="unpkl-docs-sidebar" aria-label="Documentation">
{sidebar}
  </nav>

  <main class="unpkl-docs-main">
    <div class="unpkl-docs-content">
      <nav class="unpkl-docs-breadcrumb" aria-label="Breadcrumb">
        <ol>
          <li><a href="/">Home</a></li>
          <li><a href="{hub}">Documentation</a></li>
          <li><span aria-current="page">{title}</span></li>
        </ol>
      </nav>

{toc}

      <article class="unpkl-docs-article">
        <header>
          <h1 class="unpkl-docs-page-title">{title}</h1>
          <p class="unpkl-docs-lead">{lead}</p>
        </header>

{body}
      </article>

      <footer class="unpkl-docs-article-footer">
        {related}
      </footer>
    </div>
  </main>
</div>""",
    )


def main() -> None:
    slug = sys.argv[1]
    nav = load_navigation()
    articles = json.loads((ROOT / "config" / "articles.json").read_text(encoding="utf-8"))
    if slug not in articles:
        raise SystemExit(f"Unknown article slug: {slug}")
    print(render_article_page(slug, nav, articles))


if __name__ == "__main__":
    main()
