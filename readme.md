# book2md

Convert a PDF book into **one Markdown file and one PNG per page**, so you can hand exact pages (text, code, tables, diagrams) to an LLM chat and ask questions about them.

Built on [Docling](https://github.com/docling-project/docling), run locally with [uv](https://docs.astral.sh/uv/). Nothing is uploaded anywhere.

```
book.pdf ──▶ Docling (layout + tables + code) ──▶ pages/p0001.md + p0001.png
                                                  pages/p0002.md + p0002.png
                                                  ...
```

## Why this shape

| File | Contains | Why |
|------|----------|-----|
| `pNNNN.md` | Text, headings, tables, code blocks | What the LLM reads |
| `pNNNN.png` | Render of the full page | Diagrams can't be reliably turned into text; attach the image |

Same filename stem, so pairs are easy to find. Figures appear in the `.md` as `<!-- image -->`.

## Setup

Requires macOS with [Homebrew](https://brew.sh). Everything stays under your home directory; no `sudo`.

```bash
brew install uv

mkdir -p ~/dev ~/study/books-pdf ~/study/corpus
cd ~/dev
uv init study-tools
cd study-tools
uv add docling
```

Save `book2md.py` into `~/dev/study-tools/` (delete the starter `main.py`).

### What each step does

| Command | Effect |
|---------|--------|
| `brew install uv` | Installs uv, a fast replacement for pip + venv |
| `mkdir -p ...` | `~/dev/study-tools` = code and environment. `~/study/books-pdf` = your PDFs (only read). `~/study/corpus` = output |
| `uv init study-tools` | Creates project files only: `pyproject.toml`, `.python-version`, `main.py`, `README.md`, `.gitignore`, and a git repo. **Does not create the venv** |
| `uv add docling` | Creates `.venv/`, installs Docling into it, records it in `pyproject.toml` and pins exact versions in `uv.lock` |

No activation needed: `uv run` finds `.venv` and runs inside it.

First run downloads Docling's model weights (normal, one-time). Docling uses the Apple GPU (MPS) automatically when available.

### Folder layout

```
~/dev/study-tools/        uv project (code + disposable .venv)
~/study/books-pdf/        original PDFs (read-only in practice)
~/study/corpus/<book>/pages/   output
```

Keep `~/study/` out of git and out of iCloud/Dropbox: the books are copyrighted and the files are large. Keep the project out of `~/Desktop` and `~/Documents` if those are iCloud-synced; `.venv` has tens of thousands of small files.

## Usage

```bash
cd ~/dev/study-tools

# test on a few pages first
uv run python book2md.py ~/study/books-pdf/Book.pdf --pages 1-20

# one chapter
uv run python book2md.py ~/study/books-pdf/Book.pdf --pages 150-210

# whole book, Mac kept awake
caffeinate -i uv run python book2md.py ~/study/books-pdf/Book.pdf
```

### Options

| Option | Default | Meaning |
|--------|---------|---------|
| `pdf` | required | Path to the PDF (`~` is expanded) |
| `--pages S-E` | all | Convert only pages S to E, 1-based and inclusive. `--pages 120` = one page. Output goes to `<book>_pS-E/` so a test run never overwrites a full conversion |
| `--ocr` | off | Run OCR. Only for scanned books; much slower. Digital PDFs already have text |
| `--formulas` | off | Recognise math and emit LaTeX. Off by default (slow, little math in software books) |
| `--scale X` | `1.5` | Page image scale. `2.0` is sharper and larger |

Page numbers are **PDF page numbers** (counted from the first page of the file), not the numbers printed on the pages. If chapter 1 starts on PDF page 25, use 25.

## Output

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

## The script, piece by piece

| Part | What it does |
|------|--------------|
| `CORPUS_ROOT` | Output root, `~/study/corpus` |
| `parse_pages()` | Turns `150-210` or `150` into `(start, end)`; exits on bad input |
| `argparse` block | Defines the CLI options above |
| Output path | `<CORPUS_ROOT>/<pdf name>[_pS-E]/pages/`, created if missing |
| `PdfPipelineOptions` | Docling settings (below) |
| `DocumentConverter(...)` | Builds the converter with those settings for PDF input |
| `converter.convert(..., page_range=(start, end))` | Runs the conversion, restricted to the page range |
| Page loop | For each page `n`: export that page to Markdown, write `pNNNN.md`, save the page image as `pNNNN.png` |
| `ImageRefMode.PLACEHOLDER` | Figures become `<!-- image -->` instead of embedded or linked files; the PNG is the visual source |
| `{n:04d}` | Zero-padded numbers (`p0007`) so files sort correctly |

### Pipeline options

| Setting | Value | Meaning |
|---------|-------|---------|
| `do_ocr` | `--ocr` | OCR on/off |
| `do_table_structure` | `True` | Rebuild tables as real Markdown tables (Docling's strength) |
| `do_code_enrichment` | `True` | Better detection and formatting of code blocks |
| `do_formula_enrichment` | `--formulas` | Math to LaTeX |
| `generate_page_images` | `True` | Required to get the per-page PNGs |
| `images_scale` | `--scale` | Resolution of those PNGs |

## Using the output with an LLM

- **A few pages:** upload `p0163.md` and `p0163.png` together.
- **A chapter:** join a page range into one file, markers are preserved:
  ```bash
  cd ~/study/corpus/Book/pages
  for n in $(seq 150 209); do cat "p$(printf %04d $n).md"; done > ../pages-150-209.md
  ```
- **Find pages by term:** `grep -l "replication lag" *.md`
- **Diagram questions:** always attach the page PNG; the Markdown only has a placeholder.
- Ask with page references: "Explain the example on page 163."

## Maintenance

| Task | Command |
|------|---------|
| Rebuild environment | `rm -rf .venv && uv sync` |
| Update Docling | `uv add --upgrade docling` |
| Big book, memory pressure | Convert in 100-page chunks with `--pages` |
| Garbled or empty text | PDF is probably scanned; retry with `--ocr` |

## Caveats

- Not benchmarked on every setup. Run the `--pages 1-20` test first and check that file numbers match your PDF viewer's page counter.
- Spot-check a few code blocks and tables against the PDF for each new book; headers and footers occasionally leak into the text.
- Conversion time depends on book size and whether OCR is on. Time your first book and use it as a baseline.
