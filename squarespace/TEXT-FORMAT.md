# Article text format (`.txt` markup)

UNpkl Squarespace docs are authored as plain text in:

```
blocks/pages/<slug>/<slug>.txt
```

On `./build-pages.sh`, each `.txt` file is synced to `config/articles.json` and rendered to `blocks/pages/<slug>/paste-into-code-block.html` for pasting into Squarespace.

**Only content above the `---` footer line is published.** Lines at and below `---` are notes for authors and are ignored by the build.

---

## Document structure

```txt
Page title (line 1)

Lead paragraph — one or more lines of intro text before the first section.

## First main section {#section-id}

Section body …

## Second section {#another-id}

More body …

@related other-slug, another-slug

---
Author notes (not published)
```

| Part | Rules |
|------|--------|
| **Title** | First non-empty line. Becomes the page `<h1>`. |
| **Lead** | Blank line after title, then text until the first `## … {#…}` section. Shown under the title. |
| **Sections** | `## Title {#section-id}` — main sections (`<h2>`), appear in the in-page table of contents. |
| **Related** | `@related slug-one, slug-two` — footer links to other articles (slugs without `/how-to-` prefix). |
| **Footer** | `---` on its own line; everything after is ignored. |

---

## Sections and subheadings

### Main section (in TOC)

```txt
## Setting up your router {#router-setup}
```

- `{#section-id}` must be lowercase letters, digits, and hyphens (`a-z`, `0-9`, `-`).
- The id becomes the HTML anchor (`#router-setup`) for TOC and deep links.

### Subsection inside a section (not in TOC)

Use `##` or `###` **without** `{#id}`:

```txt
## Download the UNpkl app

Body text under a bold subheading (<h3>).

### Optional smaller subheading

Renders as <h4> inside the current section.
```

---

## Paragraphs

Separate paragraphs with a **blank line**:

```txt
First paragraph.

Second paragraph.
```

---

## Inline formatting

| Markup | Renders as |
|--------|------------|
| `**bold text**` | **bold** |
| `` `code or commands` `` | `monospace` |
| `https://example.com` | Auto-linked |

Example:

```txt
Tap **Search** and type `block example.com for 2 hours`.
```

---

## Code blocks

Multi-line commands, shell sessions, and log snippets use **fenced code blocks** (same idea as images: declare markup in the `.txt`, build emits HTML).

### Fenced block (preferred)

Open with a line of three backticks, optional language tag, close with three backticks:

```txt
```shell
ssh root@doohickey.yhioe.lan
rm /mnt/data/yhioe/yh_nf*
reboot
```
```

Supported language tags are passed through as `class="language-…"` on the `<code>` element (for example `shell`, `bash`, `txt`). Omit the tag for a plain block:

```txt
```
turn agent on
change wifi setting ssid for … to …
```
```

### Copyable commands (`{copy}`)

When each line should be copied separately (for example SSH steps), add `{copy}` after the language tag on the opening fence:

```txt
```shell{copy}
ssh root@doohickey.yhioe.lan
rm /mnt/data/yhioe/yh_nf*
reboot
```
```

Each non-empty line becomes its own row with a **Copy** button and clipboard icon. Use this for multi-step shell commands; use a plain fenced block for log output or single snippets.

Rules:

- Blank lines **inside** the fence are preserved (plain blocks) or skipped (`{copy}` rows).
- Inline `` `command` `` still works for short phrases in a sentence; use fences for multiple lines.
- Plain fences render as `<pre><code>…</code></pre>` with monospace styling.
- `{copy}` fences render as one row per command with a copy-to-clipboard button. Copy uses an inline click handler (Squarespace strips `<script>` in Code blocks). Optional site-wide fallback: `blocks/site-footer-copy-snippet.html` in Code Injection → Footer.

### Legacy `<code markup>` block

Older drafts may use:

```txt
<code markup>
ssh root@doohickey.yhioe.lan
rm /mnt/data/yhioe/yh_nf*
reboot
</code markup>
```

This is equivalent to a fenced block. Prefer ``` fences in new content.

---

## FAQ-style questions

Use `### Question text?` for each entry (renders as a subheading). Group topics under `## Section {#section-id}`:

```txt
## Router and connectivity {#connectivity}

### Cannot access the internet?

Answer paragraph. Use `inline code` for commands.

```shell
ssh root@doohickey.yhioe.lan
```
```

---

## Lists

**Ordered** (use `1.` on each line; numbering is automatic in HTML):

```txt
1. Unbox the router.
2. Connect power.
3. Wait two minutes.
```

**Bullets** (`-` or `*`):

```txt
- Item one
- Item two
```

**Label bullets** (bold label + value):

```txt
- **Username:** SpongeBobSpatula
- **Password:** MySecretPass123
```

---

## Images

Place image files in the same folder as the `.txt` file:

```
blocks/pages/<slug>/how-to-example.png
```

Reference with Markdown image syntax:

```txt
![Alt text for screen readers](how-to-example.png)
Optional caption on the line after the image.
```

**Wide images (laptop / diagrams)** — append `{wide}` for full content-column width (820px) and no height cap. Use for tall infographics or multi-panel screenshots:

```txt
![Search and Command workflow](how-to-search-and-command.png){wide}
```

At build time, `{wide}` images are compressed to 820px width (default is 520px).

Rules:

- **Alt text** is required inside `[…]` for accessibility.
- **Caption** — optional plain text on the next line (not starting with `>`, `##`, `1.`, or `-`).
- At build time, PNG/WebP sources are scaled and saved as `.jpg`; the HTML uses base64-inlined JPEGs (same pipeline as initial-setup).

Example (from initial-setup):

```txt
![iPhone Settings screen showing a UNpkl Wi-Fi network](how-to-initial-setup-wifi-ssid.png)
Connect to your UNpkl Wi-Fi network before continuing setup.
```

---

## Callouts

```txt
> [!type|modifier] Callout title
> Body text continues on lines starting with `> `.
```

| Type | Use |
|------|-----|
| `important` | Warnings, prerequisites |
| `tip` | Helpful shortcuts |
| `note` | Neutral extra info |

| Modifier | Placement |
|----------|-----------|
| *(none)* | Inline at that point in the section body |
| `intro` | Top of article (before first section), e.g. `> [!important\|intro] Important` |
| `after:section-id` | After the section with that id, e.g. `> [!tip\|after:first-time-app-setup] Tip` |

Example:

```txt
> [!important|intro] Important
> Connect to a UNpkl SSID before performing app setup.

## Admin registration {#admin-registration}

…section content…

> [!tip|after:admin-registration] Tip
> Enable biometric login after registration for faster access.
```

---

## Related articles

```txt
@related wifi-6, troubleshooting, faq
```

- Comma-separated **slugs** only (folder names under `blocks/pages/`, not full URLs).
- Rendered as a “Related content” list at the bottom of the article.

---

## Search & command: manual vs auto-generated sections

The **search-and-command** article can mix:

1. **Auto-generated sections** — ids like `{#overview}`, `{#open-search}`, `{#wifi}`, … refreshed from app/firmware when you run:

   ```bash
   ./build-pages.sh --generate-search
   ```

2. **Manual sections** — entire sections you own. Use any id that **does not** match an auto id (convention: `{#manual-…}`):

   ```txt
   ## Search in the app {#manual-search-ui}

   ![Search bar in the UNpkl app](how-to-search-bar.png)
   Tap **Search** in the navigation bar to open the command field.
   ```

3. **Images inside an auto section** — add `![alt](file.png)` (and optional caption) inside `{#overview}`, `{#open-search}`, etc. These are **kept** when auto text is refreshed:

   ```txt
   ## Overview {#overview}

   ![Search and Command](how-to-search-and-command.png)
   Optional caption on the next line.

   Search combines three paths:
   …
   ```

   For extra prose (not just an image), wrap it in a manual block:

   ```txt
   <!-- MANUAL -->
   ![Screenshot](how-to-example.png)
   Extra paragraph you want to keep.
   <!-- /MANUAL -->
   ```

Manual sections and manual inserts inside auto sections are **preserved** on `--generate-search`.

Auto section ids (regenerated):  
`overview`, `open-search`, `how-commands-work`, `block-unblock`, `tag-assign`, `port-forwarding`, `wifi`, `mesh`, `wan-lan`, `upgrade-reboot-logging`, `device-lifecycle`, `ai-assistant`, `sac-phrase-templates`, `firmware-commands`, `confirmations`.

Plain `./build-pages.sh` never overwrites the `.txt` — it only syncs to HTML.

---

## Build commands

| Command | Effect |
|---------|--------|
| `./build-pages.sh` | Sync all `.txt` → `articles.json` → paste HTML |
| `./build-pages.sh --generate-search` | Regenerate search-and-command auto sections, then build |
| `python3 scripts/sync_txt_to_articles.py <slug>` | Sync one article only |
| `python3 scripts/generate_search_and_command_txt.py` | Regenerate search-and-command `.txt` merge only |

After build, re-paste `blocks/pages/<slug>/paste-into-code-block.html` into the Squarespace Code block and hard-refresh.

---

## Full minimal example

```txt
My article title

Short lead sentence explaining what this page covers.

## Getting started {#getting-started}

1. Do the first step.
2. Do the second step.

## Details {#details}

Plain paragraph with **bold** and `command` examples.

- **Option A:** value
- **Option B:** value

![Screenshot description](my-screenshot.png)
Caption shown under the image.

## Extra topic {#manual-screenshots}

Use `{#manual-…}` ids on search-and-command for sections you own.

@related initial-setup, faq

---
See squarespace/TEXT-FORMAT.md for markup reference.
```

---

## See also

- `DEPLOY.md` — Squarespace paste workflow
- `blocks/pages/initial-setup/initial-setup.txt` — worked example with images and callouts
- `scripts/sync_txt_to_articles.py` — parser implementation
- `scripts/generate_search_and_command_txt.py` — search-and-command auto section generator
