"""Helper scripts shipped inside skills: Markdown to PDF/DOCX, QA helpers, UI tree parsers."""

import importlib.util
import json
import os
import shutil
import struct
import subprocess
import sys
import zipfile
import zlib
from pathlib import Path
from xml.etree import ElementTree

import pytest

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / ".agents" / "skills"
sys.dont_write_bytecode = True  # never leave __pycache__ inside .agents/skills


def load_module(skill: str, name: str):
    path = SKILLS / skill / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"{skill.replace('-', '_')}_{name}", path)
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(path.parent))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.remove(str(path.parent))
    return module


mdlite = load_module("make-pdf", "mdlite")
make_pdf = load_module("make-pdf", "make_pdf")
make_docx = load_module("make-docx", "make_docx")
ui_tree = load_module("android-qa", "ui_tree")
ax_tree = load_module("ios-qa", "ax_tree")


def png(width: int, height: int) -> bytes:
    raw = b"".join(b"\x00" + b"\x10\x60\xa0" * width for _ in range(height))

    def chunk(tag: bytes, data: bytes) -> bytes:
        body = tag + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body))

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", zlib.compress(raw))
        + chunk(b"IEND", b"")
    )


SAMPLE = """---
title: Quarterly Review
author: Platform Team
---
# Summary

We said "ship it" -- and it's done... See [notes](https://example.com) and [metrics](#metrics).

- one
- two
  - nested **bold**
- [x] done

1. first
2. second

# Metrics

| Metric | Value |
|:--|--:|
| Crash-free | 99.8% |

![Chart](chart.png){width=50%}

![Remote](https://example.com/x.png)

![Escape](../secret.png)

```python
print("<b>")
```

> Quote

<script>alert(1)</script>

[bad](javascript:alert(1))
"""


@pytest.fixture
def doc(tmp_path: Path) -> Path:
    (tmp_path / "chart.png").write_bytes(png(400, 200))
    path = tmp_path / "doc.md"
    path.write_text(SAMPLE)
    return path


# --- shared parser ---


def test_parser_copies_are_identical():
    a = (SKILLS / "make-pdf/scripts/mdlite.py").read_bytes()
    b = (SKILLS / "make-docx/scripts/mdlite.py").read_bytes()
    assert a == b, "keep make-pdf and make-docx mdlite.py in sync"


def test_parser_blocks_and_front_matter():
    meta, blocks = mdlite.parse(SAMPLE)
    assert meta == {"title": "Quarterly Review", "author": "Platform Team"}
    kinds = [b["type"] for b in blocks]
    assert kinds[:4] == ["heading", "paragraph", "list", "list"]
    bullets, ordered = blocks[2], blocks[3]
    assert bullets["tight"] and not bullets["ordered"]
    assert bullets["items"][2]["checked"] is True
    assert bullets["items"][1]["children"][1]["type"] == "list"
    assert ordered["ordered"] and ordered["start"] == 1
    table = next(b for b in blocks if b["type"] == "table")
    assert table["aligns"] == ["left", "right"]
    code = next(b for b in blocks if b["type"] == "code")
    assert code["lang"] == "python" and code["text"] == 'print("<b>")'


def test_inline_parsing():
    nodes = mdlite.parse_inline("a **b** *c* `d*e*` ~~f~~ [g](https://x.io/a_(b)) <https://y.io>")
    kinds = [n[0] for n in nodes if n[0] != "text"]
    assert kinds == ["strong", "em", "code", "del", "link", "link"]
    assert ("code", "d*e*") in nodes
    assert ("link", "https://x.io/a_(b)", [("text", "g")]) in nodes
    image = mdlite.parse_inline("![Alt](p.png){width=50%}")[0]
    assert image == ("image", "p.png", "Alt", {"width": "50%"})
    assert mdlite.parse_inline(r"\*not em\*") == [("text", "*not em*")]


def test_smarten_and_slugify():
    assert mdlite.smarten('He said "it\'s fine" -- ok...') == "He said “it’s fine” — ok…"
    seen: set[str] = set()
    assert mdlite.slugify("Hello, World!", seen) == "hello-world"
    assert mdlite.slugify("Hello World", seen) == "hello-world-2"


def test_setext_hr_pagebreak_and_quote():
    _, blocks = mdlite.parse("Title\n=====\n\n***\n\n<!-- pagebreak -->\n\n> a\n> b\n")
    assert [b["type"] for b in blocks] == ["heading", "hr", "pagebreak", "quote"]


# --- make-pdf (HTML stage needs no browser) ---


def test_pdf_html_is_safe_and_complete(doc, tmp_path, capsys):
    out = tmp_path / "doc.html"
    assert make_pdf.main([str(doc), str(out), "--to", "html", "--cover", "--toc"]) == 0
    html = out.read_text()
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html and "<script>" not in html
    assert "javascript:" not in html
    assert 'src="data:image/png;base64,' in html and 'style="width:50%"' in html
    assert "[image: Remote]" in html and "[image: Escape]" in html
    assert 'href="#metrics"' in html and 'id="metrics"' in html
    assert "“ship it”" in html and "—" in html
    assert 'class="cover-title">Quarterly Review' in html
    assert 'counter(page) " of " counter(pages)' in html
    err = capsys.readouterr().err
    assert "remote image blocked" in err and "outside the Markdown folder" in err


def test_pdf_title_cannot_break_out_of_style(tmp_path):
    # Regression: a hostile title in front matter or the first H1 must not close <style>.
    md = tmp_path / "evil.md"
    md.write_text('---\ntitle: "</style><script>alert(1)</script>"\n---\n# Hi\n')
    out = tmp_path / "evil.html"
    assert make_pdf.main([str(md), str(out), "--to", "html"]) == 0
    html = out.read_text()
    assert "<script>" not in html and html.count("</style>") == 1
    assert "\\3C /style\\3E " in html
    assert "script-src 'none'" in html and "Content-Security-Policy" in html


def test_pdf_csp_allows_remote_images_only_on_request():
    assert "http:" not in make_pdf.content_policy(False)
    assert "https:" in make_pdf.content_policy(True)


def test_pdf_strict_fails_on_blocked_image(doc, tmp_path):
    assert make_pdf.main([str(doc), str(tmp_path / "x.html"), "--to", "html", "--strict"]) == 3


def test_pdf_rejects_bad_margins_and_missing_input(tmp_path):
    with pytest.raises(SystemExit):
        make_pdf.main([str(tmp_path / "x.md"), "--margins", "1in; color:red"])
    assert make_pdf.main([str(tmp_path / "missing.md"), "--to", "html"]) == 2


def test_pdf_reports_missing_browser(doc, tmp_path, monkeypatch):
    monkeypatch.setattr(make_pdf, "find_browser", lambda explicit: None)
    assert make_pdf.main([str(doc), str(tmp_path / "x.pdf")]) == 4


BROWSER = make_pdf.find_browser(None)


@pytest.mark.skipif(not BROWSER, reason="no Chrome, Chromium, Edge or Brave installed")
def test_pdf_renders_with_browser(doc, tmp_path, monkeypatch):
    if sys.platform.startswith("linux"):
        monkeypatch.setenv("MAKE_PDF_CHROME_FLAGS", "--no-sandbox")
    out = tmp_path / "doc.pdf"
    code = make_pdf.main([str(doc), str(out), "--cover", "--toc", "--watermark", "DRAFT"])
    if code == 3 and os.environ.get("CI") is None:
        pytest.skip("browser could not print in this sandbox")
    assert code == 0
    data = out.read_bytes()
    assert data.startswith(b"%PDF-") and len(data) > 5000
    if shutil.which("pdftotext"):
        text = subprocess.run(["pdftotext", str(out), "-"], capture_output=True, text=True).stdout
        assert "Quarterly Review" in text and "Crash-free" in text


# --- make-docx ---


def test_docx_package_is_valid(doc, tmp_path):
    out = tmp_path / "doc.docx"
    args = [str(doc), str(out), "--cover", "--toc", "--watermark", "DRAFT", "--chapter-breaks"]
    assert make_docx.main(args) == 0
    with zipfile.ZipFile(out) as zf:
        names = set(zf.namelist())
        assert {"[Content_Types].xml", "word/document.xml", "word/styles.xml"} <= names
        assert "word/media/image1.png" in names
        for name in names:
            if name.endswith((".xml", ".rels")):
                ElementTree.fromstring(zf.read(name))  # well-formed
        body = zf.read("word/document.xml").decode()
        rels = zf.read("word/_rels/document.xml.rels").decode()
        styles = zf.read("word/styles.xml").decode()
        header = zf.read("word/header1.xml").decode()
    assert 'w:styleId="Heading1"' in styles and 'w:default="1" w:styleId="Normal"' in styles
    assert "Quarterly Review" in body and "“ship it”" in body
    assert "&lt;script&gt;" in body and "javascript" not in rels
    assert 'TargetMode="External"' in rels and "https://example.com" in rels
    assert 'w:anchor="_metrics"' in body and 'w:name="_metrics"' in body
    assert "<w:numId" in body and "<w:tbl>" in body and "<w:pageBreakBefore/>" in body
    assert "TOC \\o" in body and 'string="DRAFT"' in header


def test_docx_image_scaling_and_types():
    assert make_docx.image_size(png(40, 20)) == (40, 20)
    assert make_docx.image_size(b"GIF89a" + struct.pack("<HH", 7, 9)) == (7, 9)
    jpeg = b"\xff\xd8\xff\xc0\x00\x11\x08" + struct.pack(">HH", 30, 60) + b"\x03" + b"\x00" * 9
    assert make_docx.image_size(jpeg) == (60, 30)
    assert make_docx.image_size(b"<svg/>") is None
    assert make_docx.twips("1in") == 1440 and make_docx.twips("2.54cm") == 1440


def test_docx_strict_and_bad_args(doc, tmp_path):
    assert make_docx.main([str(doc), str(tmp_path / "x.docx"), "--strict"]) == 3
    assert make_docx.main([str(tmp_path / "missing.md")]) == 2
    with pytest.raises(SystemExit):
        make_docx.main([str(doc), "--font", "<evil/>"])


def test_docx_escapes_xml_and_control_characters():
    assert make_docx.x('a<b>&"c"\x07') == "a&lt;b&gt;&amp;&quot;c&quot;"


# --- android-qa ui_tree ---


def node(rid: str, cls: str, bounds: str, text: str = "", click: bool = False, close=True):
    attrs = (
        f'text="{text}" resource-id="{rid}" class="android.widget.{cls}" package="p" '
        f'content-desc="" clickable="{str(click).lower()}" enabled="true" bounds="{bounds}"'
    )
    return f"<node {attrs}{' /' if close else ''}>"


DUMP = (
    "<?xml version='1.0' encoding='UTF-8' standalone='yes' ?><hierarchy rotation=\"0\">"
    + node("", "FrameLayout", "[0,0][1080,2400]", close=False)
    + node("p:id/row", "LinearLayout", "[0,200][1080,400]", click=True, close=False)
    + node("p:id/title", "TextView", "[100,250][700,350]", text="Network &amp; internet")
    + "</node>"
    + node("p:id/fab", "ImageButton", "[900,2000][960,2060]", click=True)
    + "</node></hierarchy>"
)


def test_ui_tree_list_find_audit(tmp_path, capsys):
    path = tmp_path / "ui.xml"
    path.write_text("UI hierchary dumped to: /sdcard/x\n" + DUMP)
    assert ui_tree.main(["ui_tree", "list", str(path)]) == 0
    listing = capsys.readouterr().out
    assert '"Network & internet" #title TextView @ 400 300' in listing
    assert ui_tree.main(["ui_tree", "find", str(path), "Network & internet"]) == 0
    assert capsys.readouterr().out.strip() == "400 300"
    assert ui_tree.main(["ui_tree", "find", str(path), "fab"]) == 0
    assert capsys.readouterr().out.strip() == "930 2030"
    assert ui_tree.main(["ui_tree", "find", str(path), "nothing here"]) == 1
    capsys.readouterr()
    assert ui_tree.main(["ui_tree", "audit", str(path), "--density", "420"]) == 0
    audit = capsys.readouterr().out
    assert "unlabeled control" in audit and "#fab" in audit
    assert "small touch target (60x60px < 126px = 48dp)" in audit
    assert "#row" not in audit  # labeled through its child, large enough


def test_ui_tree_refuses_entities(tmp_path):
    path = tmp_path / "evil.xml"
    path.write_text('<?xml version="1.0"?><!DOCTYPE x [<!ENTITY a "b">]><hierarchy></hierarchy>')
    with pytest.raises(SystemExit):
        ui_tree.load(str(path))


# --- ios-qa ax_tree ---

AXE = [
    {
        "AXLabel": "Settings",
        "type": "Application",
        "frame": {"x": 0, "y": 0, "width": 402, "height": 874},
        "children": [
            {
                "AXLabel": "General",
                "AXUniqueId": "settings.general",
                "type": "Button",
                "frame": {"x": 16, "y": 300, "width": 370, "height": 52},
                "children": [],
            },
            {"AXLabel": None, "type": "Button", "AXFrame": "{{360, 60}, {30, 30}}", "children": []},
        ],
    }
]
MAESTRO = {
    "attributes": {"bounds": "[0,0][402,874]"},
    "children": [
        {
            "attributes": {
                "accessibilityText": "Sign in",
                "resource-id": "login",
                "bounds": "[20,700][382,750]",
                "clickable": "true",
            }
        }
    ],
}


def test_ax_tree_axe_format(tmp_path, capsys):
    path = tmp_path / "axe.json"
    path.write_text(json.dumps(AXE))
    assert ax_tree.main(["ax", "find", str(path), "settings.general"]) == 0
    assert capsys.readouterr().out.strip() == "201 326"
    assert ax_tree.main(["ax", "audit", str(path)]) == 0
    audit = capsys.readouterr().out
    assert "unlabeled control" in audit and "small touch target (30x30pt < 44pt)" in audit
    assert ax_tree.main(["ax", "find", str(path), "Wi-Fi"]) == 1


def test_ax_tree_maestro_format(tmp_path, capsys):
    path = tmp_path / "maestro.json"
    path.write_text("Running hierarchy...\n" + json.dumps(MAESTRO))
    assert ax_tree.main(["ax", "find", str(path), "sign in"]) == 0
    assert capsys.readouterr().out.strip() == "201 725"


# --- shell helpers ---


def run(script: Path, *args: str, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(["bash", str(script), *args], cwd=cwd, capture_output=True, text=True)


def test_qa_run_init_issue_and_tree_state(tmp_path):
    script = SKILLS / "qa/scripts/qa-run.sh"
    subprocess.run(["git", "init", "-q", "-b", "main", str(tmp_path)], check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.email=t@t",
            "-c",
            "user.name=t",
            "commit",
            "-q",
            "--allow-empty",
            "-m",
            "init",
        ],
        cwd=tmp_path,
        check=True,
    )
    result = run(script, "init", "Checkout Flow!", cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    lines = dict(line.split("=", 1) for line in result.stdout.splitlines() if "=" in line)
    run_dir = Path(lines["RUN_DIR"])
    assert run_dir.name.startswith("checkout-flow-") and (run_dir / "report.md").is_file()
    assert lines["TREE"] == "clean"
    assert (
        subprocess.run(
            ["git", "status", "--porcelain"], cwd=tmp_path, capture_output=True, text=True
        ).stdout
        == ""
    )  # run folder is excluded from git
    assert run(script, "issue", str(run_dir), cwd=tmp_path).stdout.strip() == "ISSUE-001"
    (run_dir / "report.md").write_text("ISSUE-007 found")
    assert run(script, "issue", str(run_dir), cwd=tmp_path).stdout.strip() == "ISSUE-008"
    assert run(script, "bogus", cwd=tmp_path).returncode == 2


@pytest.mark.parametrize(
    "script",
    ["qa/scripts/qa-run.sh", "android-qa/scripts/android-qa.sh", "ios-qa/scripts/ios-qa.sh"],
)
def test_shell_scripts_parse_and_are_executable(script):
    path = SKILLS / script
    assert path.stat().st_mode & 0o111
    assert subprocess.run(["bash", "-n", str(path)]).returncode == 0


def test_android_qa_help_needs_no_device(tmp_path):
    result = run(SKILLS / "android-qa/scripts/android-qa.sh", "help", cwd=tmp_path)
    assert result.returncode == 0 and "tap-text" in result.stdout
