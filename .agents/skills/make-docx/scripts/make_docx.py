#!/usr/bin/env python3
"""Markdown to a native Word document (.docx), using only the Python standard library.

Usage: python3 make_docx.py INPUT.md [OUTPUT.docx] [options]   (-h for all options)

Produces real Word structure: Title, Heading 1-6 (navigation pane and TOC), numbered and
bulleted lists, tables with repeating header rows, code blocks, quotes, hyperlinks, internal
links to headings, embedded PNG/JPEG/GIF images, a TOC field pre-filled with links, page
"N of M" footer, optional cover page, running header and DRAFT watermark.

stdout: the output path. stderr: progress and warnings.
Exit codes: 0 ok, 2 bad arguments, 3 render or asset error.
"""

from __future__ import annotations

import argparse
import re
import struct
import sys
import zipfile
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import unquote, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
import mdlite  # noqa: E402

EMU_PER_INCH = 914400
EMU_PER_PX = 9525  # 96 dpi
MAX_IMAGE_BYTES = 25 * 1024 * 1024
PAGE = {"letter": (12240, 15840), "a4": (11906, 16838), "legal": (12240, 20160)}
SAFE_SCHEMES = {"http", "https", "mailto"}
NS = (
    'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
    'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
    'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
    'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
    'xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture" '
    'xmlns:v="urn:schemas-microsoft-com:vml" '
    'xmlns:o="urn:schemas-microsoft-com:office:office" '
    'xmlns:w10="urn:schemas-microsoft-com:office:word"'
)
REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
XML_HEAD = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
INVALID_XML = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f￾￿]")


class RenderError(Exception):
    pass


def x(text: str) -> str:
    """Escape text for XML content and attributes; drop characters XML 1.0 forbids."""
    text = INVALID_XML.sub("", text)
    return (
        text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
    )


def twips(css: str) -> int:
    m = re.fullmatch(r"(\d+(?:\.\d+)?)(in|cm|mm|pt)", css)
    if not m:
        raise ValueError(css)
    value, unit = float(m.group(1)), m.group(2)
    return round(value * {"in": 1440, "cm": 1440 / 2.54, "mm": 144 / 2.54, "pt": 20}[unit])


def image_size(data: bytes) -> tuple[int, int] | None:
    """Pixel size of PNG, JPEG or GIF data."""
    if data[:8] == b"\x89PNG\r\n\x1a\n" and len(data) >= 24:
        return struct.unpack(">II", data[16:24])
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return struct.unpack("<HH", data[6:10])
    if data[:2] == b"\xff\xd8":
        i = 2
        while i + 9 < len(data):
            if data[i] != 0xFF:
                i += 1
                continue
            marker = data[i + 1]
            if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
                i += 2
                continue
            length = struct.unpack(">H", data[i + 2 : i + 4])[0]
            if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE):
                h, w = struct.unpack(">HH", data[i + 5 : i + 9])
                return w, h
            i += 2 + length
    return None


class Docx:
    def __init__(self, base_dir: Path, opts: argparse.Namespace) -> None:
        self.base_dir = base_dir.resolve()
        self.opts = opts
        self.warnings: list[str] = []
        self.rels: list[tuple[str, str, str, bool]] = []  # id, type, target, external
        self.media: dict[str, bytes] = {}
        self.nums: list[tuple[int, int, int]] = []  # num id, abstract id, start
        self.bookmarks: dict[str, str] = {}
        self.bookmark_id = 0
        self.drawing_id = 0
        self.prev = " "
        width, _ = PAGE[opts.page_size]
        self.text_width = width - 2 * twips(opts.margins)

    # -------------------------------------------------------- helpers

    def warn(self, message: str) -> None:
        if self.opts.strict:
            raise RenderError(message)
        self.warnings.append(message)

    def rel(self, kind: str, target: str, external: bool = False) -> str:
        rid = f"rId{len(self.rels) + 10}"
        self.rels.append((rid, kind, target, external))
        return rid

    def new_num(self, ordered: bool, start: int) -> int:
        num_id = len(self.nums) + 1
        self.nums.append((num_id, 1 if ordered else 0, start))
        return num_id

    # -------------------------------------------------------- inline runs

    def run(self, text: str, fmt: frozenset[str], smart: bool = True) -> str:
        if smart:
            text = mdlite.smarten(text, self.prev)
        if text:
            self.prev = text[-1]
        props = ""
        if "code" in fmt:
            props += '<w:rStyle w:val="InlineCode"/>'
        elif "link" in fmt:
            props += '<w:rStyle w:val="Hyperlink"/>'
        props += "".join(f"<w:{tag}/>" for tag in ("b", "i", "strike") if tag in fmt)
        rpr = f"<w:rPr>{props}</w:rPr>" if props else ""
        return f'<w:r>{rpr}<w:t xml:space="preserve">{x(text)}</w:t></w:r>'

    def runs(self, nodes: list[tuple], fmt: frozenset[str] = frozenset()) -> str:
        out = []
        for node in nodes:
            kind = node[0]
            if kind == "text":
                out.append(self.run(node[1], fmt))
            elif kind == "code":
                out.append(self.run(node[1], fmt | {"code"}, smart=False))
            elif kind == "br":
                out.append("<w:r><w:br/></w:r>")
            elif kind == "image":
                out.append(self.image(node[1], node[2], node[3]))
            elif kind == "link":
                out.append(self.link(node[1], node[2], fmt))
            else:
                tag = {"strong": "b", "em": "i", "del": "strike"}[kind]
                out.append(self.runs(node[1], fmt | {tag}))
        return "".join(out)

    def link(self, href: str, kids: list[tuple], fmt: frozenset[str]) -> str:
        inner = self.runs(kids, fmt | {"link"})
        href = href.strip()
        if href.startswith("#"):
            name = self.bookmarks.get(href[1:])
            return f'<w:hyperlink w:anchor="{x(name)}">{inner}</w:hyperlink>' if name else inner
        scheme = urlparse(href).scheme.lower()
        if scheme not in SAFE_SCHEMES:
            return self.runs(kids, fmt)  # relative or unsafe link: keep the text only
        rid = self.rel(f"{REL}/hyperlink", href, external=True)
        return f'<w:hyperlink r:id="{rid}" w:history="1">{inner}</w:hyperlink>'

    def image(self, src: str, alt: str, attrs: dict[str, str]) -> str:
        placeholder = self.run(f"[image: {alt or src}]", frozenset({"i"}), smart=False)
        parsed = urlparse(src)
        if parsed.scheme:
            self.warn(f"only local images are embedded in Word output: {src}")
            return placeholder
        path = (self.base_dir / unquote(parsed.path)).resolve()
        if not path.is_relative_to(self.base_dir):
            self.warn(f"image outside the Markdown folder refused: {src}")
            return placeholder
        if not path.is_file() or path.stat().st_size > MAX_IMAGE_BYTES:
            self.warn(f"image not found or larger than 25 MB: {src}")
            return placeholder
        data = path.read_bytes()
        size = image_size(data)
        ext = {b"\x89P": "png", b"GI": "gif", b"\xff\xd8": "jpeg"}.get(data[:2])
        if not size or not ext:
            self.warn(f"Word output embeds PNG, JPEG or GIF only (convert SVG/WebP): {src}")
            return placeholder
        name = f"image{len(self.media) + 1}.{ext}"
        self.media[name] = data
        rid = self.rel(f"{REL}/image", f"media/{name}")
        cx, cy = self.scaled(size, attrs)
        self.drawing_id += 1
        n = self.drawing_id
        return (
            '<w:r><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0">'
            f'<wp:extent cx="{cx}" cy="{cy}"/><wp:docPr id="{n}" name="Picture {n}" '
            f'descr="{x(alt)}"/><wp:cNvGraphicFramePr><a:graphicFrameLocks noChangeAspect="1"/>'
            "</wp:cNvGraphicFramePr><a:graphic><a:graphicData "
            'uri="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:pic>'
            f'<pic:nvPicPr><pic:cNvPr id="{n}" name="{name}" descr="{x(alt)}"/><pic:cNvPicPr/>'
            f'</pic:nvPicPr><pic:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/>'
            '</a:stretch></pic:blipFill><pic:spPr><a:xfrm><a:off x="0" y="0"/>'
            f'<a:ext cx="{cx}" cy="{cy}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/>'
            "</a:prstGeom></pic:spPr></pic:pic></a:graphicData></a:graphic></wp:inline>"
            "</w:drawing></w:r>"
        )

    def scaled(self, size: tuple[int, int], attrs: dict[str, str]) -> tuple[int, int]:
        w_px, h_px = max(size[0], 1), max(size[1], 1)
        max_emu = self.text_width * EMU_PER_INCH // 1440
        width = w_px * EMU_PER_PX
        wanted = attrs.get("width", "")
        if wanted == "full":
            width = max_emu
        elif m := re.fullmatch(r"(\d{1,3})%", wanted):
            width = max_emu * min(int(m.group(1)), 100) // 100
        elif re.fullmatch(r"\d+(\.\d+)?(in|cm|mm|pt)", wanted):
            width = twips(wanted) * EMU_PER_INCH // 1440
        width = min(width, max_emu)
        return width, width * h_px // w_px

    # -------------------------------------------------------- blocks

    def para(
        self,
        body: str,
        style: str = "",
        numbering: tuple[int, int] | None = None,
        indent: int = 0,
        extra: str = "",
        jc: str = "",
        page_break: bool = False,
    ) -> str:
        ppr = f'<w:pStyle w:val="{style}"/>' if style else ""
        if page_break:
            ppr += "<w:pageBreakBefore/>"
        if numbering:
            num_id, ilvl = numbering
            ppr += f'<w:numPr><w:ilvl w:val="{ilvl}"/><w:numId w:val="{num_id}"/></w:numPr>'
        ppr += extra
        if indent and not numbering:
            ppr += f'<w:ind w:left="{indent}"/>'
        if jc:
            ppr += f'<w:jc w:val="{jc}"/>'
        return f"<w:p>{f'<w:pPr>{ppr}</w:pPr>' if ppr else ''}{body}</w:p>"

    def blocks(self, items: list[dict], style: str = "", indent: int = 0, depth: int = 0) -> str:
        out = []
        for block in items:
            kind = block["type"]
            self.prev = " "
            if kind == "heading":
                level = min(block["level"], 6)
                bid = self.bookmark_id
                self.bookmark_id += 1
                name = self.bookmarks[block["id"]]
                body = (
                    f'<w:bookmarkStart w:id="{bid}" w:name="{name}"/>'
                    f'{self.runs(block["inlines"])}<w:bookmarkEnd w:id="{bid}"/>'
                )
                brk = level == 1 and self.opts.chapter_breaks and block is not self.first_h1
                out.append(self.para(body, f"Heading{level}", page_break=brk))
            elif kind == "paragraph":
                only_image = len(block["inlines"]) == 1 and block["inlines"][0][0] == "image"
                jc = "center" if only_image and not indent else ""
                out.append(self.para(self.runs(block["inlines"]), style, indent=indent, jc=jc))
            elif kind == "code":
                for line in block["text"].split("\n"):
                    parts = line.split("\t")
                    body = "<w:r><w:tab/></w:r>".join(
                        self.run(p, frozenset(), smart=False) for p in parts
                    )
                    out.append(self.para(body, "CodeBlock", indent=indent))
            elif kind == "quote":
                out.append(self.blocks(block["children"], "Quote", indent, depth))
            elif kind == "list":
                out.append(self.list_block(block, indent, depth))
            elif kind == "table":
                out.append(self.table(block))
            elif kind == "hr":
                border = (
                    '<w:pBdr><w:bottom w:val="single" w:sz="6" w:space="1" w:color="BFBFBF"/>'
                    "</w:pBdr>"
                )
                out.append(self.para("", extra=border))
            elif kind == "pagebreak":
                out.append('<w:p><w:r><w:br w:type="page"/></w:r></w:p>')
        return "".join(out)

    def list_block(self, block: dict, indent: int, depth: int) -> str:
        num_id = self.new_num(block["ordered"], block["start"])
        level = min(depth, 8)
        item_indent = 720 + 360 * level
        out = []
        for item in block["items"]:
            first = True
            for child in item["children"]:
                if first and child["type"] == "paragraph":
                    self.prev = " "
                    prefix = ""
                    if item["checked"] is not None:
                        prefix = self.run("\u2611 " if item["checked"] else "\u2610 ", frozenset())
                    body = prefix + self.runs(child["inlines"])
                    out.append(self.para(body, "ListParagraph", numbering=(num_id, level)))
                    first = False
                    continue
                if first:  # item starts with a non-paragraph block: emit the marker alone
                    out.append(self.para("", "ListParagraph", numbering=(num_id, level)))
                    first = False
                nested = depth + 1 if child["type"] == "list" else depth
                out.append(self.blocks([child], "ListParagraph", item_indent, nested))
        return "".join(out)

    def table(self, block: dict) -> str:
        cols = max(len(block["header"]), 1)
        col_w = self.text_width // cols
        grid = "".join(f'<w:gridCol w:w="{col_w}"/>' for _ in range(cols))

        def cell(nodes: list[tuple], col: int, header: bool) -> str:
            align = {"right": "right", "center": "center"}.get(block["aligns"][col], "")
            shade = '<w:shd w:val="clear" w:color="auto" w:fill="F2F2F2"/>' if header else ""
            self.prev = " "
            body = self.runs(nodes, frozenset({"b"}) if header else frozenset())
            jc = f'<w:jc w:val="{align}"/>' if align else ""
            return (
                f'<w:tc><w:tcPr><w:tcW w:w="{col_w}" w:type="dxa"/>{shade}</w:tcPr>'
                f'<w:p><w:pPr><w:pStyle w:val="TableText"/>{jc}</w:pPr>{body}</w:p></w:tc>'
            )

        head = "".join(cell(c, i, True) for i, c in enumerate(block["header"]))
        rows = [f"<w:tr><w:trPr><w:tblHeader/></w:trPr>{head}</w:tr>"]
        for row in block["rows"]:
            rows.append(
                "<w:tr>" + "".join(cell(c, i, False) for i, c in enumerate(row)) + "</w:tr>"
            )
        return (
            '<w:tbl><w:tblPr><w:tblStyle w:val="TableGrid"/><w:tblW w:w="5000" w:type="pct"/>'
            '<w:tblLook w:val="04A0" w:firstRow="1" w:lastRow="0" w:firstColumn="0" '
            'w:lastColumn="0" w:noHBand="0" w:noVBand="1"/></w:tblPr>'
            f"<w:tblGrid>{grid}</w:tblGrid>{''.join(rows)}</w:tbl><w:p/>"
        )

    def toc(self, headings: list[dict]) -> str:
        top = [h for h in headings if h["level"] <= 3]
        levels = {1, 2} if sum(h["level"] == 1 for h in top) > 1 else {2, 3}
        entries = [h for h in top if h["level"] in levels]
        out = [self.para(self.run("Contents", frozenset(), smart=False), "TOCHeading")]
        begin = (
            '<w:r><w:fldChar w:fldCharType="begin"/></w:r>'
            '<w:r><w:instrText xml:space="preserve"> TOC \\o "1-3" \\h \\z \\u </w:instrText></w:r>'
            '<w:r><w:fldChar w:fldCharType="separate"/></w:r>'
        )
        end = '<w:r><w:fldChar w:fldCharType="end"/></w:r>'
        if not entries:
            return "".join(out) + self.para(begin + end)
        for i, h in enumerate(entries):
            self.prev = " "
            name = self.bookmarks[h["id"]]
            text = self.runs(h["inlines"])
            link = f'<w:hyperlink w:anchor="{name}" w:history="1">{text}</w:hyperlink>'
            body = (begin if i == 0 else "") + link + (end if i == len(entries) - 1 else "")
            out.append(self.para(body, f"TOC{h['level'] - min(levels) + 1}"))
        out.append('<w:p><w:r><w:br w:type="page"/></w:r></w:p>')
        return "".join(out)

    def cover(self, title: str, meta: dict[str, str]) -> str:
        out = [self.para(self.run(title, frozenset()), "Title")]
        subtitle = self.opts.subtitle or meta.get("subtitle")
        if subtitle:
            out.append(self.para(self.run(subtitle, frozenset()), "Subtitle"))
        author = self.opts.author or meta.get("author")
        if author:
            out.append(self.para(self.run(author, frozenset(), smart=False), "CoverMeta"))
        today = date.today()
        when = self.opts.date or meta.get("date") or f"{today:%B} {today.day}, {today.year}"
        out.append(self.para(self.run(when, frozenset(), smart=False), "CoverMeta"))
        out.append('<w:p><w:r><w:br w:type="page"/></w:r></w:p>')
        return "".join(out)

    # -------------------------------------------------------- package

    def build(self, source: Path) -> dict[str, bytes]:
        meta, items = mdlite.parse(source.read_text(encoding="utf-8"))
        headings: list[dict] = []
        assign_ids(items, set(), headings)
        for h in headings:
            self.bookmarks[h["id"]] = ("_" + re.sub(r"\W", "_", h["id"]))[:40]
        self.first_h1 = next((b for b in items if b["type"] == "heading" and b["level"] == 1), None)
        title = (
            self.opts.title
            or meta.get("title")
            or (mdlite.plain_text(self.first_h1["inlines"]) if self.first_h1 else source.stem)
        )
        if self.opts.cover and not (self.opts.title or meta.get("title")):
            if items and items[0] is self.first_h1:
                items = items[1:]
        body = ""
        if self.opts.cover:
            body += self.cover(title, meta)
        if self.opts.toc:
            body += self.toc(headings)
        body += self.blocks(items)
        header_rid = self.rel(f"{REL}/header", "header1.xml")
        footer_rid = self.rel(f"{REL}/footer", "footer1.xml")
        width, height = PAGE[self.opts.page_size]
        margin = twips(self.opts.margins)
        title_pg = "<w:titlePg/>" if self.opts.cover else ""
        sect = (
            f'<w:sectPr><w:headerReference w:type="default" r:id="{header_rid}"/>'
            f'<w:footerReference w:type="default" r:id="{footer_rid}"/>'
            f'<w:pgSz w:w="{width}" w:h="{height}"/><w:pgMar w:top="{margin}" '
            f'w:right="{margin}" w:bottom="{margin}" w:left="{margin}" w:header="708" '
            f'w:footer="708" w:gutter="0"/>{title_pg}</w:sectPr>'
        )
        document = f"{XML_HEAD}<w:document {NS}><w:body>{body}{sect}</w:body></w:document>"
        author = self.opts.author or meta.get("author") or ""
        files = {
            "[Content_Types].xml": content_types(),
            "_rels/.rels": ROOT_RELS,
            "docProps/core.xml": core_props(title, author),
            "docProps/app.xml": APP_PROPS,
            "word/document.xml": document,
            "word/styles.xml": styles(self.opts.font),
            "word/numbering.xml": numbering(self.nums),
            "word/settings.xml": settings(self.opts.toc),
            "word/header1.xml": header(
                "" if self.opts.no_header else title, self.opts.watermark or ""
            ),
            "word/footer1.xml": footer(not self.opts.no_page_numbers),
            "word/_rels/document.xml.rels": self.document_rels(),
        }
        out = {name: text.encode("utf-8") for name, text in files.items()}
        out.update({f"word/media/{name}": data for name, data in self.media.items()})
        return out

    def document_rels(self) -> str:
        fixed = [
            ("rId1", f"{REL}/styles", "styles.xml", False),
            ("rId2", f"{REL}/numbering", "numbering.xml", False),
            ("rId3", f"{REL}/settings", "settings.xml", False),
        ]
        rows = []
        for rid, kind, target, external in fixed + self.rels:
            mode = ' TargetMode="External"' if external else ""
            rows.append(f'<Relationship Id="{rid}" Type="{kind}" Target="{x(target)}"{mode}/>')
        return (
            f'{XML_HEAD}<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/'
            f'relationships">{"".join(rows)}</Relationships>'
        )


def assign_ids(items: list[dict], seen: set[str], found: list[dict]) -> None:
    for block in items:
        if block["type"] == "heading":
            block["id"] = mdlite.slugify(mdlite.plain_text(block["inlines"]), seen)
            found.append(block)
        elif block["type"] == "quote":
            assign_ids(block["children"], seen, found)
        elif block["type"] == "list":
            for item in block["items"]:
                assign_ids(item["children"], seen, found)


# ------------------------------------------------------------ package parts

ROOT_RELS = (
    f'{XML_HEAD}<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    f'<Relationship Id="rId1" Type="{REL}/officeDocument" Target="word/document.xml"/>'
    '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/'
    'metadata/core-properties" Target="docProps/core.xml"/>'
    f'<Relationship Id="rId3" Type="{REL}/extended-properties" Target="docProps/app.xml"/>'
    "</Relationships>"
)
APP_PROPS = (
    f'{XML_HEAD}<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/'
    'extended-properties"><Application>make-docx</Application></Properties>'
)


def content_types() -> str:
    wml = "application/vnd.openxmlformats-officedocument.wordprocessingml"
    parts = {
        "/word/document.xml": f"{wml}.document.main+xml",
        "/word/styles.xml": f"{wml}.styles+xml",
        "/word/numbering.xml": f"{wml}.numbering+xml",
        "/word/settings.xml": f"{wml}.settings+xml",
        "/word/header1.xml": f"{wml}.header+xml",
        "/word/footer1.xml": f"{wml}.footer+xml",
        "/docProps/core.xml": "application/vnd.openxmlformats-package.core-properties+xml",
        "/docProps/app.xml": "application/vnd.openxmlformats-officedocument."
        "extended-properties+xml",
    }
    defaults = {
        "rels": "application/vnd.openxmlformats-package.relationships+xml",
        "xml": "application/xml",
        "png": "image/png",
        "jpeg": "image/jpeg",
        "gif": "image/gif",
    }
    rows = [f'<Default Extension="{e}" ContentType="{t}"/>' for e, t in defaults.items()]
    rows += [f'<Override PartName="{p}" ContentType="{t}"/>' for p, t in parts.items()]
    return (
        f'{XML_HEAD}<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        f"{''.join(rows)}</Types>"
    )


def core_props(title: str, author: str) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")  # noqa: UP017 (py3.9)
    return (
        f"{XML_HEAD}<cp:coreProperties "
        'xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
        'xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
        f"<dc:title>{x(title)}</dc:title><dc:creator>{x(author)}</dc:creator>"
        f'<dcterms:created xsi:type="dcterms:W3CDTF">{now}</dcterms:created>'
        f'<dcterms:modified xsi:type="dcterms:W3CDTF">{now}</dcterms:modified>'
        "</cp:coreProperties>"
    )


def settings(update_fields: bool) -> str:
    update = '<w:updateFields w:val="true"/>' if update_fields else ""
    return (
        f'{XML_HEAD}<w:settings xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/'
        f'2006/main"><w:defaultTabStop w:val="720"/>{update}<w:compat><w:compatSetting '
        'w:name="compatibilityMode" w:uri="http://schemas.microsoft.com/office/word" '
        'w:val="15"/></w:compat></w:settings>'
    )


def _style(sid: str, name: str, ppr: str = "", rpr: str = "", kind: str = "paragraph") -> str:
    default = ' w:default="1"' if sid == "Normal" else ""
    based = '<w:basedOn w:val="Normal"/>' if kind == "paragraph" and sid != "Normal" else ""
    return (
        f'<w:style w:type="{kind}"{default} w:styleId="{sid}"><w:name w:val="{name}"/>{based}'
        f"<w:qFormat/>{f'<w:pPr>{ppr}</w:pPr>' if ppr else ''}"
        f"{f'<w:rPr>{rpr}</w:rPr>' if rpr else ''}</w:style>"
    )


DEFAULT_STYLES = (
    '<w:style w:type="character" w:default="1" w:styleId="DefaultParagraphFont">'
    '<w:name w:val="Default Paragraph Font"/><w:uiPriority w:val="1"/><w:semiHidden/>'
    "<w:unhideWhenUsed/></w:style>"
    '<w:style w:type="table" w:default="1" w:styleId="TableNormal"><w:name w:val="Normal Table"/>'
    '<w:uiPriority w:val="99"/><w:semiHidden/><w:unhideWhenUsed/><w:tblPr><w:tblInd w:w="0" '
    'w:type="dxa"/><w:tblCellMar><w:top w:w="0" w:type="dxa"/><w:left w:w="108" w:type="dxa"/>'
    '<w:bottom w:w="0" w:type="dxa"/><w:right w:w="108" w:type="dxa"/></w:tblCellMar></w:tblPr>'
    "</w:style>"
)


def styles(font: str) -> str:
    head_font = "Calibri Light" if font == "Calibri" else font
    mono = '<w:rFonts w:ascii="Consolas" w:hAnsi="Consolas" w:cs="Consolas"/>'
    color = '<w:color w:val="1F2A44"/>'
    heading_sizes = [32, 26, 24, 22, 22, 22]
    items = [
        _style("Normal", "Normal", '<w:spacing w:after="140" w:line="276" w:lineRule="auto"/>'),
        _style(
            "Title",
            "Title",
            '<w:spacing w:before="2400" w:after="240"/>',
            f'<w:rFonts w:ascii="{head_font}" w:hAnsi="{head_font}"/>{color}'
            '<w:sz w:val="72"/><w:szCs w:val="72"/>',
        ),
        _style(
            "Subtitle",
            "Subtitle",
            '<w:spacing w:after="600"/>',
            '<w:color w:val="595959"/><w:sz w:val="32"/><w:szCs w:val="32"/>',
        ),
        _style("CoverMeta", "Cover Meta", '<w:spacing w:after="60"/>', '<w:sz w:val="24"/>'),
    ]
    for level, size in enumerate(heading_sizes, start=1):
        items.append(
            _style(
                f"Heading{level}",
                f"heading {level}",
                f'<w:keepNext/><w:keepLines/><w:spacing w:before="{360 if level < 3 else 240}" '
                f'w:after="120"/><w:outlineLvl w:val="{level - 1}"/>',
                f'<w:rFonts w:ascii="{head_font}" w:hAnsi="{head_font}"/><w:b/>{color}'
                f'<w:sz w:val="{size}"/><w:szCs w:val="{size}"/>',
            )
        )
    items += [
        _style(
            "TOCHeading",
            "TOC Heading",
            '<w:keepNext/><w:spacing w:after="240"/>',
            f'<w:b/>{color}<w:sz w:val="32"/>',
        ),
        _style("TOC1", "toc 1", '<w:spacing w:after="80"/>'),
        _style("TOC2", "toc 2", '<w:spacing w:after="60"/><w:ind w:left="360"/>'),
        _style("TOC3", "toc 3", '<w:spacing w:after="60"/><w:ind w:left="720"/>'),
        _style(
            "Quote",
            "Quote",
            '<w:pBdr><w:left w:val="single" w:sz="18" w:space="8" w:color="C9C9C4"/></w:pBdr>'
            '<w:ind w:left="360" w:right="360"/>',
            '<w:color w:val="404040"/>',
        ),
        _style(
            "CodeBlock",
            "Code Block",
            '<w:keepLines/><w:shd w:val="clear" w:color="auto" w:fill="F4F4F2"/>'
            '<w:spacing w:after="0" w:line="240" w:lineRule="auto"/>',
            f'{mono}<w:sz w:val="18"/><w:szCs w:val="18"/>',
        ),
        _style(
            "ListParagraph", "List Paragraph", '<w:spacing w:after="60"/><w:contextualSpacing/>'
        ),
        _style(
            "TableText",
            "Table Text",
            '<w:spacing w:before="40" w:after="40"/>',
            '<w:sz w:val="20"/>',
        ),
        _style("Header", "header", "", '<w:color w:val="808080"/><w:sz w:val="18"/>'),
        _style("Footer", "footer", "", '<w:color w:val="808080"/><w:sz w:val="18"/>'),
        _style(
            "Hyperlink",
            "Hyperlink",
            "",
            '<w:color w:val="1F4E8C"/><w:u w:val="single"/>',
            kind="character",
        ),
        _style(
            "InlineCode",
            "Inline Code",
            "",
            f'{mono}<w:sz w:val="19"/><w:shd w:val="clear" w:color="auto" w:fill="F1F1EE"/>',
            kind="character",
        ),
    ]
    table = (
        '<w:style w:type="table" w:styleId="TableGrid"><w:name w:val="Table Grid"/>'
        "<w:tblPr><w:tblBorders>"
        + "".join(
            f'<w:{side} w:val="single" w:sz="4" w:space="0" w:color="BFBFBF"/>'
            for side in ("top", "left", "bottom", "right", "insideH", "insideV")
        )
        + '</w:tblBorders><w:tblCellMar><w:left w:w="100" w:type="dxa"/>'
        '<w:right w:w="100" w:type="dxa"/></w:tblCellMar></w:tblPr></w:style>'
    )
    defaults = (
        f'<w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="{font}" w:hAnsi="{font}" '
        f'w:eastAsia="{font}" w:cs="{font}"/><w:sz w:val="22"/><w:szCs w:val="22"/>'
        '<w:lang w:val="en-US"/></w:rPr></w:rPrDefault><w:pPrDefault/></w:docDefaults>'
    )
    return (
        f'{XML_HEAD}<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/'
        f'main">{defaults}{DEFAULT_STYLES}{"".join(items)}{table}</w:styles>'
    )


def numbering(nums: list[tuple[int, int, int]]) -> str:
    bullets = ["•", "◦", "▪"]
    formats = [("decimal", "%{n}."), ("lowerLetter", "%{n}."), ("lowerRoman", "%{n}.")]
    abstract = []
    for aid in (0, 1):
        levels = []
        for lvl in range(9):
            if aid == 0:
                fmt, text = "bullet", bullets[lvl % 3]
                font = '<w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial"/></w:rPr>'
            else:
                fmt, pattern = formats[lvl % 3]
                text, font = pattern.format(n=lvl + 1), ""
            left = 720 + 360 * lvl
            levels.append(
                f'<w:lvl w:ilvl="{lvl}"><w:start w:val="1"/><w:numFmt w:val="{fmt}"/>'
                f'<w:lvlText w:val="{text}"/><w:lvlJc w:val="left"/><w:pPr>'
                f'<w:ind w:left="{left}" w:hanging="360"/></w:pPr>{font}</w:lvl>'
            )
        abstract.append(
            f'<w:abstractNum w:abstractNumId="{aid}"><w:multiLevelType w:val="hybridMultilevel"/>'
            f"{''.join(levels)}</w:abstractNum>"
        )
    instances = []
    for num_id, aid, start in nums:
        overrides = (
            "".join(
                f'<w:lvlOverride w:ilvl="{lvl}"><w:startOverride w:val="{start}"/></w:lvlOverride>'
                for lvl in range(9)
            )
            if aid == 1
            else ""
        )
        instances.append(
            f'<w:num w:numId="{num_id}"><w:abstractNumId w:val="{aid}"/>{overrides}</w:num>'
        )
    return (
        f'{XML_HEAD}<w:numbering xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/'
        f'2006/main">{"".join(abstract)}{"".join(instances)}</w:numbering>'
    )


WATERMARK_SHAPETYPE = (
    '<v:shapetype id="_x0000_t136" coordsize="21600,21600" o:spt="136" adj="10800" '
    'path="m@7,l@8,m@5,21600l@6,21600e"><v:formulas>'
    + "".join(
        f'<v:f eqn="{eqn}"/>'
        for eqn in (
            "sum #0 0 10800",
            "prod #0 2 1",
            "sum 21600 0 @1",
            "sum 0 0 @2",
            "sum 21600 0 @3",
            "if @0 @3 0",
            "if @0 21600 @1",
            "if @0 0 @2",
            "if @0 @4 21600",
            "mid @5 @6",
            "mid @8 @5",
            "mid @7 @8",
            "mid @6 @7",
            "sum @6 0 @5",
        )
    )
    + '</v:formulas><v:path textpathok="t" o:connecttype="custom" '
    'o:connectlocs="@9,0;@10,10800;@11,21600;@12,10800" o:connectangles="270,180,90,0"/>'
    '<v:textpath on="t" fitshape="t"/><v:handles><v:h position="#0,bottomRight" '
    'xrange="6629,14971"/></v:handles><o:lock v:ext="edit" text="t" shapetype="t"/></v:shapetype>'
)


def header(title: str, watermark: str) -> str:
    runs = ""
    if watermark:
        runs += (
            f'<w:r><w:pict>{WATERMARK_SHAPETYPE}<v:shape id="Watermark" o:spid="_x0000_s2049" '
            'type="#_x0000_t136" style="position:absolute;margin-left:0;margin-top:0;'
            "width:468pt;height:117pt;rotation:315;z-index:-251657216;"
            "mso-position-horizontal:center;mso-position-horizontal-relative:margin;"
            'mso-position-vertical:center;mso-position-vertical-relative:margin" '
            'o:allowincell="f" fillcolor="silver" stroked="f"><v:fill opacity=".35"/>'
            '<v:textpath style="font-family:&quot;Calibri&quot;;font-size:1pt" '
            f'string="{x(watermark)}"/><w10:wrap anchorx="margin" anchory="margin"/></v:shape>'
            "</w:pict></w:r>"
        )
    if title:
        runs += f'<w:r><w:t xml:space="preserve">{x(title)}</w:t></w:r>'
    return (
        f'{XML_HEAD}<w:hdr {NS}><w:p><w:pPr><w:pStyle w:val="Header"/><w:jc w:val="center"/>'
        f"</w:pPr>{runs}</w:p></w:hdr>"
    )


def _field(code: str, shown: str) -> str:
    return (
        '<w:r><w:fldChar w:fldCharType="begin"/></w:r>'
        f'<w:r><w:instrText xml:space="preserve"> {code} </w:instrText></w:r>'
        '<w:r><w:fldChar w:fldCharType="separate"/></w:r>'
        f"<w:r><w:t>{shown}</w:t></w:r>"
        '<w:r><w:fldChar w:fldCharType="end"/></w:r>'
    )


def footer(page_numbers: bool) -> str:
    body = ""
    if page_numbers:
        body = (
            '<w:r><w:t xml:space="preserve">Page </w:t></w:r>'
            + _field("PAGE", "1")
            + '<w:r><w:t xml:space="preserve"> of </w:t></w:r>'
            + _field("NUMPAGES", "1")
        )
    return (
        f'{XML_HEAD}<w:ftr {NS}><w:p><w:pPr><w:pStyle w:val="Footer"/><w:jc w:val="center"/>'
        f"</w:pPr>{body}</w:p></w:ftr>"
    )


def write_docx(files: dict[str, bytes], out: Path) -> None:
    order = ["[Content_Types].xml", "_rels/.rels"]
    names = order + sorted(n for n in files if n not in order)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for name in names:
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(info, files[name])


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="make_docx.py", description=__doc__.split("\n\n")[0])
    p.add_argument("input", type=Path)
    p.add_argument("output", type=Path, nargs="?")
    p.add_argument("--cover", action="store_true", help="title page from title/author/date")
    p.add_argument("--toc", action="store_true", help="table of contents (links, Word adds pages)")
    p.add_argument("--title")
    p.add_argument("--subtitle")
    p.add_argument("--author")
    p.add_argument("--date")
    p.add_argument("--watermark", help='diagonal text on every page, e.g. "DRAFT"')
    p.add_argument("--page-size", choices=sorted(PAGE), default="letter")
    p.add_argument("--margins", default="1in", help="1in, 2.5cm, 25mm or 72pt")
    p.add_argument("--font", default="Calibri", help="body font name installed on readers")
    p.add_argument("--chapter-breaks", action="store_true", help="start each H1 on a new page")
    p.add_argument("--no-page-numbers", action="store_true")
    p.add_argument("--no-header", action="store_true", help="no running title header")
    p.add_argument("--strict", action="store_true", help="fail on any missing or skipped image")
    p.add_argument("--quiet", action="store_true")
    opts = p.parse_args(argv)
    try:
        twips(opts.margins)
    except ValueError:
        p.error("--margins must look like 1in, 2.5cm, 25mm or 72pt")
    if not re.fullmatch(r"[\w .-]{1,64}", opts.font):
        p.error("--font must be a plain font name")
    return opts


def main(argv: list[str] | None = None) -> int:
    opts = parse_args(argv)
    if not opts.input.is_file():
        print(f"make_docx: input not found: {opts.input}", file=sys.stderr)
        return 2
    out = opts.output or opts.input.with_suffix(".docx")
    doc = Docx(opts.input.parent, opts)
    try:
        files = doc.build(opts.input)
        write_docx(files, out)
    except (RenderError, OSError) as exc:
        print(f"make_docx: {exc}", file=sys.stderr)
        return 3
    if not opts.quiet:
        for warning in doc.warnings:
            print(f"warning: {warning}", file=sys.stderr)
        size = out.stat().st_size // 1024
        print(f"Done. {len(doc.media)} images, {size} KB: {out}", file=sys.stderr)
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
