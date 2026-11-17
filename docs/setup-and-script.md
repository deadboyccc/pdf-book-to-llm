# Setup and script reference

Companion to the [README](../README.md): installing book2md, the uv environment, and
a walkthrough of `book2md.py`.

- [Install uv](#install-uv)
- [Install book2md](#install-book2md)
- [The script](#the-script)
- [Pipeline options](#pipeline-options)
- [Housekeeping](#housekeeping)

## Install uv

uv manages Python and the environment; no `sudo` is needed. Works on macOS, Windows and glibc-based Linux; Alpine and other musl distributions are not supported because PyTorch publishes no wheels for them.

```bash
brew install uv                                   # macOS
curl -LsSf https://astral.sh/uv/install.sh | sh   # macOS / Linux
```

```powershell
# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## Install book2md

Pick one:

```bash
# 1. as a command on your PATH (recommended)
uv tool install git+https://github.com/deadboyccc/pdf-book-to-llm

# 2. from a clone, to read or change the code
git clone https://github.com/deadboyccc/pdf-book-to-llm && cd pdf-book-to-llm
uv sync
uv run book2md --help

# 3. from a release wheel
uv tool install ./book2md-1.0.0-py3-none-any.whl
```

| Command | Effect |
|---------|--------|
| `uv tool install …` | Installs `book2md` in its own isolated environment and puts the command on your `PATH` |
| `uv sync` | Creates `.venv/` and installs the exact versions pinned in `uv.lock` |
| `uv run <cmd>` | Runs `<cmd>` inside `.venv/`; no activation needed |
| `uv sync --only-group dev` | Installs only the test and lint tools (no Docling) — enough for the unit tests |

The first conversion downloads Docling's model weights (one-time, about 1 GB).
An available GPU (Apple MPS, CUDA) is used automatically; otherwise it runs on CPU.
`uv run python book2md.py …` also works from a clone.

## The script

`book2md.py` is a single module. In the order a run goes through it:

| Part | What it does |
|------|--------------|
| `build_parser()` | Defines the options (see the [README](../README.md#options)). `--pages` goes through `parse_pages()`; `--scale` must be greater than 0. Bad values are usage errors (exit 2) |
| `parse_pages()` | Turns `150-210` or `150` into `(start, end)`; raises `ValueError` on bad input |
| `output_dir()` | `<out>/<pdf name>[_pS-E]/pages/`, so a page-range run never overwrites a full conversion |
| `convert_pdf()` | Imports Docling — only now, so `--help` stays instant — applies the [pipeline options](#pipeline-options), and converts only the requested pages; page numbers stay those of the original PDF. Docling's `ConversionError` becomes `ConversionFailed` |
| `write_pages()` | For each page `n`: export that page to Markdown, write `pNNNN.md` with a `<!-- PAGE n -->` marker, save the page image as `pNNNN.png`. Creates the output folder only now, so a failed run leaves nothing behind |
| `ImageRefMode.PLACEHOLDER` | Figures become `<!-- image -->`; the PNG is the visual source |
| `page_stem()` | Zero-padded names (`p0007`) so files sort in page order |
| `main()` | Ties it together and returns the exit code: `0` all pages written, `1` failure or missing pages (listed with Docling's messages), `2` from argparse for bad arguments |

### Pipeline options

| Option | Value | Meaning |
|--------|-------|---------|
| `do_ocr` | `--ocr` | OCR on or off |
| `do_table_structure` | `True` | Rebuild tables as Markdown tables |
| `do_code_enrichment` | `True` | Better code-block detection and formatting |
| `do_formula_enrichment` | `--formulas` | Math to LaTeX |
| `generate_page_images` | `True` | Required for the per-page PNGs |
| `images_scale` | `--scale` | Resolution of those PNGs: pixels per PDF point (A4 at `1.5` is 893 px wide) |

## Housekeeping

- Keep PDFs and output out of git (copyrighted, large) and out of cloud-synced folders;
  `.venv` holds tens of thousands of small files that sync poorly.
- `.venv/` is disposable. The PDFs are only read, never modified.

| Task | Command |
|------|---------|
| Rebuild the environment | `rm -rf .venv && uv sync` |
| Update Docling | `uv lock --upgrade-package docling && uv sync` |
| Update the installed command | `uv tool upgrade book2md` |
| Run the unit tests | `uv sync --only-group dev && uv run pytest tests/unit` |
| Run the end-to-end tests | `uv sync && uv run pytest tests/e2e` |
