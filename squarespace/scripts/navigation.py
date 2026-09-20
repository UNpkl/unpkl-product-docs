"""Load navigation.json — single source of truth for tree, URLs, and page list."""
from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Iterator

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_NAV_PATH = ROOT / "config" / "navigation.json"


def base_url(nav: dict | None) -> str:
    """Site root prefix for GitHub Pages (e.g. /unpkl-product-docs). Empty for domain root."""
    if not nav:
        return ""
    return str(nav.get("baseUrl") or "").rstrip("/")


def home_url(nav: dict | None = None) -> str:
    if nav and nav.get("homeUrl"):
        return str(nav["homeUrl"]).rstrip("/") or "/"
    return "https://unpkl.io"


def hub_url(nav: dict) -> str:
    base = base_url(nav)
    if base or "baseUrl" in nav:
        return f"{base}/" if base else "/"
    return (nav.get("hubUrl") or "/how-to").rstrip("/") or "/how-to"


def page_prefix(nav: dict) -> str:
    """Legacy Squarespace flat-prefix (/how-to-). Unused when baseUrl is set."""
    return nav.get("pageUrlPrefix") or "/how-to-"


def article_url(slug: str, nav: dict | None = None) -> str:
    if nav is not None and ("baseUrl" in nav or base_url(nav)):
        base = base_url(nav)
        path = f"/{slug}/"
        return f"{base}{path}" if base else path
    if nav is not None and nav.get("baseUrl") == "":
        return f"/{slug}/"
    prefix = page_prefix(nav) if nav else "/how-to-"
    return f"{prefix}{slug}"


def asset_url(path: str, nav: dict | None = None) -> str:
    """Absolute-from-site-root URL for a static asset (css, js, icon)."""
    rel = path.lstrip("/")
    base = base_url(nav)
    return f"{base}/{rel}" if base else f"/{rel}"


def slug_from_url(url: str, nav: dict | None = None) -> str:
    normalized = (url or "").rstrip("/")
    if nav is not None and "baseUrl" in nav:
        base = base_url(nav)
        if base and normalized.startswith(base):
            rest = normalized[len(base) :].lstrip("/")
            return rest.split("/")[0] if rest else ""
        if normalized in ("", "/"):
            return ""
        return normalized.split("/")[-1]
    prefix = page_prefix(nav) if nav else "/how-to-"
    if normalized.startswith(prefix):
        return normalized[len(prefix) :]
    if normalized == hub_url(nav or {}).rstrip("/"):
        return ""
    return normalized.split("/")[-1]


def normalize_path(path: str) -> str:
    return (path or "/").rstrip("/") or "/"


def item_slug(item: dict, nav: dict | None = None) -> str:
    if item.get("slug"):
        return str(item["slug"]).strip()
    if item.get("url"):
        return slug_from_url(str(item["url"]), nav)
    raise ValueError(f"Nav item missing slug or url: {item!r}")


def item_url(item: dict, nav: dict) -> str:
    if item.get("url") and "baseUrl" not in nav:
        return str(item["url"]).rstrip("/") if item["url"] != hub_url(nav) else item["url"]
    return article_url(item_slug(item, nav), nav)


def normalize_item(item: dict, nav: dict) -> dict:
    """Ensure item has both slug and url."""
    slug = item_slug(item, nav)
    url = article_url(slug, nav)
    out = dict(item)
    out["slug"] = slug
    out["url"] = url
    return out


def normalize_nav(nav: dict) -> dict:
    """Return nav with slug+url on every item."""
    out = dict(nav)
    sections = []
    for section in nav.get("sections", []):
        sec = dict(section)
        sec["items"] = [normalize_item(item, nav) for item in section.get("items", [])]
        sections.append(sec)
    out["sections"] = sections
    return out


def load_navigation(path: Path | None = None) -> dict:
    nav_path = path or DEFAULT_NAV_PATH
    return normalize_nav(json.loads(nav_path.read_text(encoding="utf-8")))


def iter_items(nav: dict) -> Iterator[tuple[dict, dict]]:
    """Yield (section, normalized_item) in tree order."""
    for section in nav.get("sections", []):
        for item in section.get("items", []):
            yield section, normalize_item(item, nav)


def nav_slugs(nav: dict) -> list[str]:
    return [item_slug(item, nav) for _, item in iter_items(nav)]


def title_for_slug(slug: str, nav: dict, articles: dict | None = None) -> str:
    for _, item in iter_items(nav):
        if item_slug(item, nav) == slug:
            return item.get("title") or slug
    if articles and slug in articles:
        return articles[slug].get("title") or slug
    return slug


def section_has_active(section: dict, active: str | None, nav: dict) -> bool:
    if not active:
        return False
    active_norm = normalize_path(active)
    return any(normalize_path(item_url(item, nav)) == active_norm for item in section.get("items", []))


def render_hub_overview_html(nav: dict) -> str:
    """Hub page bullet list from nav sections (stays in sync with sidebar tree)."""
    parts: list[str] = []
    for section in nav.get("sections", []):
        title = section.get("title", "")
        if not title:
            continue
        parts.append(f"<li><strong>{html.escape(title)}</strong></li>")
    return f"<ul>{''.join(parts)}</ul>"


def render_hub_quick_reference_html(nav: dict) -> str:
    """Brief Search command examples for the documentation hub."""
    sac_url = html.escape(article_url("search-and-command", nav))
    examples = [
        (
            "Add Wi‑Fi network",
            "add wifi network GuestNet with password secret123 on 5ghz band",
        ),
        (
            "Delete Wi‑Fi network",
            "delete wifi network on the 5ghz band",
        ),
        (
            "Change SSID",
            "change wifi setting ssid for UNpkl-5LG-AP-1 to MyWifiSSID",
        ),
        (
            "Change password",
            "change wifi setting psk for UNpkl-5LG-AP-1 to newwifipassword",
        ),
        (
            "Block website",
            "block somewebsite.com",
        ),
    ]
    items = "".join(
        f"<li><strong>{html.escape(label)}</strong> — "
        f"<code>{html.escape(command)}</code></li>"
        for label, command in examples
    )
    return (
        f'<h2 id="quick-reference">Quick reference</h2>'
        f"<p>Common <strong>Search</strong> phrases in the UNpkl app or web UI "
        f"(while connected to your router):</p>"
        f'<ul class="unpkl-docs-quick-ref">{items}</ul>'
        f'<p>See <a href="{sac_url}">Search &amp; command</a> for the full phrase list.</p>'
    )
