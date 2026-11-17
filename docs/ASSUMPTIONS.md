# Assumptions and Decisions

The README and [docs/setup-and-script.md](setup-and-script.md) are the
specification of book2md; there is no separate roadmap. Work was planned from
what those documents promise but the code did not deliver, and from the
README's own *Caveats*. This file records every judgement call taken where the
documents were silent, always the most conservative reading that keeps the
documented behaviour working.

## Behaviour

| ID | Topic | Decision | Why |
|----|-------|----------|-----|
| B1 | Failed conversion | One line, `book2md: error: <reason>`, exit 1. Nothing is written — the output folder is created only after Docling succeeds. | Docling raises `ConversionError` for an unreadable PDF or a start page past the end of the document; the script printed a traceback and left an empty folder behind. |
| B2 | Partial conversion | Pages that converted are written; the missing ones are listed (`3 page(s) could not be converted: 2-3, 6`) with Docling's error messages, and the exit code is 1. | Docling reports `PARTIAL_SUCCESS` without raising. Silently writing fewer files and saying "Done" hides data loss from scripts and users. |
| B3 | Range past the end of the book | `--pages 900-2000` on a 950-page book converts 900–950 and succeeds. | Docling clamps the end of the range; only pages that exist can be missing. |
| B4 | Output location | `--out DIR`, default `~/study/corpus` as before. | The README said to edit `CORPUS_ROOT` in the script, which is impossible once book2md is installed as a command. |
| B5 | Argument errors | Invalid `--pages` or `--scale` (must be > 0) are usage errors: exit 2 with argparse's message. | `--scale 0` or a negative scale only failed deep inside Docling. |
| B6 | `--version` | Added. | Lets users and bug reports state which release they run. |
| B7 | Startup time | Docling is imported only when a conversion starts. | `--help` and argument errors no longer wait seconds for Docling and torch to import. |

## Packaging

| ID | Topic | Decision |
|----|-------|----------|
| P1 | Project file | `pyproject.toml` + `uv.lock` were added. The setup guide already told users to run `uv sync` from a clone, which could not work without them. |
| P2 | Command | `book2md` console script (hatchling). `uv run python book2md.py …` keeps working; `uv tool install git+…` installs the command. |
| P3 | Python | `>=3.10`, Docling's own floor. CI tests 3.10, 3.12 and 3.13. |
| P4 | Torch | Resolved from PyPI as usual, so Linux users with an NVIDIA GPU keep CUDA. The lock pins the exact versions CI tests. |
| P5 | File layout | `readme.md` → `README.md` and `setup-and-script.md` → `docs/setup-and-script.md`: the existing links already pointed there, so moving the files fixed both broken links. |
| P6 | Native binary | Not built. Unlike a JVM project, a Python tool that loads torch and Docling's models gains nothing from a single-file binary; the wheel plus `uv tool install` is the distribution. |
| P7 | Versions | Releases follow the milestones: `v0.2.0` (reproducible and robust), `v0.3.0` (verified on real Docling), `v1.0.0` (documentation). The script before this work counts as 0.1. |

## Testing

| ID | Topic | Decision |
|----|-------|----------|
| T1 | Unit tests | Docling is replaced by fakes at its boundary (`convert_pdf` and the document object), so the unit suite runs in about a second on Linux, macOS and Windows without installing Docling. |
| T2 | Real-model tests | End-to-end tests that run the real Docling models need several GB of downloads; they run in CI, not as part of the unit suite. |
