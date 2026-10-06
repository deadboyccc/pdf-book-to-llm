# book2md

Convert a PDF book into **one Markdown file and one PNG per page**, so you can give an LLM exact pages (text, code, tables, diagrams) and ask questions about them.

Built on [Docling](https://github.com/docling-project/docling) and [uv](https://docs.astral.sh/uv/). Runs locally; nothing is uploaded.

```
book.pdf ──▶ Docling ──▶ pages/p0001.md + p0001.png
                         pages/p0002.md + p0002.png
                         ...
```

| File | Contents | Purpose |
|------|----------|---------|
| `pNNNN.md` | Text, headings, tables, code blocks | What the LLM reads |
| `pNNNN.png` | Render of the full page | Diagrams can't be reliably converted to text; attach the image |

Same filename stem for each pair. Figures appear in the `.md` as `<!-- image -->`.

## Setup

Works on macOS, Linux, and Windows. Install uv, add Docling, and place `book2md.py` in the project. Full steps, with what each command does, are in **[docs/setup-and-script.md](docs/setup-and-script.md)**, along with a walkthrough of the script.

## Usage

```bash
# test on a few pages first
uv run python book2md.py books/Book.pdf --pages 1-20

# one chapter
uv run python book2md.py books/Book.pdf --pages 150-210

# whole book (caffeinate keeps a Mac awake; omit elsewhere)
caffeinate -i uv run python book2md.py books/Book.pdf
```

| Option | Default | Meaning |
|--------|---------|---------|
| `pdf` | required | Path to the PDF (`~` expanded) |
| `--pages S-E` | all | Pages S to E, 1-based, inclusive. `--pages 120` = one page. Output goes to `<book>_pS-E/`, so a test run never overwrites a full conversion |
| `--ocr` | off | Run OCR. Only for scanned books; much slower. Digital PDFs already contain text |
| `--formulas` | off | Recognise math, emit LaTeX. Slow; enable for math-heavy books |
| `--scale X` | `1.5` | Page image scale. `2.0` = sharper, larger |

Page numbers are **PDF page numbers** (counted from the first page of the file), not the numbers printed on the pages. If chapter 1 starts on PDF page 25, use 25.

## Output

Written to `CORPUS_ROOT/<book>[_pS-E]/pages/`. `CORPUS_ROOT` defaults to `~/study/corpus`; edit it in the script to change.

```
~/study/corpus/Book/pages/
├── p0001.md   p0001.png
├── p0002.md   p0002.png
└── p0163.md   p0163.png
```

Each `.md` starts with a page marker, then that page's content:

````markdown
<!-- PAGE 163 -->
## Problems with Replication Lag

| Guarantee        | Prevents                 |
|------------------|--------------------------|
| Read-after-write | Reading stale own writes |

```java
leader.append(k, v);
```

<!-- image -->
````

## Using the output with an LLM

- **A few pages:** upload `p0163.md` and `p0163.png` together.
- **A chapter:** join a page range into one file (bash); markers are preserved:
  ```bash
  cd corpus/Book/pages
  for n in $(seq 150 209); do cat "p$(printf %04d $n).md"; done > ../pages-150-209.md
  ```
- **Find pages by term:** `grep -l "replication lag" *.md`
- **Diagram questions:** attach the page PNG; the Markdown only has a placeholder.
- Ask with page references: "Explain the example on page 163."

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Memory pressure on a large book | Convert in ~100-page chunks with `--pages` |
| Garbled or empty text | PDF is probably scanned; retry with `--ocr` |

Environment tasks (rebuilding the venv, updating Docling) are in [docs/setup-and-script.md](setup-and-script.md).

## Caveats

- Page selection, numbering, file naming, image saving, and error handling were tested; Docling's layout, table, and code models were not exercised in that testing. Run `--pages 1-20` on a real book and compare against the PDF.
- Spot-check code blocks and tables for each new book; page headers and footers occasionally leak into the text.
- Conversion time depends on book size, hardware, and whether OCR is on. Time your first book as a baseline.
