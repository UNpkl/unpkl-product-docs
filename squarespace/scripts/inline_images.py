#!/usr/bin/env python3
"""Replace relative img src paths with base64 data URIs from a slug page folder."""
from __future__ import annotations

import base64
import mimetypes
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BLOCKS_PAGES = ROOT / "blocks" / "pages"

IMG_SRC_PATTERN = re.compile(
    r'(<img\b[^>]*\bsrc=")([^":/][^"]*)(")',
    re.IGNORECASE,
)


def mime_for(path: Path) -> str:
    mime, _ = mimetypes.guess_type(path.name)
    return mime or "application/octet-stream"


def inline_slug_images(slug: str, html: str, page_dir: Path | None = None) -> str:
    page_dir = page_dir or BLOCKS_PAGES / slug

    def replace(match: re.Match[str]) -> str:
        prefix, filename, suffix = match.groups()
        path = page_dir / filename
        if not path.is_file():
            return match.group(0)
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        return f'{prefix}data:{mime_for(path)};base64,{encoded}{suffix}'

    return IMG_SRC_PATTERN.sub(replace, html)
