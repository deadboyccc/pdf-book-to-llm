#!/usr/bin/env python3
"""Convert a PDF book into one Markdown file + one image per page using Docling.

Output (under <out>/<book>[_pS-E]/pages/, <out> defaults to ~/study/corpus):
  p0001.md, p0001.png
  p0002.md, p0002.png
  ...
Page numbers are PDF page numbers (counted from the first page of the file),
not the numbers printed on the pages.

Exit codes: 0 every requested page was written; 1 the conversion failed or some
pages could not be converted (the pages that did convert are still written);
2 invalid command-line arguments.
"""

from __future__ import annotations

import argparse
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

__version__ = "0.3.0"

DEFAULT_OUT = Path.home() / "study" / "corpus"
DEFAULT_SCALE = 1.5
ALL_PAGES = sys.maxsize  # Docling's own "no upper bound" for page ranges

EXIT_OK = 0
EXIT_FAILED = 1


class ConversionFailed(Exception):
    """Docling could not convert the document at all (unreadable file, bad page range, ...)."""


@dataclass
class Converted:
    """What a conversion produced, independent of Docling's result types."""

    document: Any
    page_count: int
    errors: list[str] = field(default_factory=list)


# ── arguments ───────────────────────────────────────────────────────────────────


def parse_pages(spec: str) -> tuple[int, int]:
    """'150-210' -> (150, 210); '150' -> (150, 150). Raises ValueError on bad input."""
    try:
        if "-" in spec:
            a, b = spec.split("-", 1)
            start, end = int(a), int(b)
        else:
            start = end = int(spec)
    except ValueError:
        raise ValueError(f"bad page range '{spec}'; use e.g. 1-50 or 120") from None
    if start < 1 or end < start:
        raise ValueError(f"bad page range '{spec}'; pages are 1-based and start must be <= end")
    return start, end


def _page_range(spec: str) -> tuple[int, int]:
    try:
        return parse_pages(spec)
    except ValueError as e:
        raise argparse.ArgumentTypeError(str(e)) from None


def _positive_float(text: str) -> float:
    try:
        value = float(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"'{text}' is not a number") from None
    if not value > 0:
        raise argparse.ArgumentTypeError(f"must be greater than 0, got {text}")
    return value


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="book2md",
        description="PDF book -> per-page Markdown + images, for asking an LLM about exact pages.",
    )
    ap.add_argument("pdf", type=Path, help="path to the PDF")
    ap.add_argument(
        "--pages",
        type=_page_range,
        metavar="S-E",
        help="page range, e.g. 1-50 or 120 (1-based PDF page numbers; default: all)",
    )
    ap.add_argument(
        "--out", type=Path, default=DEFAULT_OUT, metavar="DIR", help=f"output root (default: {DEFAULT_OUT})"
    )
    ap.add_argument("--ocr", action="store_true", help="enable OCR (only for scanned books; much slower)")
    ap.add_argument("--formulas", action="store_true", help="enable formula recognition (math-heavy books)")
    ap.add_argument(
        "--scale",
        type=_positive_float,
        default=DEFAULT_SCALE,
        help=f"page image scale (default {DEFAULT_SCALE}; 2.0 = sharper, bigger)",
    )
    ap.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return ap


# ── output layout ───────────────────────────────────────────────────────────────


def output_dir(out_root: Path, pdf: Path, pages: tuple[int, int] | None) -> Path:
    """<out_root>/<pdf stem>[_pS-E]/pages — a page-range run never overwrites a full one."""
    suffix = f"_p{pages[0]}-{pages[1]}" if pages else ""
    return out_root / f"{pdf.stem}{suffix}" / "pages"


def page_stem(n: int) -> str:
    """Zero-padded so files sort in page order: 7 -> 'p0007'."""
    return f"p{n:04d}"


def write_pages(doc: Any, out: Path, start: int, end: int, *, image_mode: Any = None) -> list[int]:
    """Write pNNNN.md (+ pNNNN.png when Docling rendered the page) for pages start..end.

    Figures become ``<!-- image -->`` placeholders in the Markdown; the PNG is the
    visual source. Returns the page numbers written, in order.
    """
    if image_mode is None:
        from docling_core.types.doc import ImageRefMode  # noqa: PLC0415 - heavy import, needed only here

        image_mode = ImageRefMode.PLACEHOLDER

    out.mkdir(parents=True, exist_ok=True)
    written: list[int] = []
    for n in sorted(doc.pages):
        if n < start or n > end:
            continue
        md = doc.export_to_markdown(page_no=n, image_mode=image_mode)
        (out / f"{page_stem(n)}.md").write_text(f"<!-- PAGE {n} -->\n{md.strip()}\n", encoding="utf-8")

        image = doc.pages[n].image
        if image is not None and image.pil_image is not None:
            image.pil_image.save(out / f"{page_stem(n)}.png")
        written.append(n)
    return written


# ── conversion ──────────────────────────────────────────────────────────────────


def convert_pdf(pdf: Path, start: int, end: int, *, ocr: bool, formulas: bool, scale: float) -> Converted:
    """Run Docling on pages start..end. Raises ConversionFailed if nothing could be converted."""
    # Docling (and torch) take seconds to import; keep them out of --help and argument errors.
    from docling.datamodel.base_models import InputFormat  # noqa: PLC0415
    from docling.datamodel.pipeline_options import PdfPipelineOptions  # noqa: PLC0415
    from docling.document_converter import DocumentConverter, PdfFormatOption  # noqa: PLC0415
    from docling.exceptions import ConversionError  # noqa: PLC0415

    opts = PdfPipelineOptions()
    opts.do_ocr = ocr
    opts.do_table_structure = True
    opts.do_code_enrichment = True
    opts.do_formula_enrichment = formulas
    opts.generate_page_images = True
    opts.images_scale = scale

    converter = DocumentConverter(format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=opts)})
    try:
        result = converter.convert(str(pdf), page_range=(start, end))
    except ConversionError as e:
        raise ConversionFailed(str(e)) from e
    return Converted(
        document=result.document,
        page_count=result.input.page_count,
        errors=[err.error_message for err in result.errors],
    )


# ── command line ────────────────────────────────────────────────────────────────


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    pdf = args.pdf.expanduser().resolve()
    if not pdf.is_file():
        print(f"book2md: error: file not found: {pdf}", file=sys.stderr)
        return EXIT_FAILED

    start, end = args.pages or (1, ALL_PAGES)
    out = output_dir(args.out.expanduser(), pdf, args.pages)

    shown = f"{start}-{end}" if args.pages else "all"
    print(f"Converting: {pdf.name}  pages={shown}  ocr={args.ocr}  formulas={args.formulas}")
    t0 = time.time()
    try:
        converted = convert_pdf(pdf, start, end, ocr=args.ocr, formulas=args.formulas, scale=args.scale)
    except ConversionFailed as e:
        # Nothing is written, so a failed run leaves no empty output folder behind.
        print(f"book2md: error: {e}", file=sys.stderr)
        return EXIT_FAILED
    print(f"Converted in {time.time() - t0:.0f}s. Writing pages...")

    written = write_pages(converted.document, out, start, end)
    done = set(written)
    missing = [n for n in range(start, min(end, converted.page_count) + 1) if n not in done]

    if not written:
        print("book2md: error: no pages were converted; check the page range", file=sys.stderr)
        return EXIT_FAILED
    print(f"Done: {len(written)} pages -> {out}")
    if missing or converted.errors:
        print(
            f"book2md: warning: {len(missing)} page(s) could not be converted: {_ranges(missing)}",
            file=sys.stderr,
        )
        for message in converted.errors:
            print(f"book2md: docling: {message}", file=sys.stderr)
        return EXIT_FAILED
    return EXIT_OK


def _ranges(pages: list[int]) -> str:
    """[1, 2, 3, 7] -> '1-3, 7' for compact messages."""
    parts: list[tuple[int, int]] = []
    for n in pages:
        if parts and parts[-1][1] == n - 1:
            parts[-1] = (parts[-1][0], n)
        else:
            parts.append((n, n))
    return ", ".join(f"{a}-{b}" if a != b else f"{a}" for a, b in parts) or "none"


if __name__ == "__main__":
    sys.exit(main())
