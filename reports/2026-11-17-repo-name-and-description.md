# Report: A Better Repository Name and Description

**Date:** 2026-11-17 · **Applies to:** `deadboyccc/pdf-book-to-llm` at [v1.0.0](https://github.com/deadboyccc/pdf-book-to-llm/releases/tag/v1.0.0)

## Summary

The repository is called `pdf-book-to-llm`, but everything inside it is called
**book2md**: the command, the Python package, the wheel, the mascot's caption and
the README title. The current name is also easy to misremember: it was asked for
as "pdf-to-book-llm", which does not exist. Renaming it to `book2md` makes the repo,
the command and the install line say the same thing.

Nothing has been renamed or changed on GitHub. The snippets below are ready to paste
when you decide.

| | Now | Suggested |
|---|---|---|
| Repository | `pdf-book-to-llm` | **`book2md`** |
| Command / package | `book2md` | `book2md` (unchanged) |
| Install | `uv tool install git+https://github.com/deadboyccc/pdf-book-to-llm` | `uv tool install git+https://github.com/deadboyccc/book2md` |
| GitHub description | *(none)* | see [below](#2-description) |
| Topics | *(none)* | see [below](#3-topics) |

## Where the project stands

The details are in [the improvement report](2026-11-17-improvement-report.md):

| Release | Theme |
|---|---|
| [v0.2.0](https://github.com/deadboyccc/pdf-book-to-llm/releases/tag/v0.2.0) | Installable, reproducible (`uv.lock`), clear errors and exit codes, unit tests on Linux/macOS/Windows |
| [v0.3.0](https://github.com/deadboyccc/pdf-book-to-llm/releases/tag/v0.3.0) | End-to-end tests with the real Docling models on every push |
| [v1.0.0](https://github.com/deadboyccc/pdf-book-to-llm/releases/tag/v1.0.0) | Folio the mascot, pipeline picture, rewritten docs |

Tests: 48 unit tests (99% line coverage) and 10 real-model end-to-end tests; CI green.

## 1. Name

### Recommendation: `book2md`

- **One name everywhere.** The command, the package, the wheel files and the README title are all already `book2md`.
- **Says what it does.** A book goes in, Markdown comes out, in the familiar `x2y` style of tools like `pdf2txt`.
- **Short and hard to misspell.** No order of "pdf", "book" and "llm" to remember.
- **Free where it matters.** `deadboyccc/book2md` is free on GitHub, and `book2md` is free on PyPI, so the tool could later be published as `pip install book2md` without a name clash.

One trade-off: about 13 other people's GitHub repos are also named `book2md`. Inside
your account the name is unique, and the description and topics below are what make
it findable.

### Alternatives considered

| Name | Free on GitHub / PyPI | Why not first choice |
|---|---|---|
| `book2md-llm` | yes / yes | Says "LLM", but no longer matches the command |
| `pdf-pages-for-llm` | yes / yes | Descriptive but long, and unrelated to the command name |
| `bookpages` | yes / yes | Vague: does not say Markdown or PDF |
| `pagewise` | yes / **taken on PyPI** | Could never become the package name |
| `pdf-book-to-llm` (keep) | — | Mismatches the command, and is easy to misremember |

### Copy-paste: rename

On the web: **Settings → General → Repository name** → `book2md` → **Rename**.

With the GitHub CLI:

```bash
gh repo rename book2md --repo deadboyccc/pdf-book-to-llm --yes
```

GitHub redirects the old URL, so existing clones, links and
`uv tool install git+…/pdf-book-to-llm` keep working. Still, point your clone at the new name:

```bash
git remote set-url origin https://github.com/deadboyccc/book2md.git
```

## 2. Description

GitHub's **About** box (gear icon next to *About* on the repository page). Pick one.

**Recommended** (192 characters; the limit is 350):

```text
Turn a PDF book into one Markdown file + one PNG per page, so you can give an LLM the exact pages you're asking about. Tables and code as Markdown, diagrams as images. Runs locally on Docling.
```

**Short** (when space is tight, 89 characters):

```text
PDF book → one Markdown file + one PNG per page, ready for LLMs. Local, built on Docling.
```

**Tagline** (social posts, README badges, release titles):

```text
Give your LLM the exact page, not the whole book.
```

## 3. Topics

Topics drive GitHub search and the "related repositories" lists:

```text
pdf markdown llm docling pdf-to-markdown document-conversion rag ocr books cli python uv
```

## 4. Copy-paste: apply description and topics

```bash
gh repo edit deadboyccc/book2md \
  --description "Turn a PDF book into one Markdown file + one PNG per page, so you can give an LLM the exact pages you're asking about. Tables and code as Markdown, diagrams as images. Runs locally on Docling." \
  --add-topic pdf,markdown,llm,docling,pdf-to-markdown,document-conversion,rag,ocr,books,cli,python,uv
```

If you keep the current name, replace `deadboyccc/book2md` with `deadboyccc/pdf-book-to-llm`.

## 5. After renaming: update the links in the repo

Besides this report, the current name appears 15 times across five files:

| File | Occurrences | What they are |
|---|---|---|
| `README.md` | 5 | Badges, install line, releases links |
| `pyproject.toml` | 2 | `Repository` and `Issues` URLs |
| `docs/setup-and-script.md` | 2 | Install commands |
| `CONTRIBUTING.md` | 1 | Clone command |
| `reports/2026-11-17-improvement-report.md` | 5 | Historical record — leave as written |

Copy-paste, from the repository root:

```bash
# Linux (GNU sed)
grep -rl "deadboyccc/pdf-book-to-llm" README.md pyproject.toml docs CONTRIBUTING.md \
  | xargs sed -i 's#deadboyccc/pdf-book-to-llm#deadboyccc/book2md#g'

# macOS (BSD sed)
grep -rl "deadboyccc/pdf-book-to-llm" README.md pyproject.toml docs CONTRIBUTING.md \
  | xargs sed -i '' 's#deadboyccc/pdf-book-to-llm#deadboyccc/book2md#g'

# also fix the plain clone directory name used in the docs
grep -rl "cd pdf-book-to-llm" docs CONTRIBUTING.md README.md \
  | xargs sed -i 's#cd pdf-book-to-llm#cd book2md#g'   # macOS: sed -i ''

git commit -am "Rename repository to book2md" && git push
```

`uv.lock` and the package itself need no change: the package was always called `book2md`.

## 6. Optional

- **Social preview.** **Settings → General → Social preview** accepts a 1280×640 PNG.
  Folio (`docs/images/mascot.svg`) beside the tagline would make shared links
  recognisable.
- **Publish to PyPI.** The name is free. With trusted publishing from the release
  workflow, `pip install book2md` / `uvx book2md` would work without the `git+` URL.
