#!/usr/bin/env python3
"""Render Learn-style sidebar tree from navigation.json."""
from __future__ import annotations

import base64
import html
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ICON = ROOT / "assets" / "unpkl-icon.png"

from navigation import (  # noqa: E402
    asset_url,
    hub_url,
    item_url,
    load_navigation,
    normalize_path,
    section_has_active,
)


def icon_src(nav: dict, *, linked_assets: bool = False) -> str:
    configured = nav.get("iconUrl", "").strip()
    if configured:
        return html.escape(configured, quote=True)
    if linked_assets:
        return html.escape(asset_url("assets/unpkl-icon.png", nav), quote=True)
    if DEFAULT_ICON.is_file():
        encoded = base64.b64encode(DEFAULT_ICON.read_bytes()).decode("ascii")
        return f"data:image/png;base64,{encoded}"
    return ""


def render_sidebar(
    nav: dict, active_path: str | None = None, *, linked_assets: bool = False
) -> str:
    product = html.escape(nav.get("productName", "Documentation"))
    hub = html.escape(hub_url(nav))
    active = normalize_path(active_path) if active_path else None
    hub_normalized = normalize_path(hub_url(nav))
    on_hub = active == hub_normalized
    hub_active = on_hub
    icon = icon_src(nav, linked_assets=linked_assets)
    icon_markup = (
        f'<img class="unpkl-docs-sidebar__icon" src="{icon}" alt="" width="32" height="32">'
        if icon
        else ""
    )

    parts = [
        f'<div class="unpkl-docs-sidebar__brand"><a href="{hub}"'
        f'{" class=\"is-active\"" if hub_active else ""}>'
        f"{icon_markup}<span>{product}</span></a></div>",
        '<div class="unpkl-docs-tree">',
    ]

    for section in nav.get("sections", []):
        title = html.escape(section["title"])
        is_open = on_hub or active is None or section_has_active(section, active, nav)
        open_attr = " open" if is_open else ""

        parts.append(f'<details class="unpkl-docs-tree-group"{open_attr}>')
        parts.append(f"<summary>{title}</summary>")
        parts.append('<ul class="unpkl-docs-tree-list">')

        for item in section.get("items", []):
            url = html.escape(item_url(item, nav))
            label = html.escape(item["title"])
            is_active = active and normalize_path(item_url(item, nav)) == active
            active_class = ' class="is-active"' if is_active else ""
            parts.append(f'<li><a href="{url}"{active_class}>{label}</a></li>')

        parts.append("</ul></details>")

    parts.append("</div>")
    return "\n".join(parts)


def main() -> None:
    nav_path = Path(sys.argv[1])
    active_path = sys.argv[2] if len(sys.argv) > 2 else None
    nav = load_navigation(nav_path)
    print(render_sidebar(nav, active_path))


if __name__ == "__main__":
    main()
