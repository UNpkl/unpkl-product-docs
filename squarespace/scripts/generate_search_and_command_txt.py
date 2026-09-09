#!/usr/bin/env python3
"""
Generate blocks/pages/search-and-command/search-and-command.txt from UNpkl app + firmware sources.

Regenerate when any of these change (paths relative to sibling repos by default):

  unpkl-app/constants/searchCommands.ts          — example phrases, routing categories
  unpkl-app/constants/localAiSystemPrompt.txt    — AI / command vocabulary notes
  unpkl-app/services/localAiTools.ts             — LOCAL_EMBEDDED_ROUTER_ACTIONS + HTTP paths
  unpkl-app/services/localAiChat.ts              — local Search AI entry point (reference)
  yh-wireless/include/yh_unsac_hashes.h          — YH_CMD_* authoritative hash names
  yh-wireless/src/yh_ossl_lib/unsac_commands.txt — UNSAC phrase templates

Run directly:
  python3 scripts/generate_search_and_command_txt.py

Regenerate from app/firmware into .txt, then build HTML:
  ./build-pages.sh --generate-search

Manual edits (images, extra sections, SAC wording in {#manual-*} sections) are preserved when you run:
  ./build-pages.sh --generate-search

Only auto-generated section ids (overview, open-search, …) are refreshed from app/firmware.
Add images in sections titled ## … {#manual-your-id} — same pattern as initial-setup.txt.

Plain ./build-pages.sh syncs .txt → HTML without touching the .txt file.

Override source locations with environment variables:
  UNPKL_APP_ROOT, YH_WIRELESS_ROOT
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_PATH = ROOT / "blocks" / "pages" / "search-and-command" / "search-and-command.txt"

DEFAULT_UNPKL_APP = Path(os.environ.get("UNPKL_APP_ROOT", Path.home() / "unpkl-app"))
DEFAULT_YH_WIRELESS = Path(
    os.environ.get(
        "YH_WIRELESS_ROOT",
        Path.home() / "unpkl-github" / "yh" / "yhioe" / "yh-wireless",
    )
)

# End-user docs say SAC (search and command). Firmware/app sources use UNSAC / unsac_* filenames.
SAC = "SAC (search and command)"
SAC_SHORT = "SAC"

SOURCE_FILES = {
    "searchCommands.ts": "constants/searchCommands.ts",
    "localAiSystemPrompt.txt": "constants/localAiSystemPrompt.txt",
    "localAiTools.ts": "services/localAiTools.ts",
    "localAiChat.ts": "services/localAiChat.ts",
    "yh_unsac_hashes.h": "include/yh_unsac_hashes.h",
    "unsac_commands.txt": "src/yh_ossl_lib/unsac_commands.txt",
}


def resolve_sources(app_root: Path, wireless_root: Path) -> dict[str, Path]:
    app_files = {
        "searchCommands.ts",
        "localAiSystemPrompt.txt",
        "localAiTools.ts",
        "localAiChat.ts",
    }
    paths: dict[str, Path] = {}
    for key, rel in SOURCE_FILES.items():
        base = app_root if key in app_files else wireless_root
        paths[key] = base / rel
    return paths


def read_text(path: Path) -> str:
    if not path.is_file():
        raise FileNotFoundError(f"Missing source: {path}")
    return path.read_text(encoding="utf-8")


def parse_ts_string_array(text: str, const_name: str) -> list[str]:
    """Extract string literals from `export const NAME = [ ... ]`."""
    pattern = rf"export const {re.escape(const_name)}\s*=\s*\[(.*?)\]\s*as const"
    match = re.search(pattern, text, re.DOTALL)
    if not match:
        return []
    return re.findall(r"'((?:\\'|[^'])*)'", match.group(1))


def parse_command_categories(ts: str) -> dict[str, list[str]]:
    """Parse COMMAND_CATEGORIES object — category key → example strings."""
    match = re.search(
        r"export const COMMAND_CATEGORIES\s*=\s*\{(.*?)\n\};",
        ts,
        re.DOTALL,
    )
    if not match:
        return {}
    body = match.group(1)
    categories: dict[str, list[str]] = {}
    for cat_match in re.finditer(
        r"(\w+):\s*\[(.*?)\](?:,|\s*$)",
        body,
        re.DOTALL,
    ):
        key = cat_match.group(1)
        if key == "suggestTokens":
            continue
        items = re.findall(r"'((?:\\'|[^'])*)'", cat_match.group(2))
        if items:
            categories[key] = items
    return categories


def parse_router_actions(ts: str) -> list[str]:
    return parse_ts_string_array(ts, "LOCAL_EMBEDDED_ROUTER_ACTIONS")


def parse_unsac_phrases(text: str) -> list[str]:
    lines = []
    for line in text.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            lines.append(line)
    return lines


def yh_cmd_to_phrase(define_name: str) -> str:
    """YH_CMD_BLOCK_SOURCE_FROM_DESTINATION → block source from destination"""
    name = define_name.removeprefix("YH_CMD_")
    return name.lower().replace("_", " ")


def parse_yh_cmd_hashes(header: str) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for match in re.finditer(r"#define (YH_CMD_\w+)\s+0x[0-9a-fA-F]+", header):
        define_name = match.group(1)
        rows.append((define_name, yh_cmd_to_phrase(define_name)))
    return rows


def bullet_list(items: list[str], limit: int | None = None) -> str:
    subset = items if limit is None else items[:limit]
    return "\n".join(f"- `{item}`" for item in subset)


def example_list(items: list[str]) -> str:
    return "\n".join(f"- `{x}`" for x in items)


def section(title: str, section_id: str, body: str) -> str:
    return f"## {title} {{#{section_id}}}\n\n{body.strip()}\n"


# Section ids owned by the generator — everything else (e.g. {#manual-…}) is preserved on regenerate.
GENERATED_SECTION_IDS = frozenset(
    {
        "overview",
        "open-search",
        "how-commands-work",
        "block-unblock",
        "tag-assign",
        "port-forwarding",
        "wifi",
        "mesh",
        "wan-lan",
        "upgrade-reboot-logging",
        "device-lifecycle",
        "ai-assistant",
        "sac-phrase-templates",
        "firmware-commands",
        "confirmations",
    }
)

MANUAL_BLOCK_RE = re.compile(
    r"<!--\s*MANUAL\s*-->(.*?)<!--\s*/MANUAL\s*-->",
    re.DOTALL | re.IGNORECASE,
)
IMAGE_MD_RE = re.compile(
    r"^!\[([^\]]*)\]\(([^)]+)\)(?:\s+\"([^\"]+)\")?(?:\s*\{wide\})?\s*$",
    re.IGNORECASE,
)
ORDERED_LINE_RE = re.compile(r"^\d+\.\s+")
BULLET_LINE_RE = re.compile(r"^[-*]\s+")
CALLOUT_LINE_RE = re.compile(r"^> \[!?")
SECTION_HEADER_RE = re.compile(r"^## (.+?) \{#([a-z0-9-]+)\}\s*$")
RELATED_RE = re.compile(r"^@related\s+(.+)\s*$", re.I)
FOOTER_START_RE = re.compile(r"^---\s*$")

DEFAULT_RELATED = ["settings-and-charts", "live-data", "faq"]


@dataclass
class DocSection:
    title: str
    section_id: str
    body: str


@dataclass
class Document:
    title: str
    lead: str
    sections: list[DocSection]
    related: list[str] = field(default_factory=lambda: list(DEFAULT_RELATED))
    footer_lines: list[str] = field(default_factory=list)


def default_footer_lines() -> list[str]:
    return [
        "Auto-generated sections: scripts/generate_search_and_command_txt.py (--generate-search)",
        "Manual sections: ## Title {#manual-your-id} — see squarespace/TEXT-FORMAT.md",
        "Build HTML: ./build-pages.sh",
        "Sources (app/firmware paths in script header):",
        *(f"  {key} ← {rel}" for key, rel in SOURCE_FILES.items()),
    ]


def split_footer(text: str) -> tuple[str, list[str]]:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if FOOTER_START_RE.match(line):
            return "\n".join(lines[:index]).strip(), lines[index + 1 :]
    return text.strip(), []


def parse_existing_document(text: str) -> Document | None:
    body, footer_lines = split_footer(text)
    if not body.strip():
        return None
    lines = body.splitlines()
    title = lines[0].strip()
    first_section = next(
        (index for index, line in enumerate(lines) if SECTION_HEADER_RE.match(line)),
        None,
    )
    if first_section is None:
        return None

    lead = "\n".join(
        line.strip()
        for line in lines[1:first_section]
        if line.strip()
    )

    related_idx = next(
        (index for index, line in enumerate(lines) if RELATED_RE.match(line)),
        len(lines),
    )
    related = list(DEFAULT_RELATED)
    if related_idx < len(lines):
        match = RELATED_RE.match(lines[related_idx])
        if match:
            related = [
                part.strip()
                for part in match.group(1).split(",")
                if part.strip()
            ]

    sections: list[DocSection] = []
    index = first_section
    while index < related_idx:
        match = SECTION_HEADER_RE.match(lines[index])
        if not match:
            index += 1
            continue
        sec_title, sec_id = match.groups()
        index += 1
        body_lines: list[str] = []
        while index < related_idx and not SECTION_HEADER_RE.match(lines[index]):
            body_lines.append(lines[index])
            index += 1
        sections.append(
            DocSection(sec_title, sec_id, "\n".join(body_lines).strip())
        )

    return Document(
        title=title,
        lead=lead,
        sections=sections,
        related=related,
        footer_lines=footer_lines or default_footer_lines(),
    )


def strip_manual_comment_blocks(body: str) -> str:
    return MANUAL_BLOCK_RE.sub("", body or "").strip()


def extract_manual_comment_blocks(body: str) -> list[str]:
    return [block.strip() for block in MANUAL_BLOCK_RE.findall(body or "") if block.strip()]


def extract_image_blocks(body: str) -> list[str]:
    """Standalone `![alt](file)` blocks (optional caption line) to keep on regenerate."""
    text = strip_manual_comment_blocks(body)
    if not text.strip():
        return []
    blocks: list[str] = []
    for paragraph in re.split(r"\n\s*\n", text.strip()):
        lines = [line for line in paragraph.splitlines() if line.strip()]
        if not lines or not IMAGE_MD_RE.match(lines[0]):
            continue
        caption = ""
        if len(lines) > 1:
            second = lines[1]
            if (
                not second.startswith("##")
                and not ORDERED_LINE_RE.match(second)
                and not BULLET_LINE_RE.match(second)
                and not CALLOUT_LINE_RE.match(second)
            ):
                caption = second
        blocks.append(lines[0] + (f"\n{caption}" if caption else ""))
    return blocks


def extract_preserved_section_content(body: str) -> list[str]:
    """Manual inserts inside auto-generated sections (images, <!-- MANUAL --> blocks)."""
    preserved = extract_manual_comment_blocks(body)
    for image_block in extract_image_blocks(body):
        if image_block not in preserved:
            preserved.append(image_block)
    return preserved


def merge_section_body(existing_body: str, generated_body: str) -> str:
    preserved = extract_preserved_section_content(existing_body)
    if not preserved:
        return generated_body.strip()
    generated = strip_manual_comment_blocks(generated_body).strip()
    parts = preserved + ([generated] if generated else [])
    return "\n\n".join(parts).strip()


def merge_documents(existing: Document | None, generated: Document) -> Document:
    """Replace generated section ids; keep {#manual-*} and any unknown ids."""
    if existing is None:
        return generated

    generated_map = {section.section_id: section for section in generated.sections}
    existing_ids = {section.section_id for section in existing.sections}
    merged_sections: list[DocSection] = []

    for section in existing.sections:
        if section.section_id in GENERATED_SECTION_IDS and section.section_id in generated_map:
            fresh = generated_map[section.section_id]
            merged_sections.append(
                DocSection(
                    fresh.title,
                    fresh.section_id,
                    merge_section_body(section.body, fresh.body),
                )
            )
        else:
            merged_sections.append(section)

    for section in generated.sections:
        if section.section_id not in existing_ids:
            merged_sections.append(section)

    return Document(
        title=generated.title,
        lead=generated.lead,
        sections=merged_sections,
        related=existing.related or generated.related,
        footer_lines=generated.footer_lines,
    )


def render_document(doc: Document) -> str:
    parts = [doc.title, "", doc.lead.strip(), ""]
    for sec in doc.sections:
        parts.append(section(sec.title, sec.section_id, sec.body).rstrip())
        parts.append("")
    parts.append(f"@related {', '.join(doc.related)}")
    parts.append("")
    parts.append("---")
    parts.extend(doc.footer_lines or default_footer_lines())
    return "\n".join(parts) + "\n"


def _sec(title: str, section_id: str, body: str) -> DocSection:
    return DocSection(title, section_id, body.strip())


def generate(
    categories: dict[str, list[str]],
    router_actions: list[str],
    unsac_phrases: list[str],
    yh_cmds: list[tuple[str, str]],
) -> Document:
    sections: list[DocSection] = []

    lead = (
        "Use **Search** in the UNpkl mobile app to control your local router with natural-language "
        "commands, ask questions about your network, and run in-app flows such as device provisioning. "
        f"Commands are sent to the router as plain English phrases the firmware understands ({SAC})."
    )

    sections.append(
        _sec(
            "Overview",
            "overview",
            """Search combines three paths:

1. **Direct commands** — phrases that match the router command vocabulary are sent to the router (`POST /c`) immediately (after confirmation when a reboot or brief Wi‑Fi interruption is expected).
2. **AI assistant** — questions, follow-ups, and complex requests are handled by the local Search AI, which plans actions and runs them on **this router only** (not cloud fleet mode).
3. **App flows** — scan, provision, return device, and subscription phrases open dedicated in-app wizards (middleware / QR), not raw router HTTP.

You must be signed in to the **local embedded router** (connected to its Wi‑Fi or LAN). Cloud-only stats and multi-edge APIs are not available from local Search.""",
        )
    )

    sections.append(
        _sec(
            "Open Search",
            "open-search",
            """1. Open the UNpkl app while connected to your UNpkl router network.
2. Tap **Search** in the navigation bar (or use the search entry point on your device).
3. Type a command or question and submit.

**Tips:**

- Ask **how** questions in plain English (for example, `How do I forward a port?`) — these route to the AI assistant instead of being sent blindly to the router.
- Short follow-ups (`yes`, `show passwords`, `the second network`) stay in the AI conversation thread.
- If a phrase is not in the app's command list but may exist on newer firmware, the app can offer to send it **directly to the router** after you confirm.""",
        )
    )

    sections.append(
        _sec(
            "How router commands work",
            "how-commands-work",
            f"""Router control uses **natural-language queries** posted to `POST /c` as form field `query`. The {SAC} engine on the device maps each phrase to an internal command hash (`YH_CMD_*` in firmware).

**Wording matters** — use the same verbs and structure as the examples below. Hostnames (for example `Mac`) must match DHCP lease names on your router.

**Allow vs unblock:** On port-access phrases, **allow** and **unblock** are synonyms. User intent to **deny**, **stop**, or block port access maps to `block access to port …`, not informal "stop" wording in the {SAC_SHORT} command grammar.

**Read-only HTTP** (no `/c` phrase): topology, live devices, history, policy tables, wireless config snapshot, cloud status, upgrade check — the AI uses dedicated GET routes when answering questions.""",
        )
    )

    block_examples = categories.get("block", [])
    unblock_examples = categories.get("unblock", [])
    sections.append(
        _sec(
            "Block and unblock",
            "block-unblock",
            f"""Block destinations (websites, domains, apps) or specific source → destination pairs. Timed blocks use explicit units: **minutes**, **hours**, or **days**.

**Examples:**

{example_list(block_examples + unblock_examples)}

**Schedules** — combine source/destination with time windows and **weekdays**, **weekends**, or **everyday** (for example, `block source iPhone from destination social.example.com from time 9 pm to time 5 pm weekdays`).

**Block everything:** `block all` / `unblock all`.""",
        )
    )

    tag_examples = categories.get("tag", []) + categories.get("assign", [])
    sections.append(
        _sec(
            "Tag, assign, and rename devices",
            "tag-assign",
            f"""Organize clients and destinations with tags and groups, or rename a source for easier Search.

**Examples:**

{example_list(tag_examples)}""",
        )
    )

    forward_examples = categories.get("forward", [])
    port_examples = categories.get("portAccess", [])
    sections.append(
        _sec(
            "Port forwarding and firewall access",
            "port-forwarding",
            f"""**Port forwarding (DNAT)** — expose a LAN service on a WAN port. Targets can be an IP, `host:port`, or a DHCP hostname.

{example_list(forward_examples)}

**Firewall / port access** — block or allow traffic to router services by port and optional source IP list.

{example_list(port_examples)}

Related phrases: `clear access to port …`, `clear port …`, `unblock access to port only from …`, `unforward port … from …`.""",
        )
    )

    wifi_examples = categories.get("wifi", [])
    mesh_examples = categories.get("mesh", [])
    sections.append(
        _sec(
            "Wi‑Fi networks",
            "wifi",
            f"""Manage SSIDs, passwords, VLAN IDs, and network count on 2.4 GHz, 5 GHz, or both bands.

**Examples:**

{example_list(wifi_examples)}

**Add a network:** `add wifi network <ssid> with password <psk> on <band> band` — password must be **at least 8 characters**, **letters and digits only** (no spaces or symbols). Default band is **5 GHz** if omitted.

**Changing an existing SSID** (`change wifi setting psk|ssid|hidden|vlan …`) applies without reboot but may briefly disconnect clients.

**Adding networks, changing network count, or deleting SSIDs** requires a **router reboot** to take effect. The app prompts before rebooting.

**Wi‑Fi join QR:** Ask the AI for a scannable QR (for example, `show qr code for wifi on 5ghz`). Passphrases are only included after you explicitly confirm.""",
        )
    )

    if mesh_examples:
        sections.append(
            _sec(
                "Mesh and EasyMesh",
                "mesh",
                f"""Control mesh controller and agent roles on supported hardware.

**Examples:**

{example_list(mesh_examples)}""",
            )
        )

    wan_examples = categories.get("wan", [])
    set_examples = categories.get("set", [])
    sections.append(
        _sec(
            "WAN, LAN, and device properties",
            "wan-lan",
            f"""Configure static WAN addressing or LAN subnet.

**Examples:**

{example_list(wan_examples + set_examples)}

Other supported phrases include `refresh web certificate`, `set device property … as …`, and `clear all`.""",
        )
    )

    log_examples = categories.get("logging", [])
    upgrade_verbs = [v for v in categories.get("verbs", []) if "upgrade" in v.lower()]
    sections.append(
        _sec(
            "Upgrade, reboot, and logging",
            "upgrade-reboot-logging",
            f"""**Firmware:** `upgrade check`, `force upgrade`, `upgrade test`, `upgrade test check`.

**Reboot:** Confirm before rebooting — you will be logged out. Required after some Wi‑Fi/WAN changes.

**Logging:**

{example_list(log_examples) if log_examples else "- `start logging` / `stop logging` / `start logging to file`"}

Ask the AI **is cloud connected?** or **cloud status** to read cloud registration without a `/c` command.""",
        )
    )

    scan_verbs = [
        v
        for v in categories.get("verbs", [])
        if any(x in v.lower() for x in ("scan", "provision", "add device", "new device"))
        and "unprovision" not in v.lower()
    ]
    sub_verbs = [v for v in categories.get("verbs", []) if "subscription" in v.lower()]
    unprov = [
        v
        for v in categories.get("verbs", [])
        if any(x in v.lower() for x in ("unprovision", "return device", "remove device"))
    ]
    sections.append(
        _sec(
            "Device scan, provisioning, and subscriptions",
            "device-lifecycle",
            f"""These phrases open **in-app flows** (QR scanner, confirmations, middleware) — they are **not** sent as `POST /c` router commands.

**Scan / add / provision:** {", ".join(f"`{x}`" for x in scan_verbs[:6])}

**Return / remove:** {", ".join(f"`{x}`" for x in unprov[:5])}

**Subscription billing:** {", ".join(f"`{x}`" for x in sub_verbs)}

Use Search with one of the phrases above; follow on-screen steps.""",
        )
    )

    # Group unsac templates by first word for appendix
    grouped: dict[str, list[str]] = {}
    for phrase in unsac_phrases:
        key = phrase.split()[0] if phrase else "other"
        grouped.setdefault(key, []).append(phrase)

    top_verbs = sorted(grouped.keys(), key=lambda k: (-len(grouped[k]), k))[:12]
    appendix_parts = []
    for verb in top_verbs:
        samples = grouped[verb][:8]
        appendix_parts.append(f"**{verb}** — " + ", ".join(f"`{s}`" for s in samples))
        if len(grouped[verb]) > 8:
            appendix_parts.append(
                f"- _{len(grouped[verb]) - 8} additional `{verb}` templates in firmware_"
            )

    sections.append(
        _sec(
            "AI assistant capabilities",
            "ai-assistant",
            f"""When your input is a question or needs multiple steps, local Search AI:

1. Plans using router context (topology, live devices, network stats).
2. Runs allowed **router actions** on this device only.
3. Summarizes results in plain language (without exposing internal action names).

**Supported router actions** ({len(router_actions)}): {", ".join(f"`{a}`" for a in router_actions[:10])}, … and `execute_command` for any other {SAC_SHORT} command phrase.

Destructive shell commands via `exec` are blocked unless explicitly allowed. Wi‑Fi passwords require your confirmation before the AI displays them.""",
        )
    )

    sections.append(
        _sec(
            "SAC phrase templates",
            "sac-phrase-templates",
            f"""The firmware matcher accepts {len(unsac_phrases)} {SAC_SHORT} phrase templates (source file `unsac_commands.txt` in firmware). Samples by leading verb:

{chr(10).join(appendix_parts)}

Placeholders such as `source`, `destination`, `time`, `n`, and `port` stand in for your values. See **Block and unblock** and **Wi‑Fi networks** for filled-in examples.""",
        )
    )

    # Compact firmware hash reference (grouped)
    hash_sample = [phrase for _, phrase in yh_cmds if "block source from destination" in phrase][:6]
    sections.append(
        _sec(
            "Firmware command hashes",
            "firmware-commands",
            f"""Each accepted phrase resolves to a `YH_CMD_*` hash in `yh_unsac_hashes.h` ({len(yh_cmds)} definitions). Examples:

{bullet_list(hash_sample, 6)}

The app and docs stay aligned with firmware sources (`yh_unsac_hashes.h`, `unsac_commands.txt`) when commands are added or renamed. Those filenames use the internal UNSAC name; documentation refers to the feature as {SAC}.""",
        )
    )

    sections.append(
        _sec(
            "Confirmations and errors",
            "confirmations",
            """**Reboot prompt** — After `add wifi network`, `set N wifi networks`, `delete wifi network`, or static WAN changes, reply **yes** / **now** to reboot immediately, **later** / **no** to apply without rebooting now, or **cancel** to abort.

**Wi‑Fi setting changes** — `change wifi setting …` may interrupt connections briefly; no reboot required.

**Invalid command** — Router may return `invalid command` or `uh oh` in the response message even with HTTP 200.

**Direct send** — Unknown phrases can still be tried on the router if you confirm when prompted.""",
        )
    )

    return Document(
        title="Search & command",
        lead=lead,
        sections=sections,
        related=list(DEFAULT_RELATED),
        footer_lines=default_footer_lines(),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app-root", type=Path, default=DEFAULT_UNPKL_APP)
    parser.add_argument("--wireless-root", type=Path, default=DEFAULT_YH_WIRELESS)
    parser.add_argument("--out", type=Path, default=OUT_PATH)
    parser.add_argument("--check", action="store_true", help="Exit 1 if output would change")
    args = parser.parse_args()

    sources = resolve_sources(args.app_root, args.wireless_root)
    for path in sources.values():
        if not path.is_file():
            print(f"error: missing source {path}", file=sys.stderr)
            return 1

    search_ts = read_text(sources["searchCommands.ts"])
    tools_ts = read_text(sources["localAiTools.ts"])
    unsac = read_text(sources["unsac_commands.txt"])
    hashes = read_text(sources["yh_unsac_hashes.h"])

    categories = parse_command_categories(search_ts)
    router_actions = parse_router_actions(tools_ts)
    unsac_phrases = parse_unsac_phrases(unsac)
    yh_cmds = parse_yh_cmd_hashes(hashes)

    generated = generate(categories, router_actions, unsac_phrases, yh_cmds)
    existing = (
        parse_existing_document(args.out.read_text(encoding="utf-8"))
        if args.out.is_file()
        else None
    )
    merged = merge_documents(existing, generated)
    content = render_document(merged)
    manual_count = sum(
        1 for section in merged.sections if section.section_id not in GENERATED_SECTION_IDS
    )

    if args.check:
        if args.out.is_file() and args.out.read_text(encoding="utf-8") == content:
            print("search-and-command.txt is up to date")
            return 0
        print("search-and-command.txt is stale — run generate_search_and_command_txt.py", file=sys.stderr)
        return 1

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(content, encoding="utf-8")
    preserved = f", {manual_count} manual section(s) preserved" if manual_count else ""
    print(
        f"Wrote {args.out.relative_to(ROOT)} "
        f"({len(unsac_phrases)} SAC templates, {len(yh_cmds)} YH_CMD hashes{preserved})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
