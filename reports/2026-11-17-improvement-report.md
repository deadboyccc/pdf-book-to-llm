# Report: Making book2md Installable, Robust and Verified

**Date:** 2026-11-17 · **Final release:** [v1.0.0](https://github.com/deadboyccc/pdf-book-to-llm/releases/tag/v1.0.0)

## Summary

book2md started as a single script with no packaging, no tests and two broken
documentation links; its own README said Docling's models had never been
exercised. It is now an installable command with a lockfile, clear error
handling, a unit suite on three operating systems, end-to-end tests that run the
real Docling models on every push, a mascot, a pipeline picture and rewritten docs.
Each milestone was validated in a memory-capped sandbox, pushed to `main` and
released.

| | Before | After |
|---|---|---|
| Install | Copy the script into a hand-made uv project | `uv tool install git+https://github.com/deadboyccc/pdf-book-to-llm` |
| Reproducible environment | `uv sync` documented but impossible (no `pyproject.toml`) | `pyproject.toml` + `uv.lock` |
| Unit tests | 0 | 48, 99% line coverage, Linux / macOS / Windows, Python 3.10–3.13 |
| Real-model tests | none ("not exercised") | 10 end-to-end tests with real Docling models, every push |
| CI | none | Lint, lockfile, unit matrix, package build, end-to-end |
| Releases | none | v0.2.0, v0.3.0, v1.0.0 (wheel, sdist, checksums) |

## Milestones

| Release | Theme | Delivered |
|---|---|---|
| [v0.2.0](https://github.com/deadboyccc/pdf-book-to-llm/releases/tag/v0.2.0) | Reproducible and robust | Packaging and lockfile, `book2md` command, `--out`, `--version`, exit codes, bug fixes, unit tests, CI |
| [v0.3.0](https://github.com/deadboyccc/pdf-book-to-llm/releases/tag/v0.3.0) | Verified on real Docling | End-to-end tests on a generated sample book with the real models; converted pages uploaded per commit |
| [v1.0.0](https://github.com/deadboyccc/pdf-book-to-llm/releases/tag/v1.0.0) | Presentation | Folio the bookworm, pipeline picture, rewritten README and setup guide, CONTRIBUTING, this report |

## Bugs fixed

- **Start page past the end of the book**: printed a Docling traceback and left an empty output folder.
- **File that isn't a PDF**: same traceback and empty folder. Both cases now print one error line, exit 1, and write nothing.
- **Partial conversion**: silently wrote fewer pages and said "Done". The missing pages are now listed with Docling's errors, and the exit code is 1.
- **`--scale 0` or a negative scale**: accepted, then failed deep inside Docling. Now it is a usage error.
- **Changing the output folder**: required editing the script, which is impossible once installed. There is now `--out`.
- **Broken documentation links** in both documents, and a setup guide whose `uv sync` could not work.
- **`--help` was slow**: it waited seconds for Docling to import. Docling now loads only when converting.
- **CI on the first push**: `astral-sh/setup-uv` has no floating `@v10` tag, so every job failed during set-up. It is now pinned to `v10.3.3`.

## What the real-model tests showed

The sample book in CI has headed prose, a bordered table, a code listing and a figure.
Docling 2.150 converts it correctly:

- headings come out as `##`;
- the table is a Markdown table with every row;
- the listing is fenced as code;
- the figure becomes `<!-- image -->`, and its caption is kept.

One quirk is now documented: code indentation can come back as **tabs**, with no language tag on the fence.

## How it was verified

1. **Unit tests** replace Docling with fakes at its boundary, so they run in seconds on any OS. They also check the exact pipeline options passed to Docling.
2. **End-to-end tests** run the installed `book2md` command as a separate process, with the real models, on Linux CI. Converted pages are uploaded as an artifact; the v0.3.0 output was downloaded and inspected by hand.
3. **Fresh-clone sandbox**: before every push, a fresh clone ran the lockfile check, ruff, unit tests and package build in a memory-capped container, plus an install of the wheel and a run of the command.
4. **Heavy changes** (the real-model job) went green on a `milestone-*` branch before `main` was fast-forwarded.
5. **Mascot and picture** were rendered to PNG and checked visually before use.

## Key decisions

Full list in [`docs/ASSUMPTIONS.md`](../docs/ASSUMPTIONS.md). The main ones:

- **A partial conversion exits 1**, but keeps the pages that did convert.
- **The output folder is created only after Docling succeeds.**
- **torch stays on the regular PyPI build**, so Linux users with an NVIDIA GPU keep CUDA.
- **No single-file binary.** For a Python tool that loads torch and model weights, the wheel plus `uv tool install` is the right distribution.
- **Documentation examples are real CI output**, including the tabs.

## Suggested repository name and description

The command, the package and the README are all called **book2md**, but the repository is
`pdf-book-to-llm`, which is easy to misremember. `book2md` is free on GitHub (under this
account) and on PyPI. Reasons, alternatives and the follow-up steps after renaming are in
[the naming report](2026-11-17-repo-name-and-description.md).

**Repository name**

```text
book2md
```

**Description** (GitHub *About* box, 192 characters)

```text
Turn a PDF book into one Markdown file + one PNG per page, so you can give an LLM the exact pages you're asking about. Tables and code as Markdown, diagrams as images. Runs locally on Docling.
```

**Topics**

```text
pdf markdown llm docling pdf-to-markdown document-conversion rag ocr books cli python uv
```

**Apply all three** (GitHub CLI)

```bash
gh repo rename book2md --repo deadboyccc/pdf-book-to-llm --yes
gh repo edit deadboyccc/book2md \
  --description "Turn a PDF book into one Markdown file + one PNG per page, so you can give an LLM the exact pages you're asking about. Tables and code as Markdown, diagrams as images. Runs locally on Docling." \
  --add-topic pdf,markdown,llm,docling,pdf-to-markdown,document-conversion,rag,ocr,books,cli,python,uv
```

## Caveats

- **The real-model tests run on Linux only.** The unit tests cover macOS and Windows; real conversions there were not exercised.
- **The sample book is clean and digital.** Scanned books (`--ocr`) and formula recognition (`--formulas`) are wired and unit-tested, but were not run against real models in CI: they need extra model downloads and are slow.
- **No local real-model runs.** This server lacks the disk for torch and the models (about 1 GB of weights, plus several GB of wheels), so those runs happen only in CI.
- **Pull requests:** the access token used could not open them. Milestone branches plus fast-forwarding `main` were used instead.
