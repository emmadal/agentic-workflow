---
name: make-pdf
description: "Use when asked to make, export or print a PDF from Markdown or notes: report, spec, memo, proposal, handout. Cover, clickable TOC, page numbers, running header, DRAFT watermark, offline images."
---
# make-pdf

Markdown in, finished PDF out: 1in margins, real page breaks, "N of M" page numbers, running title header, curly quotes and em dashes, tagged PDF with bookmarks, text that copies cleanly. Script: `scripts/make_pdf.py` (Python 3.9+, no packages; prints through Chrome, Chromium, Edge or Brave in headless mode).

## Steps
1. Find or write the Markdown. When the user gives notes, structure them first: one H1 title, H2 sections, short paragraphs, tables for comparisons. Show the outline if the content is long.
2. Pick options from intent; ask only when unclear (memo vs. publication):
   - memo or letter: no flags
   - report, proposal, spec: `--cover --toc`
   - review copy: `--watermark DRAFT`
   - A4 regions: `--page-size a4`
3. Run: `python3 scripts/make_pdf.py doc.md out.pdf --cover --toc --author "Name"`. Stdout is the output path; warnings go to stderr.
4. Check the result before handing it over: open it or rasterize pages (`pdftoppm -r 50 -png out.pdf page`) and look at the cover, a table page and the last page. With `pdftotext` installed the script reports extractable words; a count far below the source means broken text.
5. Report the path, page count and any warnings (blocked or missing images).

## Markdown features
Front matter `title`, `subtitle`, `author`, `date`. Tables, task lists, code blocks, quotes, footnote-free links, `<!-- pagebreak -->`. Images: `![Chart](chart.png){width=60%}` or `{width=full}`; local files inline. Each H1 starts a new page (`--no-chapter-breaks` to stop). All flags: `python3 scripts/make_pdf.py -h`.

## Safety
- Offline by default: remote images become a visible placeholder and the browser runs behind a dead proxy; `--allow-network` fetches them.
- Images outside the Markdown's folder are refused. Raw HTML is printed as text, `javascript:` links become plain text.
- `--strict` turns every missing or blocked image into a failure (CI).

## Exit codes
0 done · 2 bad arguments or missing input · 3 render or asset error · 4 no browser (install Chrome or Chromium, set `CHROME_PATH`, or use `--to html` for a self-contained HTML file).

## Troubleshooting
Browser exits without a PDF inside a container: set `MAKE_PDF_CHROME_FLAGS=--no-sandbox` only for trusted input. Wrong fonts on Linux: install `fonts-liberation` and `fonts-noto-color-emoji`. Word output instead: the `make-docx` skill. Depth and layout recipes: `references/guide.md`.
