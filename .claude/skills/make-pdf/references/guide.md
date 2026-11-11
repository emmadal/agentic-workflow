# make-pdf: detailed guide

Loaded on demand from SKILL.md.

## How it works
1. `mdlite.py` parses Markdown into blocks (no dependencies, raw HTML kept as text).
2. `make_pdf.py` renders one self-contained HTML page: print CSS, inlined images (data URIs), heading ids, optional cover, TOC and watermark.
3. Headless Chrome, Chromium, Edge or Brave prints it with `--print-to-pdf`, a throwaway profile, `--no-pdf-header-footer` and `--generate-pdf-document-outline` (PDF bookmarks). Page numbers and the running header come from CSS `@page` margin boxes (Chrome 131+).
4. When `pdftotext` (poppler) exists, the script counts extractable words as a copy-paste check.

## Layout recipes
| Want | Flags or Markdown |
|---|---|
| Memo, letter | none |
| Report with title page | `--cover --toc --author "Team"` |
| Draft for review | `--watermark DRAFT` (any short text: `CONFIDENTIAL`, `INTERNAL`) |
| European paper | `--page-size a4 --margins 2.5cm` |
| Dense handout | `--margins 0.75in --font sans --no-chapter-breaks` |
| No header or numbers | `--no-header --no-page-numbers` |
| Manual page break | a line with `<!-- pagebreak -->` |
| Wide figure | `![Architecture](arch.png){width=full}` |
| Share as web page | `--to html` (single file, images inlined) |

Title order: `--title`, then front matter `title`, then the first H1. With `--cover` and no explicit title, the first H1 moves to the cover so it is not printed twice.

## Writing Markdown that prints well
- One H1 per chapter; H2 and H3 inside. The TOC uses H1-H2 when there are several H1s, else H2-H3.
- Tables: keep to about 6 columns; long cell text wraps. Right-align numbers with `--:` in the delimiter row.
- Code blocks wrap long lines instead of overflowing; keep them under ~60 lines so they do not split across pages awkwardly.
- Images: use PNG or SVG at 2x the printed size; give every image alt text.
- Diagrams: render Mermaid or other diagram sources to SVG or PNG first, then reference the image.

## Verify the output
```bash
pdfinfo out.pdf | grep -E 'Pages|Tagged|Page size'   # poppler
pdftotext -layout out.pdf - | head -60                # text order and copy-paste quality
pdftoppm -r 50 -png out.pdf page                       # look at page-1.png, a table page, last page
```
Look for: cover alone on page 1, no orphaned headings at page bottoms, tables not cut mid-row, images inside margins, page numbers on body pages.

## Environment notes
- Browser lookup order: `--chrome`, `CHROME_PATH`, standard macOS and Windows install paths, then `google-chrome`, `chromium`, `chromium-browser`, `microsoft-edge`, `msedge`, `brave-browser` on `PATH`.
- Containers often need `MAKE_PDF_CHROME_FLAGS=--no-sandbox` (root user is detected automatically). Use it only for Markdown you trust.
- Linux fonts: `fonts-liberation` (Helvetica and Arial metrics), `fonts-noto-color-emoji`, a CJK font such as `fonts-noto-cjk` when needed.
- `--blink-settings=scriptEnabled=false` breaks headless printing in current Chrome; the generated HTML contains no scripts, so it is not needed.

## Limits
No syntax highlighting, footnotes, math or TOC page numbers (the TOC is clickable; PDF bookmarks carry the structure). For those, use pandoc with a LaTeX or Typst engine if the machine has it.
