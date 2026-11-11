# make-docx: detailed guide

Loaded on demand from SKILL.md.

## What the document contains
| Markdown | Word |
|---|---|
| front matter `title`, `subtitle`, `author`, `date` | cover page (`--cover`), document properties |
| `#` to `######` | Heading 1-6 (navigation pane, TOC levels, bookmarks for `#links`) |
| paragraphs, `**bold**`, `*italic*`, `~~strike~~`, `` `code` `` | Normal runs, Inline Code character style |
| `- item`, `1. item`, nested lists, `- [x] task` | real Word numbering (bullets, 1. a. i.), checkbox glyphs |
| fenced or indented code | Code Block paragraphs (Consolas, shaded, spaces and tabs kept) |
| `> quote` | Quote style with a left rule |
| pipe tables with `:--:` alignment | Table Grid, bold shaded header row that repeats on each page |
| `![alt](img.png){width=50%}` | embedded picture scaled to the text width, alt text kept |
| `[text](https://...)`, `<https://...>`, bare URLs | hyperlinks; `[text](#heading)` jumps inside the document |
| `---` | horizontal rule (bottom border) |
| `<!-- pagebreak -->` | page break |

Footer: "Page N of M" fields. Header: document title (`--no-header` to remove), plus the watermark when requested. Cover pages use a different first-page header and footer, so the cover stays clean.

## Table of contents
`--toc` inserts a real Word TOC field whose cached result is a list of links to every heading. Word asks to update fields on open and then adds page numbers; Google Docs, Pages and LibreOffice show the cached links.

## Styling after generation
Everything uses named styles, so restyling is fast in Word: Home, Styles pane, modify Normal (font), Heading 1-3 (colors), Code Block, Quote. `--font "Aptos"` changes the body and heading font at generation time; use a font readers have installed.

## Checks
```bash
textutil -convert txt -stdout out.docx | head -40     # macOS: readable text in reading order
unzip -l out.docx                                       # parts: word/document.xml, styles, media
unzip -p out.docx word/document.xml | head -c 2000      # spot-check structure
```
With python-docx available: `python -c "import docx; d=docx.Document('out.docx'); print([p.style.name for p in d.paragraphs][:20])"`.

## When to use pandoc instead
If `pandoc` is installed and the user needs footnotes, citations, math or a corporate template: `pandoc doc.md -o out.docx --reference-doc=template.docx --toc`. The built-in script stays the default because it needs nothing but Python.

## Limits
- Images: local PNG, JPEG and GIF only. Convert SVG and WebP to PNG (`sips -s format png in.svg --out out.png` on macOS, `rsvg-convert` or Inkscape elsewhere).
- No syntax highlighting, footnotes, math, or merged table cells.
- The watermark is a VML text shape in the header, the same mechanism Word's own Watermark menu uses.
