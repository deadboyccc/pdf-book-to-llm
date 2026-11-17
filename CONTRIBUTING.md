# Contributing to book2md

Thanks for helping. book2md is deliberately small — one module, one job — so a good
change is usually a small one.

## Set up

```bash
git clone https://github.com/deadboyccc/pdf-book-to-llm && cd pdf-book-to-llm
uv sync --only-group dev        # test and lint tools only; enough for most changes
uv sync                         # + Docling, for the end-to-end tests and real runs
```

## Workflow

1. Write or change a test that shows the behaviour (or reproduces the bug).
2. Make it pass with the smallest change to `book2md.py`.
3. Run the checks below.
4. Update the [README](README.md) or [docs/setup-and-script.md](docs/setup-and-script.md)
   if behaviour, options or output changed. Record judgement calls in
   [docs/ASSUMPTIONS.md](docs/ASSUMPTIONS.md).

## Checks

| Check | Command | Needs |
|-------|---------|-------|
| Lint | `uv run ruff check . && uv run ruff format --check .` | dev group |
| Unit tests | `uv run pytest tests/unit --cov --cov-fail-under=95` | dev group |
| End-to-end tests | `uv run pytest tests/e2e` | `uv sync` and ~1 GB of model weights (first run) |
| Lockfile | `uv lock --check` | — |

CI runs all of them on every push: unit tests on Linux, macOS and Windows with
Python 3.10, 3.12 and 3.13, and the end-to-end tests with the real Docling models
on Linux. The converted sample pages are uploaded as a build artifact.

## Writing tests

- **Unit tests** (`tests/unit`) never import Docling. Fake it at the boundary:
  replace `convert_pdf`, or install stand-in modules as the existing fixtures do.
- **End-to-end tests** (`tests/e2e`) run the installed `book2md` command as a real
  process on the generated sample book. Assert structure (markers, tables, code
  fences, placeholders), not exact Markdown, which shifts between model versions.
- Every test asserts something; no sleeps; no network beyond Docling's model download.

## Releasing

1. Bump `__version__` in `book2md.py` (the package version is read from it).
2. Push to a `milestone-*` branch for heavy changes and wait for CI to go green,
   then fast-forward `main`.
3. Tag `vX.Y.Z` on the green commit and publish a GitHub release with the wheel,
   sdist (`uv build`) and `SHA256SUMS`.
