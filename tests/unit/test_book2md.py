"""Unit tests for book2md: no Docling, no models, no PDFs.

Docling is replaced by small fakes at its boundary (``convert_pdf`` and the
document object it returns), so these tests run in milliseconds on any OS.
The real models are exercised by ``tests/e2e``.
"""

from __future__ import annotations

import subprocess
import sys
import types
from pathlib import Path

import pytest

import book2md

# ── fakes ────────────────────────────────────────────────────────────────────


class FakeImage:
    def __init__(self, payload: bytes = b"\x89PNG fake") -> None:
        self.payload = payload

    def save(self, fp: Path) -> None:
        Path(fp).write_bytes(self.payload)


class FakePage:
    def __init__(self, with_image: bool = True) -> None:
        self.image = types.SimpleNamespace(pil_image=FakeImage()) if with_image else None


class FakeDocument:
    """Duck-types the parts of DoclingDocument that book2md uses."""

    def __init__(self, pages: dict[int, FakePage]) -> None:
        self.pages = pages
        self.exports: list[tuple[int, object]] = []

    def export_to_markdown(self, page_no: int, image_mode: object) -> str:
        self.exports.append((page_no, image_mode))
        return f"\n\n## Heading on page {page_no}\n\nBody text.\n\n"


def doc_with(*pages: int, without_image: tuple[int, ...] = ()) -> FakeDocument:
    return FakeDocument({n: FakePage(with_image=n not in without_image) for n in pages})


@pytest.fixture
def pdf(tmp_path: Path) -> Path:
    path = tmp_path / "Designing Data.pdf"
    path.write_bytes(b"%PDF-1.7 not really parsed by the unit tests")
    return path


@pytest.fixture
def fake_convert(monkeypatch: pytest.MonkeyPatch):
    """Replace convert_pdf; returns the list of recorded calls."""
    calls: list[dict] = []
    outcome: dict = {"result": book2md.Converted(document=doc_with(1, 2, 3), page_count=3)}

    def convert(pdf, start, end, *, ocr, formulas, scale):
        calls.append(
            {"pdf": pdf, "start": start, "end": end, "ocr": ocr, "formulas": formulas, "scale": scale}
        )
        if isinstance(outcome["result"], Exception):
            raise outcome["result"]
        return outcome["result"]

    monkeypatch.setattr(book2md, "convert_pdf", convert)
    # write_pages imports Docling's ImageRefMode; a real run always has it installed.
    for name in ("docling_core", "docling_core.types"):
        monkeypatch.setitem(sys.modules, name, types.ModuleType(name))
    monkeypatch.setitem(
        sys.modules,
        "docling_core.types.doc",
        types.SimpleNamespace(ImageRefMode=types.SimpleNamespace(PLACEHOLDER="placeholder")),
    )
    return types.SimpleNamespace(calls=calls, outcome=outcome)


# ── parse_pages ─────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("spec", "expected"),
    [("150-210", (150, 210)), ("150", (150, 150)), ("1-1", (1, 1)), (" 3 - 9 ", (3, 9))],
)
def test_parse_pages_accepts_ranges_and_single_pages(spec: str, expected: tuple[int, int]) -> None:
    assert book2md.parse_pages(spec) == expected


@pytest.mark.parametrize("spec", ["", "abc", "1-", "-5", "1-2-3", "a-b"])
def test_parse_pages_rejects_malformed_specs(spec: str) -> None:
    with pytest.raises(ValueError, match="use e.g. 1-50 or 120"):
        book2md.parse_pages(spec)


@pytest.mark.parametrize("spec", ["0", "0-5", "10-5"])
def test_parse_pages_rejects_zero_and_reversed_ranges(spec: str) -> None:
    with pytest.raises(ValueError, match="1-based and start must be <= end"):
        book2md.parse_pages(spec)


# ── argument parsing ────────────────────────────────────────────────────────────


def test_parser_defaults(pdf: Path) -> None:
    args = book2md.build_parser().parse_args([str(pdf)])

    assert args.pages is None
    assert args.out == book2md.DEFAULT_OUT
    assert args.scale == book2md.DEFAULT_SCALE
    assert (args.ocr, args.formulas) == (False, False)


@pytest.mark.parametrize(
    ("argv", "message"),
    [
        (["--pages", "10-5"], "argument --pages"),
        (["--pages", "x"], "argument --pages"),
        (["--scale", "0"], "must be greater than 0"),
        (["--scale", "-1"], "must be greater than 0"),
        (["--scale", "big"], "is not a number"),
        ([], "the following arguments are required: pdf"),
    ],
)
def test_invalid_arguments_are_usage_errors(
    argv: list[str], message: str, pdf: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    full = argv if argv == [] else [str(pdf), *argv]
    with pytest.raises(SystemExit) as exit_info:
        book2md.main(full)

    assert exit_info.value.code == 2
    assert message in capsys.readouterr().err


def test_version_flag(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exit_info:
        book2md.main(["--version"])

    assert exit_info.value.code == 0
    assert capsys.readouterr().out.strip() == f"book2md {book2md.__version__}"


# ── output layout ───────────────────────────────────────────────────────────────


def test_output_dir_for_whole_book(tmp_path: Path) -> None:
    assert book2md.output_dir(tmp_path, Path("/x/Book.pdf"), None) == tmp_path / "Book" / "pages"


def test_output_dir_for_page_range_never_collides_with_whole_book(tmp_path: Path) -> None:
    assert (
        book2md.output_dir(tmp_path, Path("/x/Book.pdf"), (150, 210)) == tmp_path / "Book_p150-210" / "pages"
    )


@pytest.mark.parametrize(("n", "stem"), [(1, "p0001"), (163, "p0163"), (9999, "p9999"), (12345, "p12345")])
def test_page_stem_is_zero_padded_for_sorting(n: int, stem: str) -> None:
    assert book2md.page_stem(n) == stem


# ── write_pages ─────────────────────────────────────────────────────────────────


def test_write_pages_writes_marker_markdown_and_png_per_page(tmp_path: Path) -> None:
    doc = doc_with(1, 2)
    out = tmp_path / "Book" / "pages"

    written = book2md.write_pages(doc, out, 1, 2, image_mode="placeholder")

    assert written == [1, 2]
    assert (out / "p0001.md").read_text(encoding="utf-8") == (
        "<!-- PAGE 1 -->\n## Heading on page 1\n\nBody text.\n"
    )
    assert (out / "p0002.png").read_bytes() == b"\x89PNG fake"
    assert doc.exports == [(1, "placeholder"), (2, "placeholder")]


def test_write_pages_skips_pages_outside_the_range_and_sorts(tmp_path: Path) -> None:
    doc = doc_with(5, 3, 4, 9)

    written = book2md.write_pages(doc, tmp_path, 3, 5, image_mode="placeholder")

    assert written == [3, 4, 5]
    assert sorted(p.name for p in tmp_path.iterdir()) == [
        "p0003.md",
        "p0003.png",
        "p0004.md",
        "p0004.png",
        "p0005.md",
        "p0005.png",
    ]


def test_write_pages_without_rendered_image_writes_only_markdown(tmp_path: Path) -> None:
    doc = doc_with(1, 2, without_image=(2,))

    book2md.write_pages(doc, tmp_path, 1, 2, image_mode="placeholder")

    assert (tmp_path / "p0002.md").exists()
    assert not (tmp_path / "p0002.png").exists()


def test_write_pages_with_image_object_but_no_pixels_writes_only_markdown(tmp_path: Path) -> None:
    doc = doc_with(1)
    doc.pages[1].image = types.SimpleNamespace(pil_image=None)

    book2md.write_pages(doc, tmp_path, 1, 1, image_mode="placeholder")

    assert [p.name for p in tmp_path.iterdir()] == ["p0001.md"]


def test_write_pages_overwrites_a_previous_run(tmp_path: Path) -> None:
    (tmp_path / "p0001.md").write_text("stale", encoding="utf-8")

    book2md.write_pages(doc_with(1), tmp_path, 1, 1, image_mode="placeholder")

    assert (tmp_path / "p0001.md").read_text(encoding="utf-8").startswith("<!-- PAGE 1 -->")


# ── main: happy path ────────────────────────────────────────────────────────────


def test_main_converts_whole_book_into_out_dir(
    pdf: Path, tmp_path: Path, fake_convert, capsys: pytest.CaptureFixture[str]
) -> None:
    out_root = tmp_path / "corpus"

    code = book2md.main([str(pdf), "--out", str(out_root)])

    pages = out_root / "Designing Data" / "pages"
    assert code == 0
    assert sorted(p.name for p in pages.iterdir()) == [
        "p0001.md",
        "p0001.png",
        "p0002.md",
        "p0002.png",
        "p0003.md",
        "p0003.png",
    ]
    assert fake_convert.calls == [
        {
            "pdf": pdf.resolve(),
            "start": 1,
            "end": book2md.ALL_PAGES,
            "ocr": False,
            "formulas": False,
            "scale": 1.5,
        }
    ]
    out = capsys.readouterr().out
    assert "pages=all" in out
    assert f"Done: 3 pages -> {pages}" in out


def test_main_passes_page_range_and_switches(pdf: Path, tmp_path: Path, fake_convert) -> None:
    fake_convert.outcome["result"] = book2md.Converted(document=doc_with(2, 3), page_count=10)

    code = book2md.main(
        [str(pdf), "--out", str(tmp_path), "--pages", "2-3", "--ocr", "--formulas", "--scale", "2"]
    )

    assert code == 0
    assert fake_convert.calls[0] | {"pdf": None} == {
        "pdf": None,
        "start": 2,
        "end": 3,
        "ocr": True,
        "formulas": True,
        "scale": 2.0,
    }
    assert (tmp_path / "Designing Data_p2-3" / "pages" / "p0003.md").exists()


def test_main_expands_user_home_in_paths(
    pdf: Path, tmp_path: Path, fake_convert, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))  # Windows

    code = book2md.main([str(pdf), "--out", "~/corpus"])

    assert code == 0
    assert (tmp_path / "corpus" / "Designing Data" / "pages" / "p0001.md").exists()


def test_main_range_past_the_end_is_not_a_partial_failure(pdf: Path, tmp_path: Path, fake_convert) -> None:
    fake_convert.outcome["result"] = book2md.Converted(document=doc_with(9, 10), page_count=10)

    assert book2md.main([str(pdf), "--out", str(tmp_path), "--pages", "9-50"]) == 0


# ── main: failures ──────────────────────────────────────────────────────────────


def test_main_missing_file_fails_without_converting(
    tmp_path: Path, fake_convert, capsys: pytest.CaptureFixture[str]
) -> None:
    code = book2md.main([str(tmp_path / "nope.pdf"), "--out", str(tmp_path / "corpus")])

    assert code == 1
    assert "file not found" in capsys.readouterr().err
    assert fake_convert.calls == []


def test_main_conversion_failure_is_one_line_and_leaves_no_output_folder(
    pdf: Path, tmp_path: Path, fake_convert, capsys: pytest.CaptureFixture[str]
) -> None:
    fake_convert.outcome["result"] = book2md.ConversionFailed(
        "Document has 3 pages, fewer than the requested page_range start 5."
    )
    out_root = tmp_path / "corpus"

    code = book2md.main([str(pdf), "--out", str(out_root), "--pages", "5-6"])

    assert code == 1
    assert capsys.readouterr().err == (
        "book2md: error: Document has 3 pages, fewer than the requested page_range start 5.\n"
    )
    assert not out_root.exists()


def test_main_partial_conversion_writes_what_it_can_and_reports_the_rest(
    pdf: Path, tmp_path: Path, fake_convert, capsys: pytest.CaptureFixture[str]
) -> None:
    fake_convert.outcome["result"] = book2md.Converted(
        document=doc_with(1, 4, 5), page_count=6, errors=["Page 2: layout model crashed"]
    )

    code = book2md.main([str(pdf), "--out", str(tmp_path)])

    assert code == 1
    err = capsys.readouterr().err
    assert "3 page(s) could not be converted: 2-3, 6" in err
    assert "book2md: docling: Page 2: layout model crashed" in err
    assert (tmp_path / "Designing Data" / "pages" / "p0005.md").exists()


def test_main_errors_without_missing_pages_still_fail(
    pdf: Path, tmp_path: Path, fake_convert, capsys: pytest.CaptureFixture[str]
) -> None:
    fake_convert.outcome["result"] = book2md.Converted(
        document=doc_with(1, 2, 3), page_count=3, errors=["table model timed out"]
    )

    assert book2md.main([str(pdf), "--out", str(tmp_path)]) == 1
    assert "book2md: docling: table model timed out" in capsys.readouterr().err


def test_main_no_pages_converted_fails(
    pdf: Path, tmp_path: Path, fake_convert, capsys: pytest.CaptureFixture[str]
) -> None:
    fake_convert.outcome["result"] = book2md.Converted(document=doc_with(), page_count=0)

    assert book2md.main([str(pdf), "--out", str(tmp_path)]) == 1
    assert "no pages were converted" in capsys.readouterr().err


@pytest.mark.parametrize(
    ("pages", "text"),
    [([], "none"), ([4], "4"), ([1, 2, 3, 7], "1-3, 7"), ([2, 4, 5, 6, 9, 10], "2, 4-6, 9-10")],
)
def test_ranges_are_compact(pages: list[int], text: str) -> None:
    assert book2md._ranges(pages) == text


# ── convert_pdf, with Docling replaced by fake modules ──────────────────────────


@pytest.fixture
def fake_docling(monkeypatch: pytest.MonkeyPatch):
    """Install minimal stand-ins for the Docling modules convert_pdf imports."""
    state: dict = {"raise": None, "converters": []}

    class ConversionError(RuntimeError):
        pass

    class PdfPipelineOptions:
        pass

    class PdfFormatOption:
        def __init__(self, pipeline_options):
            self.pipeline_options = pipeline_options

    class DocumentConverter:
        def __init__(self, format_options):
            self.format_options = format_options
            self.calls = []
            state["converters"].append(self)

        def convert(self, source, page_range):
            self.calls.append((source, page_range))
            if state["raise"]:
                raise ConversionError(state["raise"])
            return types.SimpleNamespace(
                document="the-document",
                input=types.SimpleNamespace(page_count=42),
                errors=[types.SimpleNamespace(error_message="page 7: odd glyphs")],
            )

    modules = {
        "docling": types.ModuleType("docling"),
        "docling.datamodel": types.ModuleType("docling.datamodel"),
        "docling.datamodel.base_models": types.SimpleNamespace(InputFormat=types.SimpleNamespace(PDF="pdf")),
        "docling.datamodel.pipeline_options": types.SimpleNamespace(PdfPipelineOptions=PdfPipelineOptions),
        "docling.document_converter": types.SimpleNamespace(
            DocumentConverter=DocumentConverter, PdfFormatOption=PdfFormatOption
        ),
        "docling.exceptions": types.SimpleNamespace(ConversionError=ConversionError),
    }
    for name, module in modules.items():
        monkeypatch.setitem(sys.modules, name, module)
    return state


def test_convert_pdf_configures_the_pipeline_from_the_switches(fake_docling) -> None:
    converted = book2md.convert_pdf(Path("/b/Book.pdf"), 3, 9, ocr=True, formulas=False, scale=2.0)

    converter = fake_docling["converters"][0]
    opts = converter.format_options["pdf"].pipeline_options
    assert vars(opts) == {
        "do_ocr": True,
        "do_table_structure": True,
        "do_code_enrichment": True,
        "do_formula_enrichment": False,
        "generate_page_images": True,
        "images_scale": 2.0,
    }
    assert converter.calls == [(str(Path("/b/Book.pdf")), (3, 9))]
    assert converted == book2md.Converted(
        document="the-document", page_count=42, errors=["page 7: odd glyphs"]
    )


def test_convert_pdf_turns_docling_errors_into_conversion_failed(fake_docling) -> None:
    fake_docling["raise"] = "Conversion failed for: x.pdf with status: failure."

    with pytest.raises(book2md.ConversionFailed, match="with status: failure") as info:
        book2md.convert_pdf(Path("x.pdf"), 1, 2, ocr=False, formulas=False, scale=1.5)

    assert type(info.value.__cause__).__name__ == "ConversionError"


# ── running the file as a script ────────────────────────────────────────────────


def test_script_mode_runs_without_importing_docling_for_help() -> None:
    script = Path(book2md.__file__)

    result = subprocess.run(
        [sys.executable, str(script), "--help"], capture_output=True, text=True, check=False
    )

    assert result.returncode == 0
    assert "usage: book2md" in result.stdout
    assert "--pages S-E" in result.stdout
