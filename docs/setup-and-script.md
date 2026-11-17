# Setup and script reference

Companion to the [README](../README.md): the uv environment setup and a walkthrough of `book2md.py`.

## Setup

Works on macOS, Linux, and Windows. uv manages Python and the environment; no `sudo` needed.

```bash
# install uv (once)
brew install uv                                   # macOS
curl -LsSf https://astral.sh/uv/install.sh | sh   # macOS / Linux
# Windows: powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# option 1: install the book2md command for your user
uv tool install git+https://github.com/deadboyccc/pdf-book-to-llm

# option 2: from a clone
git clone https://github.com/deadboyccc/pdf-book-to-llm && cd pdf-book-to-llm
uv sync
uv run book2md --help
```

| Command | Effect |
|---------|--------|
| `uv tool install git+…` | Installs `book2md` and its own isolated environment; the command is on your `PATH` |
| `uv sync` | Creates `.venv/` and installs the exact versions pinned in `uv.lock` |
| `uv run <cmd>` | Runs `<cmd>` inside `.venv/`; no activation needed |
| `uv sync --only-group dev` | Installs only the test and lint tools (no Docling) — enough for the unit tests |

The first run downloads Docling's model weights (one-time). An available GPU (Apple MPS, CUDA) is used automatically; otherwise it runs on CPU.

## The script

`book2md.py`, section by section:

| Part | What it does |
|------|--------------|
| `parse_pages()` | Turns `150-210` or `150` into `(start, end)`; raises `ValueError` on bad input, which argparse reports as a usage error (exit 2) |
| `build_parser()` | Defines the CLI options (see the [README](../README.md#usage)); `--scale` must be greater than 0 |
| `output_dir()` | `<out>/<pdf name>[_pS-E]/pages/`, so a page-range run never overwrites a full conversion |
| `convert_pdf()` | Imports Docling (only now, so `--help` stays fast), applies the pipeline options below, and converts only the requested pages; page numbers stay those of the original PDF. Docling's `ConversionError` becomes `ConversionFailed` |
| `write_pages()` | For each page `n`: export that page to Markdown, write `pNNNN.md` with a `<!-- PAGE n -->` marker, save the page image as `pNNNN.png`. Creates the output folder only now, so a failed run leaves nothing behind |
| `ImageRefMode.PLACEHOLDER` | Figures become `<!-- image -->`; the PNG is the visual source |
| `page_stem()` | Zero-padded numbers (`p0007`) so files sort correctly |
| `main()` | Ties it together and returns the exit code: lists pages Docling could not convert and returns 1 in that case |

### Pipeline options

| Option | Value | Meaning |
|--------|-------|---------|
| `do_ocr` | `--ocr` | OCR on/off |
| `do_table_structure` | `True` | Rebuild tables as Markdown tables |
| `do_code_enrichment` | `True` | Better code-block detection and formatting |
| `do_formula_enrichment` | `--formulas` | Math to LaTeX |
| `generate_page_images` | `True` | Required for the per-page PNGs |
| `images_scale` | `--scale` | Resolution of those PNGs |

## Housekeeping

- Keep PDFs and output out of git (copyrighted, large) and out of cloud-synced folders; `.venv` holds tens of thousands of small files that sync poorly.
- `.venv/` is disposable. The PDFs are only read, never modified.

| Task | Command |
|------|---------|
| Rebuild environment | `rm -rf .venv && uv sync` |
| Update Docling | `uv lock --upgrade-package docling && uv sync` |
| Run the unit tests | `uv sync --only-group dev && uv run pytest tests/unit` |
