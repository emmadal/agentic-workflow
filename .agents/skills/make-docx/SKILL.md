---
name: make-docx
description: "Use when asked for a Word document or .docx from Markdown or notes: report, proposal, spec, letter or handout to edit in Word or Google Docs. Real headings, lists, tables, images, TOC, page numbers."
---
# make-docx

Markdown in, native Word document out, ready for people to edit: styles they can change (Title, Heading 1-6, List Paragraph, Quote, Code Block), real numbered and bulleted lists, tables with repeating header rows, embedded images, internal links to headings, a TOC field, "Page N of M" footer. Script: `scripts/make_docx.py` (Python 3.9+, standard library only, no Word needed).

## Steps
1. Find or write the Markdown. For notes, structure first: one H1 title, H2 sections, tables for comparisons, numbered lists for steps.
2. Pick options from intent:
   - letter or memo: no flags
   - report or proposal: `--cover --toc`
   - review copy: `--watermark DRAFT`
   - one chapter per page: `--chapter-breaks`
   - A4 or house font: `--page-size a4 --font "Aptos"`
3. Run: `python3 scripts/make_docx.py doc.md out.docx --cover --toc --author "Name"`. Stdout is the path; warnings go to stderr.
4. Check before handing over: on macOS `textutil -convert txt -stdout out.docx | head -40`; elsewhere `unzip -l out.docx` and read `word/document.xml` for the expected headings. Say what you checked.
5. Report the path and warnings. Tell the user Word fills TOC page numbers when it asks to update fields on open; other editors show the TOC as links.

## Markdown features
Front matter `title`, `subtitle`, `author`, `date`. Tables with alignment, task lists, nested lists, code blocks, quotes, links, `<!-- pagebreak -->`. Images: PNG, JPEG, GIF, local only, `{width=50%}` or `{width=full}`; convert SVG or WebP to PNG first. All flags: `python3 scripts/make_docx.py -h`.

## Safety
Images outside the Markdown's folder and remote images are not embedded (placeholder plus warning; `--strict` fails instead). Raw HTML is kept as text. Only http, https and mailto links become hyperlinks.

## Exit codes
0 done · 2 bad arguments or missing input · 3 render or asset error.

## Limits
Layout is Word's, not print-perfect: for a fixed-layout deliverable use `make-pdf`. No syntax highlighting, footnotes or math. Style reference, edits after generation and pandoc fallback: `references/guide.md`.
