"""HTML document shell and page wrappers for the static GitHub Pages site."""
from __future__ import annotations

import html
import re
from pathlib import Path

from navigation import asset_url, home_url, hub_url

ROOT = Path(__file__).resolve().parents[1]
HUB_TEMPLATE = ROOT / "templates" / "hub-page.html"


def wrap_document(title: str, body: str, nav: dict, description: str = "") -> str:
    css = html.escape(asset_url("assets/unpkl-docs.css", nav), quote=True)
    js = html.escape(asset_url("assets/unpkl-docs.js", nav), quote=True)
    page_title = html.escape(title)
    desc = html.escape(description) if description else ""
    meta_desc = f'\n  <meta name="description" content="{desc}">' if desc else ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{page_title}</title>{meta_desc}
  <link rel="stylesheet" href="{css}">
</head>
<body>
{body}
<script src="{js}" defer></script>
</body>
</html>
"""


def rewrite_home_links(body: str, nav: dict) -> str:
    """Replace breadcrumb Home href=\"/\" with configured homeUrl."""
    home = html.escape(home_url(nav), quote=True)
    return body.replace('<a href="/">Home</a>', f'<a href="{home}">Home</a>')


def render_hub_body(nav: dict, sidebar: str, overview: str, quick_ref: str) -> str:
    body = HUB_TEMPLATE.read_text(encoding="utf-8")
    body = body.replace("<!-- UNPKL_SIDEBAR -->", sidebar)
    body = body.replace("<!-- UNPKL_HUB_OVERVIEW -->", overview)
    body = body.replace("<!-- UNPKL_HUB_QUICK_REF -->", quick_ref)
    body = re.sub(r"<!--.*?-->", "", body, flags=re.DOTALL).strip()
    hub = html.escape(hub_url(nav), quote=True)
    # Hub brand already uses hub_url via sidebar; fix Home breadcrumb.
    body = rewrite_home_links(body, nav)
    # Ensure Documentation current page does not need hub link.
    _ = hub
    return body
