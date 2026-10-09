# Setup and script reference

Companion to the [README](readme.md): the uv environment setup and a walkthrough of `book2md.py`.

## Setup

Works on macOS, Linux, and Windows. uv manages Python and the environment; no `sudo` needed.

```bash
# install uv (once)
brew install uv                                   # macOS
curl -LsSf https://astral.sh/uv/install.sh | sh   # macOS / Linux
# Windows: powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# new project
uv init book2md && cd book2md
uv add docling
# put book2md.py in this folder; delete the starter main.py

# or, from an existing clone
uv sync
```

| Command | Effect |
|---------|--------|
| `uv init book2md` | Creates project files only (`pyproject.toml`, `.python-version`, `main.py`, `README.md`, `.gitignore`, git repo). **No venv yet** |
| `uv add docling` | Creates `.venv/`, installs Docling, records it in `pyproject.toml`, pins exact versions in `uv.lock` |
| `uv sync` | Creates `.venv/` and installs from `uv.lock` |
| `uv run <cmd>` | Runs `<cmd>` inside `.venv/`; no activation needed |

The first run downloads Docling's model weights (one-time). An available GPU (Apple MPS, CUDA) is used automatically; otherwise it runs on CPU.

## The script

`book2md.py`, section by section:

| Part | What it does |
|------|--------------|
| `CORPUS_ROOT` | Output root |
| `parse_pages()` | Turns `150-210` or `150` into `(start, end)`; exits on bad input |
| `argparse` block | Defines the CLI options (see the [README](../README.md#usage)) |
| Output path | `CORPUS_ROOT/<pdf name>[_pS-E]/pages/`, created if missing |
| `PdfPipelineOptions` | Docling settings (below) |
| `DocumentConverter(...)` | Builds the converter with those settings for PDF input |
| `converter.convert(..., page_range=(start, end))` | Converts only the requested pages; page numbers stay those of the original PDF |
| Page loop | For each page `n`: export that page to Markdown, write `pNNNN.md`, save the page image as `pNNNN.png` |
| `ImageRefMode.PLACEHOLDER` | Figures become `<!-- image -->`; the PNG is the visual source |
| `{n:04d}` | Zero-padded numbers (`p0007`) so files sort correctly |

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
| Update Docling | `uv add --upgrade docling` |
