"""Small, dependency-free Markdown parser shared by make-pdf and make-docx.

Keep the copies in make-pdf/scripts/ and make-docx/scripts/ identical (a test checks it).

Supported: YAML-style front matter (flat key: value), ATX and setext headings, paragraphs,
emphasis, strong, strikethrough, code spans, fenced and indented code, block quotes, nested
ordered/bullet/task lists, GFM pipe tables, links, autolinks, images with {width=..}
attributes, hard breaks, horizontal rules and `<!-- pagebreak -->`. Raw HTML is kept as
literal text (never rendered), which keeps untrusted Markdown safe to convert.

Blocks are dicts with a "type" key. Inlines are tuples:
  ("text", s) ("code", s) ("strong", kids) ("em", kids) ("del", kids)
  ("link", href, kids) ("image", src, alt, attrs) ("br",)
"""

from __future__ import annotations

import re

__all__ = ["parse", "parse_inline", "plain_text", "slugify", "smarten"]

FENCE_RE = re.compile(r"^( {0,3})(`{3,}|~{3,})\s*([^`\s]*)[^`]*$")
ATX_RE = re.compile(r"^ {0,3}(#{1,6})(?:[ \t]+(.*?))?(?:[ \t]+#+)?[ \t]*$")
HR_RE = re.compile(r"^ {0,3}([-*_])(?:[ \t]*\1){2,}[ \t]*$")
LIST_RE = re.compile(r"^( {0,3})([-+*]|\d{1,9}[.)])(?:([ \t]+)(.*)|[ \t]*)$")
TASK_RE = re.compile(r"^\[([ xX])\][ \t]+")
TABLE_DELIM_RE = re.compile(r"^ {0,3}\|?[ \t]*:?-+:?[ \t]*(\|[ \t]*:?-+:?[ \t]*)*\|?[ \t]*$")
PAGEBREAK_RE = re.compile(r"^ {0,3}(<!--\s*pagebreak\s*-->|\\pagebreak|\\newpage)[ \t]*$", re.I)
FRONT_KEY_RE = re.compile(r"^([A-Za-z][\w-]*):[ \t]*(.*)$")


def parse(text: str) -> tuple[dict[str, str], list[dict]]:
    """Return (front matter, blocks)."""
    lines = text.replace("\r\n", "\n").replace("\r", "\n").expandtabs(4).split("\n")
    meta: dict[str, str] = {}
    if lines and lines[0].strip() == "---":
        for end in range(1, len(lines)):
            if lines[end].strip() in ("---", "..."):
                body = lines[1:end]
                if all(not ln.strip() or FRONT_KEY_RE.match(ln) for ln in body):
                    for ln in body:
                        m = FRONT_KEY_RE.match(ln)
                        if m:
                            meta[m.group(1).lower()] = m.group(2).strip().strip("\"'")
                    lines = lines[end + 1 :]
                break
    return meta, _blocks(lines)


def _blocks(lines: list[str]) -> list[dict]:
    out: list[dict] = []
    para: list[str] = []
    i = 0

    def flush() -> None:
        if para:
            out.append({"type": "paragraph", "inlines": parse_inline("\n".join(para).strip())})
            para.clear()

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not stripped:
            flush()
            i += 1
            continue
        if PAGEBREAK_RE.match(line):
            flush()
            out.append({"type": "pagebreak"})
            i += 1
            continue
        fence = FENCE_RE.match(line)
        if fence:
            flush()
            indent, marker, lang = len(fence.group(1)), fence.group(2), fence.group(3)
            body: list[str] = []
            i += 1
            while i < len(lines):
                close = lines[i].strip()
                if close.startswith(marker[0] * len(marker)) and not close.strip(marker[0]):
                    i += 1
                    break
                body.append(_dedent(lines[i], indent))
                i += 1
            out.append({"type": "code", "lang": lang, "text": "\n".join(body)})
            continue
        if para and re.match(r"^ {0,3}=+[ \t]*$", line):
            out.append(_heading(1, " ".join(p.strip() for p in para)))
            para.clear()
            i += 1
            continue
        if para and re.match(r"^ {0,3}-+[ \t]*$", line):
            out.append(_heading(2, " ".join(p.strip() for p in para)))
            para.clear()
            i += 1
            continue
        atx = ATX_RE.match(line)
        if atx:
            flush()
            out.append(_heading(len(atx.group(1)), atx.group(2) or ""))
            i += 1
            continue
        if HR_RE.match(line):
            flush()
            out.append({"type": "hr"})
            i += 1
            continue
        if not para and line.startswith("    "):
            body = []
            while i < len(lines) and (lines[i].startswith("    ") or not lines[i].strip()):
                body.append(lines[i][4:])
                i += 1
            while body and not body[-1].strip():
                body.pop()
            out.append({"type": "code", "lang": "", "text": "\n".join(body)})
            continue
        if re.match(r"^ {0,3}>", line):
            flush()
            quoted: list[str] = []
            while i < len(lines) and lines[i].strip():
                m = re.match(r"^ {0,3}> ?(.*)$", lines[i])
                quoted.append(m.group(1) if m else lines[i])
                i += 1
            out.append({"type": "quote", "children": _blocks(quoted)})
            continue
        if (
            "|" in line
            and i + 1 < len(lines)
            and TABLE_DELIM_RE.match(lines[i + 1])
            and "-" in lines[i + 1]
        ):
            header = _cells(line)
            aligns = [_align(c) for c in _cells(lines[i + 1])]
            if len(aligns) == len(header):
                flush()
                i += 2
                rows = []
                while i < len(lines) and lines[i].strip() and "|" in lines[i]:
                    cells = _cells(lines[i])[: len(header)]
                    rows.append(cells + [""] * (len(header) - len(cells)))
                    i += 1
                out.append(
                    {
                        "type": "table",
                        "aligns": aligns,
                        "header": [parse_inline(c) for c in header],
                        "rows": [[parse_inline(c) for c in row] for row in rows],
                    }
                )
                continue
        item = LIST_RE.match(line)
        # A list interrupts a paragraph only with content and a bullet or "1." marker.
        can_interrupt = item and item.group(4) and item.group(2)[:-1] in ("-", "+", "*", "1", "")
        if item and (not para or can_interrupt):
            flush()
            block, i = _list(lines, i)
            out.append(block)
            continue
        para.append(line)
        i += 1
    flush()
    return out


def _sibling(line: str, base: int, ordered: bool, marker: str) -> bool:
    """True when line starts another item of the same list."""
    m = LIST_RE.match(line)
    if not m or len(m.group(1)) != base or m.group(2)[0].isdigit() != ordered:
        return False
    return m.group(2)[-1] == marker[-1] if ordered else m.group(2) == marker


def _heading(level: int, raw: str) -> dict:
    return {"type": "heading", "level": level, "inlines": parse_inline(raw.strip())}


def _dedent(line: str, n: int) -> str:
    strip = len(line) - len(line.lstrip(" "))
    return line[min(n, strip) :]


def _cells(line: str) -> list[str]:
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|") and not s.endswith("\\|"):
        s = s[:-1]
    cells, cur, esc = [], "", False
    for ch in s:
        if esc:
            cur += ch if ch == "|" else "\\" + ch
            esc = False
        elif ch == "\\":
            esc = True
        elif ch == "|":
            cells.append(cur.strip())
            cur = ""
        else:
            cur += ch
    cells.append(cur.strip())
    return cells


def _align(cell: str) -> str:
    c = cell.strip()
    if c.startswith(":") and c.endswith(":"):
        return "center"
    if c.endswith(":"):
        return "right"
    return "left" if c.startswith(":") else ""


def _list(lines: list[str], i: int) -> tuple[dict, int]:
    first = LIST_RE.match(lines[i])
    if first is None:
        raise ValueError("not a list item")
    marker = first.group(2)
    ordered = marker[0].isdigit()
    start = int(marker[:-1]) if ordered else 1
    base = len(first.group(1))
    items: list[dict] = []
    loose = False
    while i < len(lines):
        m = LIST_RE.match(lines[i])
        if not m or not _sibling(lines[i], base, ordered, marker):
            break
        gap = m.group(3) or " "
        content_indent = base + len(m.group(2)) + (len(gap) if len(gap) <= 4 else 1)
        body = [m.group(4) or ""]
        i += 1
        blank_inside = False
        while i < len(lines):
            line = lines[i]
            if not line.strip():
                nxt = next((ln for ln in lines[i + 1 :] if ln.strip()), None)
                if nxt is None:
                    break
                nxt_indent = len(nxt) - len(nxt.lstrip(" "))
                if nxt_indent >= content_indent:
                    body.append("")
                    blank_inside = True
                    i += 1
                    continue
                if _sibling(nxt, base, ordered, marker):
                    loose = True
                break
            indent = len(line) - len(line.lstrip(" "))
            if indent >= content_indent:
                body.append(line[content_indent:])
            elif LIST_RE.match(line) and indent <= base + 3:
                if indent > base:
                    body.append(line[min(indent, content_indent) :])
                else:
                    break
            elif (
                FENCE_RE.match(line)
                or ATX_RE.match(line)
                or HR_RE.match(line)
                or re.match(r"^ {0,3}>", line)
            ):
                break
            else:
                body.append(line.strip())  # lazy continuation
            i += 1
        checked = None
        task = TASK_RE.match(body[0])
        if task:
            checked = task.group(1).lower() == "x"
            body[0] = body[0][task.end() :]
        loose = loose or blank_inside
        items.append({"checked": checked, "children": _blocks(body)})
        while i < len(lines) and not lines[i].strip():
            nxt = next((ln for ln in lines[i:] if ln.strip()), None)
            if nxt and _sibling(nxt, base, ordered, marker):
                loose = True
                i += 1
            else:
                break
    return {
        "type": "list",
        "ordered": ordered,
        "start": start,
        "tight": not loose,
        "items": items,
    }, i


# ---------------------------------------------------------------- inlines

PH = ""  # private-use placeholder brackets for protected spans
PH_END = ""
_LABEL = r"\[((?:[^\[\]]|\[[^\[\]]*\])*)\]"
_DEST = r"\(\s*<?([^\s<>()]*(?:\([^\s()]*\))?[^\s<>()]*)>?(?:\s+\"[^\"]*\")?\s*\)"
INLINE_PATTERNS = [
    ("image", re.compile("!" + _LABEL + _DEST + r"(\{[^}\n]*\})?")),
    ("link", re.compile(_LABEL + _DEST)),
    ("autolink", re.compile(r"<((?:https?|mailto):[^\s<>]+)>")),
    ("bare", re.compile(r"(?<![\w/\"'(=])(https?://[^\s<>()\[\]]*[^\s<>()\[\].,;:!?\"'])")),
    ("strong", re.compile(r"\*\*(?=\S)(.+?)(?<=\S)\*\*|(?<!\w)__(?=\S)(.+?)(?<=\S)__(?!\w)", re.S)),
    ("del", re.compile(r"~~(?=\S)(.+?)(?<=\S)~~", re.S)),
    (
        "em",
        re.compile(
            r"\*(?=[^\s*])(.+?)(?<=[^\s*])\*|(?<!\w)_(?=[^\s_])(.+?)(?<=[^\s_])_(?!\w)", re.S
        ),
    ),
    ("br", re.compile(r"(?: {2,}|\\)\n")),
]


def parse_inline(text: str) -> list[tuple]:
    protected: list[tuple] = []

    def protect(node: tuple) -> str:
        protected.append(node)
        return f"{PH}{len(protected) - 1}{PH_END}"

    def code_span(m: re.Match) -> str:
        body = m.group(2).replace("\n", " ")
        if body.startswith(" ") and body.endswith(" ") and body.strip():
            body = body[1:-1]
        return protect(("code", body))

    text = re.sub(r"(`+)(.+?)(?<!`)\1(?!`)", code_span, text, flags=re.S)
    text = re.sub(
        r"\\([\\`*_{}\[\]()#+\-.!|~<>\"'])", lambda m: protect(("text", m.group(1))), text
    )
    return _inline(text, protected)


def _inline(text: str, protected: list[tuple]) -> list[tuple]:
    nodes: list[tuple] = []
    pos = 0
    while pos < len(text):
        best = None
        for kind, rx in INLINE_PATTERNS:
            m = rx.search(text, pos)
            if m and (best is None or m.start() < best[1].start()):
                best = (kind, m)
        if best is None:
            break
        kind, m = best
        _text(nodes, text[pos : m.start()], protected)
        if kind == "image":
            alt = plain_text(_inline(m.group(1), protected))
            nodes.append(("image", _restore(m.group(2), protected), alt, _attrs(m.group(3))))
        elif kind == "link":
            nodes.append(("link", _restore(m.group(2), protected), _inline(m.group(1), protected)))
        elif kind in ("autolink", "bare"):
            url = m.group(1)
            label = url[7:] if url.startswith("mailto:") else url
            nodes.append(("link", url, [("text", label)]))
        elif kind == "br":
            nodes.append(("br",))
        else:
            inner = next(g for g in m.groups() if g is not None)
            nodes.append((kind, _inline(inner, protected)))
        pos = m.end()
    _text(nodes, text[pos:], protected)
    return nodes


def _text(nodes: list[tuple], s: str, protected: list[tuple]) -> None:
    for part in re.split(f"({PH}\\d+{PH_END})", s):
        if not part:
            continue
        m = re.fullmatch(f"{PH}(\\d+){PH_END}", part)
        node = protected[int(m.group(1))] if m else ("text", part.replace("\n", " "))
        if node[0] == "text" and nodes and nodes[-1][0] == "text":
            nodes[-1] = ("text", nodes[-1][1] + node[1])
        else:
            nodes.append(node)


def _restore(s: str, protected: list[tuple]) -> str:
    return re.sub(f"{PH}(\\d+){PH_END}", lambda m: plain_text([protected[int(m.group(1))]]), s)


def _attrs(raw: str | None) -> dict[str, str]:
    if not raw:
        return {}
    return dict(re.findall(r"([A-Za-z]+)=\"?([^\s\"}]+)\"?", raw))


def plain_text(nodes: list[tuple]) -> str:
    out = []
    for node in nodes:
        kind = node[0]
        if kind in ("text", "code"):
            out.append(node[1])
        elif kind == "br":
            out.append(" ")
        elif kind == "image":
            out.append(node[2])
        elif kind == "link":
            out.append(plain_text(node[2]))
        else:
            out.append(plain_text(node[1]))
    return "".join(out)


def slugify(text: str, seen: set[str] | None = None) -> str:
    base = re.sub(r"[^\w\s-]", "", text.lower()).strip()
    base = re.sub(r"[\s_-]+", "-", base).strip("-") or "section"
    if seen is None:
        return base
    slug, n = base, 1
    while slug in seen:
        n += 1
        slug = f"{base}-{n}"
    seen.add(slug)
    return slug


def smarten(text: str, prev: str = " ") -> str:
    """Curly quotes, em dashes and ellipses for prose (never call on code)."""
    text = text.replace("---", "—").replace("--", "—").replace("...", "…")
    out = []
    for ch in text:
        if ch in "\"'":
            opening = prev.isspace() or prev in "([{—-‘“" or prev == ""
            if ch == '"':
                out.append("“" if opening else "”")
            else:
                out.append("‘" if opening else "’")
        else:
            out.append(ch)
        prev = out[-1]
    return "".join(out)
