#!/usr/bin/env python3
"""Markdown to publication-quality PDF (or one self-contained HTML file).

Usage: python3 make_pdf.py INPUT.md [OUTPUT] [options]   (python3 make_pdf.py -h for all)

Renders Markdown to print HTML (mdlite.py, no dependencies) and prints it with headless
Chrome, Chromium, Edge or Brave. Local images are inlined; remote images are blocked unless
--allow-network. Raw HTML in the Markdown is shown as text, never executed.

stdout: the output path. stderr: progress and warnings.
Exit codes: 0 ok, 2 bad arguments, 3 render or asset error, 4 no browser found.
"""

from __future__ import annotations

import argparse
import base64
import html
import mimetypes
import os
import re
import shlex
import shutil
import subprocess  # nosec B404
import sys
import tempfile
import time
from datetime import date
from pathlib import Path
from urllib.parse import unquote, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
import mdlite  # noqa: E402

IMAGE_TYPES = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}
MAX_IMAGE_BYTES = 25 * 1024 * 1024
SAFE_SCHEMES = {"http", "https", "mailto"}
PAGE_SIZES = {"letter", "a4", "legal"}
FONTS = {
    "serif": '"Iowan Old Style", Charter, Georgia, "Noto Serif", "DejaVu Serif", serif',
    "sans": '"Helvetica Neue", Helvetica, Arial, "Liberation Sans", "Noto Sans", sans-serif',
}
HEAD_FONT = '"Helvetica Neue", Helvetica, Arial, "Liberation Sans", "Noto Sans", sans-serif'
MONO_FONT = '"SF Mono", Menlo, Consolas, "Liberation Mono", "DejaVu Sans Mono", monospace'
EMOJI = '"Apple Color Emoji", "Segoe UI Emoji", "Noto Color Emoji"'


class RenderError(Exception):
    pass


class Context:
    def __init__(self, base_dir: Path, allow_network: bool, strict: bool) -> None:
        self.base_dir = base_dir.resolve()
        self.allow_network = allow_network
        self.strict = strict
        self.warnings: list[str] = []
        self.prev = " "

    def warn(self, message: str) -> None:
        if self.strict:
            raise RenderError(message)
        self.warnings.append(message)


# ---------------------------------------------------------------- HTML


def esc(text: str) -> str:
    return html.escape(text, quote=True)


def safe_href(href: str) -> str | None:
    href = href.strip()
    if href.startswith("#"):
        return href
    scheme = urlparse(href).scheme.lower()
    if scheme and scheme not in SAFE_SCHEMES:
        return None
    return href


def image_src(src: str, alt: str, ctx: Context) -> str | None:
    """Return a data URI or allowed URL, or None (caller renders a placeholder)."""
    parsed = urlparse(src)
    if parsed.scheme in ("http", "https"):
        if ctx.allow_network:
            return src
        ctx.warn(f"remote image blocked (use --allow-network): {src}")
        return None
    if parsed.scheme == "data":
        if src.startswith("data:image/") and not src.startswith("data:image/svg"):
            return src
        ctx.warn(f"unsupported data URI image: {alt or src[:40]}")
        return None
    if parsed.scheme:
        ctx.warn(f"unsupported image scheme: {src}")
        return None
    path = (ctx.base_dir / unquote(parsed.path)).resolve()
    if not path.is_relative_to(ctx.base_dir):
        ctx.warn(f"image outside the Markdown folder refused: {src}")
        return None
    if not path.is_file():
        ctx.warn(f"image not found: {src}")
        return None
    if path.suffix.lower() not in IMAGE_TYPES:
        ctx.warn(f"not an image type ({path.suffix}): {src}")
        return None
    if path.stat().st_size > MAX_IMAGE_BYTES:
        ctx.warn(f"image larger than 25 MB: {src}")
        return None
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    if path.suffix.lower() == ".svg":
        mime = "image/svg+xml"
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode()}"


def width_style(attrs: dict[str, str]) -> str:
    width = attrs.get("width", "")
    if width == "full":
        return ' style="width:100%"'
    if re.fullmatch(r"\d{1,3}%|\d+(\.\d+)?(in|cm|mm|px|pt)", width):
        return f' style="width:{width}"'
    return ""


def inlines(nodes: list[tuple], ctx: Context) -> str:
    out = []
    for node in nodes:
        kind = node[0]
        if kind == "text":
            text = mdlite.smarten(node[1], ctx.prev)
            ctx.prev = text[-1:] or ctx.prev
            out.append(esc(text))
        elif kind == "code":
            ctx.prev = node[1][-1:] or ctx.prev
            out.append(f"<code>{esc(node[1])}</code>")
        elif kind == "br":
            out.append("<br>")
            ctx.prev = " "
        elif kind == "image":
            _, src, alt, attrs = node
            data = image_src(src, alt, ctx)
            if data is None:
                out.append(f'<span class="img-missing">[image: {esc(alt or src)}]</span>')
            else:
                out.append(f'<img src="{esc(data)}" alt="{esc(alt)}"{width_style(attrs)}>')
        elif kind == "link":
            href = safe_href(node[1])
            inner = inlines(node[2], ctx)
            out.append(f'<a href="{esc(href)}">{inner}</a>' if href else inner)
        else:
            tag = {"strong": "strong", "em": "em", "del": "del"}[kind]
            out.append(f"<{tag}>{inlines(node[1], ctx)}</{tag}>")
    return "".join(out)


def blocks(items: list[dict], ctx: Context, tight: bool = False) -> str:
    out = []
    for block in items:
        kind = block["type"]
        ctx.prev = " "
        if kind == "heading":
            level = block["level"]
            out.append(f'<h{level} id="{block["id"]}">{inlines(block["inlines"], ctx)}</h{level}>')
        elif kind == "paragraph":
            body = inlines(block["inlines"], ctx)
            only_image = len(block["inlines"]) == 1 and block["inlines"][0][0] == "image"
            if only_image:
                out.append(f'<figure class="figure">{body}</figure>')
            else:
                out.append(body if tight else f"<p>{body}</p>")
        elif kind == "code":
            lang = f' class="language-{esc(block["lang"])}"' if block["lang"] else ""
            out.append(f"<pre><code{lang}>{esc(block['text'])}</code></pre>")
        elif kind == "quote":
            out.append(f"<blockquote>{blocks(block['children'], ctx)}</blockquote>")
        elif kind == "list":
            tag = "ol" if block["ordered"] else "ul"
            start = f' start="{block["start"]}"' if block["ordered"] and block["start"] != 1 else ""
            rows = []
            for item in block["items"]:
                box = ""
                cls = ""
                if item["checked"] is not None:
                    box = "\u2611 " if item["checked"] else "\u2610 "
                    cls = ' class="task"'
                rows.append(f"<li{cls}>{box}{blocks(item['children'], ctx, block['tight'])}</li>")
            out.append(f"<{tag}{start}>{''.join(rows)}</{tag}>")
        elif kind == "table":
            out.append(table(block, ctx))
        elif kind == "hr":
            out.append("<hr>")
        elif kind == "pagebreak":
            out.append('<div class="page-break"></div>')
    return "\n".join(out)


def table(block: dict, ctx: Context) -> str:
    aligns = block["aligns"]

    def cell(tag: str, nodes: list[tuple], col: int) -> str:
        style = f' style="text-align:{aligns[col]}"' if aligns[col] else ""
        return f"<{tag}{style}>{inlines(nodes, ctx)}</{tag}>"

    head = "".join(cell("th", c, i) for i, c in enumerate(block["header"]))
    body = "".join(
        "<tr>" + "".join(cell("td", c, i) for i, c in enumerate(row)) + "</tr>"
        for row in block["rows"]
    )
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def assign_ids(items: list[dict], seen: set[str], found: list[dict]) -> None:
    for block in items:
        if block["type"] == "heading":
            block["id"] = mdlite.slugify(mdlite.plain_text(block["inlines"]), seen)
            found.append(block)
        if block["type"] == "quote":
            assign_ids(block["children"], seen, found)
        elif block["type"] == "list":
            for item in block["items"]:
                assign_ids(item["children"], seen, found)


def toc_html(headings: list[dict], ctx: Context) -> str:
    top = [h for h in headings if h["level"] <= 3]
    levels = {1, 2} if sum(h["level"] == 1 for h in top) > 1 else {2, 3}
    rows = []
    for h in top:
        if h["level"] in levels:
            depth = h["level"] - min(levels)
            ctx.prev = " "
            text = inlines(h["inlines"], ctx)
            rows.append(f'<li class="toc-{depth}"><a href="#{h["id"]}">{text}</a></li>')
    if not rows:
        return ""
    return f'<nav class="toc"><h2 class="toc-title">Contents</h2><ol>{"".join(rows)}</ol></nav>'


def css_string(text: str) -> str:
    """Quote text as a CSS string that cannot close the surrounding <style> element."""
    out = text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ").replace("\r", " ")
    for ch, code in (("<", "\\3C "), (">", "\\3E "), ("&", "\\26 ")):
        out = out.replace(ch, code)
    return '"' + out + '"'


def content_policy(allow_network: bool) -> str:
    """CSP for the generated page: no scripts, no external loads except opted-in images."""
    images = "data: http: https:" if allow_network else "data:"
    return f"default-src 'none'; style-src 'unsafe-inline'; img-src {images}; script-src 'none'"


def stylesheet(opts: argparse.Namespace, title: str) -> str:
    body_font = FONTS[opts.font]
    page_numbers = (
        '@bottom-center { content: counter(page) " of " counter(pages); '
        f"font: 8.5pt {HEAD_FONT}; color: #666; }}"
        if not opts.no_page_numbers
        else ""
    )
    header = (
        f"@top-center {{ content: {css_string(title)}; font: 8.5pt {HEAD_FONT}; color: #888; }}"
        if title and not opts.no_header
        else ""
    )
    first = "@page :first { @top-center { content: none; } }"
    if opts.cover:
        first = "@page :first { @top-center { content: none; } @bottom-center { content: none; } }"
    chapter = (
        "main > h1:not(:first-of-type) { break-before: page; }"
        if not opts.no_chapter_breaks
        else ""
    )
    return f"""
@page {{ size: {opts.page_size}; margin: {opts.margins}; {header} {page_numbers} }}
{first}
html {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
body {{ font-family: {body_font}, {EMOJI}; font-size: 10.5pt; line-height: 1.5; color: #1a1a1a;
  margin: 0; text-align: left; hyphens: auto; }}
@media screen {{ body {{ max-width: 46em; margin: 2em auto; padding: 0 1em; }} }}
h1, h2, h3, h4, h5, h6 {{ font-family: {HEAD_FONT}, {EMOJI}; line-height: 1.25; color: #111;
  break-after: avoid; break-inside: avoid; }}
h1 {{ font-size: 22pt; margin: 0 0 14pt; }}
h2 {{ font-size: 15pt; margin: 20pt 0 8pt; }}
h3 {{ font-size: 12pt; margin: 16pt 0 6pt; }}
h4, h5, h6 {{ font-size: 10.5pt; margin: 12pt 0 4pt; }}
p {{ margin: 0 0 9pt; orphans: 3; widows: 3; }}
a {{ color: #1f4e8c; text-decoration: none; }}
code {{ font-family: {MONO_FONT}; font-size: 0.86em; background: #f3f3f1; padding: 0.05em 0.25em;
  border-radius: 2px; }}
pre {{ font-family: {MONO_FONT}; font-size: 8.6pt; line-height: 1.4; background: #f6f6f4;
  border: 0.5pt solid #ddd; border-radius: 3px; padding: 7pt 9pt; white-space: pre-wrap;
  overflow-wrap: anywhere; break-inside: avoid; }}
pre code {{ background: none; padding: 0; font-size: inherit; }}
blockquote {{ margin: 0 0 9pt; padding: 0 0 0 10pt; border-left: 2.5pt solid #c9c9c4;
  color: #444; }}
ul, ol {{ margin: 0 0 9pt; padding-left: 18pt; }}
li {{ margin: 0 0 3pt; }}
li > p {{ margin-bottom: 4pt; }}
li.task {{ list-style: none; margin-left: -14pt; }}
table {{ border-collapse: collapse; width: 100%; margin: 0 0 11pt; font-size: 9.5pt; }}
th, td {{ border-bottom: 0.5pt solid #ccc; padding: 4pt 6pt; vertical-align: top;
  text-align: left; }}
th {{ font-family: {HEAD_FONT}; border-bottom: 1pt solid #888; }}
tr {{ break-inside: avoid; }}
img {{ max-width: 100%; height: auto; }}
figure.figure {{ margin: 6pt 0 12pt; text-align: center; break-inside: avoid; }}
hr {{ border: 0; border-top: 0.5pt solid #bbb; margin: 14pt 0; }}
del {{ color: #777; }}
.img-missing {{ display: inline-block; border: 1pt dashed #b33; color: #b33; padding: 2pt 6pt;
  font: 9pt {HEAD_FONT}; }}
.page-break {{ break-after: page; }}
.cover {{ break-after: page; padding-top: 1.6in; }}
.cover h1.cover-title {{ font-size: 40pt; line-height: 1.1; margin: 0 0 14pt; }}
.cover .cover-subtitle {{ font: 16pt {HEAD_FONT}; color: #444; margin: 0 0 30pt; }}
.cover .cover-rule {{ border-top: 0.75pt solid #222; width: 2.2in; margin: 0 0 12pt; }}
.cover .cover-meta {{ font: 11pt {HEAD_FONT}; color: #333; margin: 0 0 3pt; }}
.toc {{ break-after: page; }}
.toc ol {{ list-style: none; padding: 0; }}
.toc li {{ margin: 0 0 5pt; }}
.toc .toc-1 {{ margin-left: 16pt; font-size: 0.95em; }}
.watermark {{ position: fixed; top: 45%; left: 0; right: 0; text-align: center;
  transform: rotate(-35deg); font: bold 96pt {HEAD_FONT}; color: rgba(0, 0, 0, 0.08);
  z-index: 1000; pointer-events: none; }}
{chapter}
"""


def build_html(source: Path, opts: argparse.Namespace) -> tuple[str, list[str], int]:
    meta, items = mdlite.parse(source.read_text(encoding="utf-8"))
    ctx = Context(source.parent, opts.allow_network, opts.strict)
    headings: list[dict] = []
    assign_ids(items, set(), headings)
    first_h1 = next((b for b in items if b["type"] == "heading" and b["level"] == 1), None)
    title = (
        opts.title
        or meta.get("title")
        or (mdlite.plain_text(first_h1["inlines"]) if first_h1 else source.stem)
    )
    if opts.cover and not (opts.title or meta.get("title")) and first_h1 is items[0]:
        items = items[1:]  # the cover shows it
    parts = []
    if opts.watermark:
        parts.append(f'<div class="watermark">{esc(opts.watermark)}</div>')
    if opts.cover:
        lines = [f'<h1 class="cover-title">{esc(mdlite.smarten(title))}</h1>']
        subtitle = opts.subtitle or meta.get("subtitle")
        if subtitle:
            lines.append(f'<p class="cover-subtitle">{esc(mdlite.smarten(subtitle))}</p>')
        lines.append('<div class="cover-rule"></div>')
        author = opts.author or meta.get("author")
        if author:
            lines.append(f'<p class="cover-meta">{esc(author)}</p>')
        today = date.today()
        when = opts.date or meta.get("date") or f"{today:%B} {today.day}, {today.year}"
        lines.append(f'<p class="cover-meta">{esc(when)}</p>')
        parts.append(f'<section class="cover">{"".join(lines)}</section>')
    if opts.toc:
        parts.append(toc_html(headings, ctx))
    parts.append(f"<main>{blocks(items, ctx)}</main>")
    author_meta = opts.author or meta.get("author") or ""
    csp = content_policy(opts.allow_network)
    doc = (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        f'<meta http-equiv="Content-Security-Policy" content="{csp}">'
        f"<title>{esc(title)}</title>"
        f'<meta name="author" content="{esc(author_meta)}">'
        '<meta name="generator" content="make-pdf">'
        f"<style>{stylesheet(opts, '' if opts.no_header else title)}</style></head>"
        f"<body>{''.join(parts)}</body></html>"
    )
    words = len(re.findall(r"\w+", source.read_text(encoding="utf-8")))
    return doc, ctx.warnings, words


# ---------------------------------------------------------------- browser


def find_browser(explicit: str | None) -> str | None:
    candidates = [explicit, os.environ.get("CHROME_PATH")]
    candidates += [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    ]
    for name in (
        "google-chrome",
        "google-chrome-stable",
        "chromium",
        "chromium-browser",
        "microsoft-edge",
        "msedge",
        "brave-browser",
        "chrome",
    ):
        candidates.append(shutil.which(name))
    return next((c for c in candidates if c and Path(c).is_file()), None)


def print_pdf(browser: str, html_path: Path, out: Path, allow_network: bool) -> None:
    with tempfile.TemporaryDirectory(prefix="make-pdf-profile-") as profile:
        args = [
            browser,
            "--headless",
            "--disable-gpu",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-extensions",
            "--disable-background-networking",
            f"--user-data-dir={profile}",
            "--no-pdf-header-footer",
            "--generate-pdf-document-outline",
            "--run-all-compositor-stages-before-draw",
            "--virtual-time-budget=10000",
            f"--print-to-pdf={out}",
        ]
        if not allow_network:
            args += ["--proxy-server=http://127.0.0.1:9", "--proxy-bypass-list=<-loopback>"]
        if hasattr(os, "geteuid") and os.geteuid() == 0:
            args.append("--no-sandbox")
        args += shlex.split(os.environ.get("MAKE_PDF_CHROME_FLAGS", ""))
        args.append(html_path.as_uri())
        if out.exists():
            out.unlink()
        result = subprocess.run(  # nosec B603
            args, capture_output=True, text=True, timeout=180, check=False
        )
        if not out.is_file() or out.read_bytes()[:5] != b"%PDF-":
            tail = (result.stderr or result.stdout).strip().splitlines()[-3:]
            raise RenderError("browser did not produce a PDF: " + " | ".join(tail))


def describe(pdf: Path) -> str:
    data = pdf.read_bytes()
    pages = len(re.findall(rb"/Type\s*/Page[^s]", data))
    summary = f"{len(data) // 1024} KB"
    if pages:
        summary = f"{pages} pages, " + summary
    if shutil.which("pdftotext"):
        text = subprocess.run(  # nosec B603 B607
            ["pdftotext", "-q", str(pdf), "-"], capture_output=True, text=True, check=False
        ).stdout
        summary += f", {len(text.split())} extractable words"
    return summary


# ---------------------------------------------------------------- CLI


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="make_pdf.py", description=__doc__.split("\n\n")[0])
    p.add_argument("input", type=Path)
    p.add_argument("output", type=Path, nargs="?")
    p.add_argument("--to", choices=["pdf", "html"], default="pdf")
    p.add_argument("--cover", action="store_true", help="title page from title/author/date")
    p.add_argument("--toc", action="store_true", help="clickable table of contents")
    p.add_argument("--title")
    p.add_argument("--subtitle")
    p.add_argument("--author")
    p.add_argument("--date")
    p.add_argument("--watermark", help='diagonal text on every page, e.g. "DRAFT"')
    p.add_argument("--page-size", default="letter", choices=sorted(PAGE_SIZES))
    p.add_argument("--margins", default="1in", help="CSS length: 1in, 2.5cm, 20mm, 72pt")
    p.add_argument("--font", choices=sorted(FONTS), default="serif", help="body font family")
    p.add_argument("--no-chapter-breaks", action="store_true", help="no new page per H1")
    p.add_argument("--no-page-numbers", action="store_true")
    p.add_argument("--no-header", action="store_true", help="no running title header")
    p.add_argument("--allow-network", action="store_true", help="fetch remote images")
    p.add_argument("--strict", action="store_true", help="fail on any missing or blocked image")
    p.add_argument("--chrome", help="path to Chrome, Chromium, Edge or Brave")
    p.add_argument("--quiet", action="store_true")
    opts = p.parse_args(argv)
    if not re.fullmatch(r"\d+(\.\d+)?(in|cm|mm|pt|px)", opts.margins):
        p.error("--margins must be a CSS length such as 1in, 2cm, 20mm or 72pt")
    return opts


def main(argv: list[str] | None = None) -> int:
    opts = parse_args(argv)
    log = (lambda m: None) if opts.quiet else (lambda m: print(m, file=sys.stderr))
    source = opts.input
    if not source.is_file():
        print(f"make_pdf: input not found: {source}", file=sys.stderr)
        return 2
    out = opts.output or source.with_suffix(f".{opts.to}")
    start = time.monotonic()
    try:
        doc, warnings, words = build_html(source, opts)
    except RenderError as exc:
        print(f"make_pdf: {exc}", file=sys.stderr)
        return 3
    for warning in warnings:
        log(f"warning: {warning}")
    if opts.to == "html":
        out.write_text(doc, encoding="utf-8")
        log(f"Done in {time.monotonic() - start:.1f}s. {words} words, HTML.")
        print(out)
        return 0
    browser = find_browser(opts.chrome)
    if not browser:
        print(
            "make_pdf: no Chrome, Chromium, Edge or Brave found. Install one, set CHROME_PATH, "
            "or pass --chrome PATH. `--to html` works without a browser.",
            file=sys.stderr,
        )
        return 4
    log(f"Rendering through {Path(browser).name}...")
    with tempfile.TemporaryDirectory(prefix="make-pdf-") as tmp:
        html_path = Path(tmp) / "document.html"
        html_path.write_text(doc, encoding="utf-8")
        try:
            print_pdf(browser, html_path, out.resolve(), opts.allow_network)
        except (RenderError, subprocess.TimeoutExpired, OSError) as exc:
            print(f"make_pdf: {exc}", file=sys.stderr)
            return 3
    log(f"Done in {time.monotonic() - start:.1f}s. {words} words, {describe(out)}: {out}")
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
