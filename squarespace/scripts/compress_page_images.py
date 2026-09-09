#!/usr/bin/env python3
"""Scale and compress page images for Squarespace paste size limits."""
from __future__ import annotations

import subprocess
import sys
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BLOCKS_PAGES = ROOT / "blocks" / "pages"

MAX_WIDTH = 520
MAX_WIDTH_WIDE = 820
JPEG_QUALITY = 85
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
WIDE_IMAGE_LINE_RE = re.compile(
    r"^!\[[^\]]*\]\(([^)]+)\).*\{wide\}",
    re.IGNORECASE,
)


def to_rgb(image):
    from PIL import Image

    if image.mode in ("RGBA", "LA") or (
        image.mode == "P" and "transparency" in image.info
    ):
        background = Image.new("RGBA", image.size, (255, 255, 255, 255))
        background = Image.alpha_composite(background, image.convert("RGBA"))
        return background.convert("RGB")
    return image.convert("RGB")


def scale_if_needed(image, max_width: int = MAX_WIDTH):
    from PIL import Image

    if image.width <= max_width:
        return image
    height = round(image.height * (max_width / image.width))
    return image.resize((max_width, height), Image.Resampling.LANCZOS)


def save_jpeg(image, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    image.save(
        dest,
        "JPEG",
        quality=JPEG_QUALITY,
        subsampling=0,
        optimize=True,
    )


def prepare_with_pillow(source: Path, dest: Path, max_width: int = MAX_WIDTH) -> None:
    from PIL import Image

    image = scale_if_needed(to_rgb(Image.open(source)), max_width)
    save_jpeg(image, dest)


def compress_with_sips(source: Path, dest: Path, max_width: int = MAX_WIDTH) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "sips",
        "-s",
        "format",
        "jpeg",
        "-s",
        "formatOptions",
        str(JPEG_QUALITY),
        "--resampleWidth",
        str(max_width),
        str(source),
        "--out",
        str(dest),
    ]
    subprocess.run(cmd, check=True, capture_output=True)


def prepare_image(source: Path, dest: Path, max_width: int = MAX_WIDTH) -> None:
    if source.suffix.lower() in {".png", ".webp"} or _needs_resize(source, max_width):
        prepare_with_pillow(source, dest, max_width)
        return
    if source.stat().st_size > 400_000:
        prepare_with_pillow(source, dest, max_width)
        return
    compress_with_sips(source, dest, max_width)


def _needs_resize(source: Path, max_width: int = MAX_WIDTH) -> bool:
    from PIL import Image

    with Image.open(source) as image:
        return image.width > max_width


def wide_image_stems(page_dir: Path) -> set[str]:
    txt = page_dir / f"{page_dir.name}.txt"
    if not txt.is_file():
        return set()
    stems: set[str] = set()
    for line in txt.read_text(encoding="utf-8").splitlines():
        match = WIDE_IMAGE_LINE_RE.match(line.strip())
        if match:
            stems.add(Path(match.group(1).strip()).stem)
    return stems


def prepare_slug_images(slug: str) -> list[tuple[str, int]]:
    page_dir = BLOCKS_PAGES / slug
    if not page_dir.is_dir():
        return []

    png_sources: dict[str, Path] = {}
    other_sources: dict[str, Path] = {}
    for source in page_dir.iterdir():
        if not source.is_file():
            continue
        suffix = source.suffix.lower()
        if suffix not in IMAGE_SUFFIXES:
            continue
        if source.name.startswith("."):
            continue
        stem = source.stem
        if suffix in {".png", ".webp"}:
            png_sources[stem] = source
        else:
            other_sources.setdefault(stem, source)

    wide_stems = wide_image_stems(page_dir)
    written: list[tuple[str, int]] = []
    for stem in sorted(set(png_sources) | set(other_sources)):
        source = png_sources.get(stem) or other_sources[stem]
        dest = page_dir / f"{stem}.jpg"
        max_width = MAX_WIDTH_WIDE if stem in wide_stems else MAX_WIDTH
        prepare_image(source, dest, max_width)
        written.append((dest.name, dest.stat().st_size))

    return written


def main() -> None:
    slug = sys.argv[1]
    results = prepare_slug_images(slug)
    if not results:
        print(f"No images prepared for {slug}")
        return
    for name, size in results:
        print(f"{name}\t{size}")


if __name__ == "__main__":
    main()
