#!/usr/bin/env python3
"""Sync blocks/pages/<slug>/<slug>.txt into config/articles.json.

Markup reference: squarespace/TEXT-FORMAT.md
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES = ROOT / "blocks" / "pages"
ARTICLES_PATH = ROOT / "config" / "articles.json"

SECTION_RE = re.compile(r"^## (.+?) \{#([a-z0-9-]+)\}\s*$")
SUBSECTION_H3_RE = re.compile(r"^## (.+?)\s*$")
SUBSECTION_H4_RE = re.compile(r"^### (.+?)\s*$")
CALLOUT_RE = re.compile(r"^> \[!?([a-z]+)(?:\|([^\]]+))?\] (.+)\s*$")
IMAGE_MD_RE = re.compile(
    r"^!\[([^\]]*)\]\(([^)]+)\)(?:\s+\"([^\"]+)\")?(?:\s*\{wide\})?\s*$",
    re.IGNORECASE,
)
IMAGE_WIDE_SUFFIX_RE = re.compile(r"\{wide\}\s*$", re.IGNORECASE)
IMAGE_LEGACY_RE = re.compile(r"^Image:\s*(\S+)(?:\s*\|\s*(.+))?\s*$", re.I)
ORDERED_RE = re.compile(r"^\d+\.\s+")
BULLET_RE = re.compile(r"^[-*]\s+")
URL_RE = re.compile(r"(https?://[^\s<]+)")
RELATED_RE = re.compile(r"^@related\s+(.+)\s*$", re.I)
FOOTER_START = re.compile(r"^---\s*$")
CODE_FENCE_RE = re.compile(r"^```(\w*)(?:\{copy\})?\s*$", re.I)
CODE_LEGACY_START = re.compile(r"^<code markup>\s*$", re.I)
CODE_LEGACY_END = re.compile(r"^</code markup>\s*$", re.I)


def slug_txt_path(slug: str) -> Path:
    page_dir = PAGES / slug
    for name in (f"{slug}.txt", f"unpkl-{slug}.txt"):
        candidate = page_dir / name
        if candidate.is_file():
            return candidate
    return page_dir / f"{slug}.txt"


def discover_slugs() -> list[str]:
    slugs: list[str] = []
    if not PAGES.is_dir():
        return slugs
    for folder in sorted(PAGES.iterdir()):
        if not folder.is_dir():
            continue
        if slug_txt_path(folder.name).is_file():
            slugs.append(folder.name)
    return slugs


def strip_footer(text: str) -> str:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if FOOTER_START.match(line):
            return "\n".join(lines[:index]).strip()
    return text.strip()


def image_src(filename: str, slug: str) -> str:
    """Published HTML uses scaled .jpg; PNG/WebP sources compress to .jpg at build."""
    name = Path(filename.strip()).name
    stem = Path(name).stem
    page_dir = PAGES / slug
    # PNG/WebP always publish as compressed JPEG (see compress_page_images.py).
    if (page_dir / f"{stem}.png").is_file() or (page_dir / f"{stem}.webp").is_file():
        return f"{stem}.jpg"
    if (page_dir / f"{stem}.jpg").is_file() or (page_dir / f"{stem}.jpeg").is_file():
        return f"{stem}.jpg"
    if (page_dir / name).is_file():
        return name
    return f"{stem}.jpg"


def inline_text(text: str) -> str:
    parts: list[str] = []
    pos = 0
    for match in re.finditer(r"`([^`]+)`|\*\*([^*]+)\*\*", text):
        before = text[pos : match.start()]
        if before:
            parts.append(html.escape(before))
        if match.group(1) is not None:
            parts.append(f"<code>{html.escape(match.group(1))}</code>")
        else:
            parts.append(f"<strong>{html.escape(match.group(2))}</strong>")
        pos = match.end()
    tail = text[pos:]
    if tail:
        parts.append(html.escape(tail))
    return URL_RE.sub(
        r'<a href="\1">\1</a>',
        "".join(parts) if parts else html.escape(text),
    )


def paragraph_html(text: str) -> str:
    return f"<p>{inline_text(text.strip())}</p>"


def callout_html(ctype: str, title: str, body_html: str) -> str:
    return (
        f'<div class="unpkl-docs-callout unpkl-docs-callout--{html.escape(ctype)}">'
        f'<p class="unpkl-docs-callout__title">{html.escape(title)}</p>'
        f"{body_html}</div>"
    )


COPY_ICON = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" '
    'fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
    'stroke-linejoin="round" aria-hidden="true">'
    '<rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>'
    '<path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>'
    "</svg>"
)

# Inline handler: Squarespace Code blocks strip trailing <script> tags.
COPY_CLICK_HANDLER = (
    "var b=this,"
    "el=b.parentElement&&b.parentElement.querySelector('.unpkl-docs-cmd__text'),"
    "t=el&&(el.value!==undefined?el.value:el.textContent);"
    "if(!t)return false;"
    "var done=function(){b.classList.add('is-copied');"
    "var l=b.querySelector('.unpkl-docs-cmd__copy-label');"
    "if(l){var p=l.textContent;l.textContent='Copied';"
    "setTimeout(function(){b.classList.remove('is-copied');l.textContent=p},2000)}};"
    "var fb=function(){var e=document.createElement('textarea');"
    "e.value=t;e.setAttribute('readonly','');"
    "e.style.cssText='position:fixed;top:0;left:0;width:2em;height:2em;padding:0;"
    "border:none;outline:none;background:transparent';"
    "document.body.appendChild(e);e.focus();e.select();"
    "try{document.execCommand('copy')&&done()}catch(x){}"
    "document.body.removeChild(e)};"
    "if(navigator.clipboard&&navigator.clipboard.writeText){"
    "navigator.clipboard.writeText(t).then(done).catch(fb)}else{fb()};"
    "return false"
)


def pre_html(code_lines: list[str], lang: str = "") -> str:
    content = html.escape("\n".join(code_lines).rstrip("\n"))
    if lang:
        lang_attr = html.escape(lang)
        return f'<pre><code class="language-{lang_attr}">{content}</code></pre>'
    return f"<pre><code>{content}</code></pre>"


def copyable_commands_html(code_lines: list[str], lang: str = "") -> str:
    lang_cls = f" language-{html.escape(lang)}" if lang else ""
    parts = ['<div class="unpkl-docs-cmd-list">']
    for line in code_lines:
        cmd = line.rstrip()
        if not cmd.strip():
            continue
        escaped = html.escape(cmd)
        parts.append(
            f'<div class="unpkl-docs-cmd">'
            f'<textarea readonly class="unpkl-docs-cmd__text{lang_cls}" rows="1" '
            f'spellcheck="false" aria-label="Shell command" '
            f'onclick="this.select()">{escaped}</textarea>'
            f'<button type="button" class="unpkl-docs-cmd__copy" '
            f'onclick="{COPY_CLICK_HANDLER}" '
            f'aria-label="Copy command to clipboard">'
            f"{COPY_ICON}"
            f'<span class="unpkl-docs-cmd__copy-label">Copy</span>'
            f"</button>"
            f"</div>"
        )
    parts.append("</div>")
    return "".join(parts)


def iter_body_blocks(body: str) -> list[tuple[str, object]]:
    """Split section body into ('code', lang, lines, copyable) or ('text', line_list) blocks."""
    lines = body.splitlines()
    blocks: list[tuple[str, object]] = []
    paragraph: list[str] = []
    index = 0

    def flush_paragraph() -> None:
        nonlocal paragraph
        if paragraph:
            blocks.append(("text", paragraph))
            paragraph = []

    while index < len(lines):
        stripped = lines[index].strip()
        fence = CODE_FENCE_RE.match(stripped)
        if fence:
            flush_paragraph()
            lang = fence.group(1) or ""
            copyable = bool(re.search(r"\{copy\}", stripped, re.I))
            code_lines: list[str] = []
            index += 1
            while index < len(lines) and not CODE_FENCE_RE.match(lines[index].strip()):
                code_lines.append(lines[index])
                index += 1
            if index < len(lines):
                index += 1
            blocks.append(("code", lang, code_lines, copyable))
            continue

        if CODE_LEGACY_START.match(stripped):
            flush_paragraph()
            code_lines = []
            index += 1
            while index < len(lines):
                if CODE_LEGACY_END.match(lines[index].strip()):
                    index += 1
                    break
                if (
                    not lines[index].strip()
                    and index + 1 < len(lines)
                    and (
                        SECTION_RE.match(lines[index + 1])
                        or SUBSECTION_H3_RE.match(lines[index + 1])
                        or SUBSECTION_H4_RE.match(lines[index + 1])
                    )
                ):
                    break
                code_lines.append(lines[index])
                index += 1
            blocks.append(("code", "", code_lines))
            continue

        if not stripped:
            flush_paragraph()
            index += 1
            continue

        paragraph.append(lines[index].rstrip())
        index += 1

    flush_paragraph()
    return blocks


def list_html(lines: list[str], ordered: bool) -> str:
    tag = "ol" if ordered else "ul"
    items = []
    for line in lines:
        content = ORDERED_RE.sub("", line) if ordered else BULLET_RE.sub("", line)
        if content.startswith("**") and ":**" in content:
            label, _, value = content.partition(":**")
            label = label.removeprefix("**").strip()
            items.append(
                f"<li><strong>{html.escape(label)}:</strong> {inline_text(value.strip())}</li>"
            )
        else:
            items.append(f"<li>{inline_text(content.strip())}</li>")
    return f"<{tag}>{''.join(items)}</{tag}>"


def image_is_wide(raw_line: str) -> bool:
    return bool(IMAGE_WIDE_SUFFIX_RE.search(raw_line.strip()))


def figure_html(
    filename: str,
    alt: str,
    caption: str,
    slug: str,
    *,
    wide: bool = False,
) -> str:
    src = image_src(filename, slug)
    alt_attr = html.escape(alt or Path(filename).stem.replace("-", " "))
    cap = caption.strip()
    cap_html = (
        f"<figcaption>{inline_text(cap)}</figcaption>" if cap else ""
    )
    figure_class = (
        "unpkl-docs-figure unpkl-docs-figure--wide"
        if wide
        else "unpkl-docs-figure"
    )
    img_class = (
        "unpkl-docs-image unpkl-docs-image--wide" if wide else "unpkl-docs-image"
    )
    return (
        f'<figure class="{figure_class}">'
        f'<img class="{img_class}" src="{html.escape(src)}" alt="{alt_attr}">'
        f"{cap_html}</figure>"
    )


def parse_callout_meta(modifier: str | None) -> tuple[str | None, str | None]:
    if not modifier:
        return None, None
    if modifier == "intro":
        return "intro", None
    if modifier.startswith("after:"):
        return None, modifier.removeprefix("after:").strip()
    return modifier, None


def subsection_html(line: str) -> str | None:
    """In-section subheadings: ## Title → h3, ### Title → h4 (no {#id})."""
    if SECTION_RE.match(line):
        return None
    match = SUBSECTION_H4_RE.match(line)
    if match:
        return f"<h4>{html.escape(match.group(1))}</h4>"
    match = SUBSECTION_H3_RE.match(line)
    if match:
        return f"<h3>{html.escape(match.group(1))}</h3>"
    return None


def parse_text_block(lines: list[str], section_id: str, slug: str) -> tuple[list[str], list[dict]]:
    """Parse a prose block (may contain internal blank lines as paragraph breaks)."""
    callouts: list[dict] = []
    html_parts: list[str] = []
    subblocks = re.split(r"\n\s*\n", "\n".join(lines).strip())
    if not subblocks or not subblocks[0].strip():
        return html_parts, callouts

    for block in subblocks:
        block_lines = [line.rstrip() for line in block.splitlines() if line.strip()]
        if not block_lines:
            continue

        first = block_lines[0]
        callout_match = CALLOUT_RE.match(first)
        if callout_match and all(line.startswith("> ") for line in block_lines):
            ctype, modifier, title = callout_match.groups()
            body_lines = [line.removeprefix("> ").strip() for line in block_lines[1:]]
            callout_body = paragraph_html(" ".join(body_lines) if body_lines else title.strip())
            position, after = parse_callout_meta(modifier)
            if position or after:
                entry: dict = {
                    "type": ctype,
                    "title": title.strip(),
                    "html": callout_body,
                }
                if position:
                    entry["position"] = position
                if after:
                    entry["after"] = after
                callouts.append(entry)
            else:
                html_parts.append(callout_html(ctype, title.strip(), callout_body))
            continue

        if len(block_lines) == 1:
            heading = subsection_html(first)
            if heading:
                html_parts.append(heading)
                continue
            image_match = IMAGE_MD_RE.match(first)
            if image_match:
                alt, filename, caption = image_match.groups()
                cap = caption or ""
                html_parts.append(
                    figure_html(
                        filename, alt, cap, slug, wide=image_is_wide(first)
                    )
                )
                continue
            legacy_match = IMAGE_LEGACY_RE.match(first)
            if legacy_match:
                filename, alt = legacy_match.groups()
                html_parts.append(figure_html(filename, alt or "", "", slug))
                continue

        image_match = IMAGE_MD_RE.match(first)
        if image_match:
            alt, filename, caption = image_match.groups()
            cap = caption or ""
            if not cap and len(block_lines) > 1 and not block_lines[1].startswith(">"):
                cap = block_lines[1].strip()
            html_parts.append(figure_html(filename, alt, cap, slug, wide=image_is_wide(first)))
            continue

        legacy_match = IMAGE_LEGACY_RE.match(first)
        if legacy_match:
            filename, alt = legacy_match.groups()
            cap = (
                block_lines[1].strip()
                if len(block_lines) > 1 and not block_lines[1].startswith(">")
                else ""
            )
            html_parts.append(figure_html(filename, alt or "", cap, slug))
            continue

        if all(ORDERED_RE.match(line) for line in block_lines):
            html_parts.append(list_html(block_lines, ordered=True))
            continue

        if all(BULLET_RE.match(line) for line in block_lines):
            html_parts.append(list_html(block_lines, ordered=False))
            continue

        for line in block_lines:
            heading = subsection_html(line)
            if heading:
                html_parts.append(heading)
                continue
            html_parts.append(paragraph_html(line))

    return html_parts, callouts


def parse_section_body(body: str, section_id: str, slug: str) -> tuple[str, list[dict]]:
    callouts: list[dict] = []
    html_parts: list[str] = []
    if not body.strip():
        return "", callouts

    for item in iter_body_blocks(body):
        if item[0] == "code":
            _, lang, code_lines, copyable = item
            if copyable:
                html_parts.append(copyable_commands_html(code_lines, lang))
            else:
                html_parts.append(pre_html(code_lines, lang))
            continue
        _, payload = item
        text_parts, block_callouts = parse_text_block(payload, section_id, slug)
        html_parts.extend(text_parts)
        callouts.extend(block_callouts)

    return "".join(html_parts), callouts


def parse_article_text(text: str, slug: str) -> dict:
    text = strip_footer(text)
    lines = text.splitlines()

    while lines and not lines[0].strip():
        lines.pop(0)
    if not lines:
        raise ValueError("Missing title")

    title = lines[0].strip()
    index = 1
    while index < len(lines) and not lines[index].strip():
        index += 1

    lead_lines: list[str] = []
    while index < len(lines):
        line = lines[index]
        if SECTION_RE.match(line) or RELATED_RE.match(line):
            break
        if line.strip():
            lead_lines.append(line.strip())
        elif lead_lines:
            break
        index += 1
    lead = " ".join(lead_lines)

    related: list[str] = []
    sections: list[dict] = []
    callouts: list[dict] = []

    current_title = None
    current_id = None
    current_body: list[str] = []

    def flush_section() -> None:
        nonlocal current_title, current_id, current_body
        if current_id is None:
            return
        body = "\n".join(current_body).strip()
        section_html, section_callouts = parse_section_body(body, current_id, slug)
        sections.append(
            {
                "id": current_id,
                "title": current_title or current_id,
                "level": 2,
                "html": section_html,
            }
        )
        callouts.extend(section_callouts)
        current_title = None
        current_id = None
        current_body = []

    while index < len(lines):
        line = lines[index]
        related_match = RELATED_RE.match(line)
        if related_match:
            related = [
                part.strip()
                for part in related_match.group(1).split(",")
                if part.strip()
            ]
            index += 1
            continue

        section_match = SECTION_RE.match(line)
        if section_match:
            flush_section()
            current_title, current_id = section_match.groups()
            index += 1
            continue

        if current_id is not None:
            current_body.append(line)
        index += 1

    flush_section()

    article: dict = {
        "title": title,
        "lead": lead,
        "sections": sections,
        "callouts": callouts,
    }
    if related:
        article["related"] = related
    return article


def merge_article(existing: dict | None, parsed: dict) -> dict:
    merged = dict(existing or {})
    merged.update(parsed)
    if existing:
        if "related" not in parsed and "related" in existing:
            merged["related"] = existing["related"]
        if "callouts" not in parsed and "callouts" in existing:
            merged["callouts"] = existing["callouts"]
    return merged


def sync_slug(slug: str, articles: dict, write: bool = True) -> bool:
    txt_path = slug_txt_path(slug)
    if not txt_path.is_file():
        return False
    parsed = parse_article_text(txt_path.read_text(encoding="utf-8"), slug)
    merged = merge_article(articles.get(slug), parsed)
    changed = articles.get(slug) != merged
    if write:
        articles[slug] = merged
    return changed


def sync_all(slugs: list[str] | None = None, dry_run: bool = False) -> list[str]:
    articles = json.loads(ARTICLES_PATH.read_text(encoding="utf-8"))
    targets = slugs or discover_slugs()
    changed_slugs: list[str] = []
    for slug in targets:
        txt_path = slug_txt_path(slug)
        if not txt_path.is_file():
            print(f"skip {slug}: no {txt_path.name}", file=sys.stderr)
            continue
        if sync_slug(slug, articles, write=True):
            changed_slugs.append(slug)
    if changed_slugs and not dry_run:
        ARTICLES_PATH.write_text(
            json.dumps(articles, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    return changed_slugs


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "slugs",
        nargs="*",
        help="Article slugs to sync (default: all folders with <slug>.txt)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit 1 if articles.json would change",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print slugs that would change without writing",
    )
    args = parser.parse_args()

    articles_before = json.loads(ARTICLES_PATH.read_text(encoding="utf-8"))
    articles = json.loads(ARTICLES_PATH.read_text(encoding="utf-8"))
    targets = args.slugs or discover_slugs()
    changed: list[str] = []
    for slug in targets:
        txt_path = slug_txt_path(slug)
        if not txt_path.is_file():
            print(f"skip {slug}: no {txt_path.name}", file=sys.stderr)
            continue
        parsed = parse_article_text(txt_path.read_text(encoding="utf-8"), slug)
        merged = merge_article(articles_before.get(slug), parsed)
        if articles_before.get(slug) != merged:
            changed.append(slug)
            if not args.check and not args.dry_run:
                articles[slug] = merged

    if changed and not args.check and not args.dry_run:
        ARTICLES_PATH.write_text(
            json.dumps(articles, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    if changed:
        label = "would sync" if args.dry_run or args.check else "synced"
        print(f"{label}: {', '.join(changed)}")
    else:
        print("articles.json already up to date")

    if args.check and changed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
