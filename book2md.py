#!/usr/bin/env python3
"""Convert a PDF book into one Markdown file + one image per page using Docling.

Output (under ~/study/corpus/<book>[_pS-E]/pages/):
  p0001.md, p0001.png
  p0002.md, p0002.png
  ...
Page numbers are PDF page numbers (counted from the first page of the file),
not the numbers printed on the pages.
"""
import argparse
import sys
import time
from pathlib import Path

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling_core.types.doc import ImageRefMode

CORPUS_ROOT = Path.home() / "study" / "corpus"


def parse_pages(spec: str) -> tuple[int, int]:
    """'150-210' -> (150, 210); '150' -> (150, 150)."""
    try:
        if "-" in spec:
            a, b = spec.split("-", 1)
            start, end = int(a), int(b)
        else:
            start = end = int(spec)
    except ValueError:
        sys.exit(f"Bad --pages value '{spec}'. Use e.g. 1-50 or 120.")
    if start < 1 or end < start:
        sys.exit("--pages must be 1-based with start <= end.")
    return start, end


def main() -> None:
    ap = argparse.ArgumentParser(description="PDF book -> per-page Markdown + images")
    ap.add_argument("pdf", help="path to the PDF")
    ap.add_argument("--pages", help="page range, e.g. 1-50 (1-based, PDF page numbers)")
    ap.add_argument("--ocr", action="store_true",
                    help="enable OCR (only for scanned books; much slower)")
    ap.add_argument("--formulas", action="store_true",
                    help="enable formula recognition (math-heavy books)")
    ap.add_argument("--scale", type=float, default=1.5,
                    help="page image scale (default 1.5; 2.0 = sharper, bigger)")
    args = ap.parse_args()

    pdf = Path(args.pdf).expanduser().resolve()
    if not pdf.is_file():
        sys.exit(f"File not found: {pdf}")

    start, end = (1, sys.maxsize)
    suffix = ""
    if args.pages:
        start, end = parse_pages(args.pages)
        suffix = f"_p{start}-{end}"

    out = CORPUS_ROOT / (pdf.stem + suffix) / "pages"
    out.mkdir(parents=True, exist_ok=True)

    opts = PdfPipelineOptions()
    opts.do_ocr = args.ocr
    opts.do_table_structure = True
    opts.do_code_enrichment = True
    opts.do_formula_enrichment = args.formulas
    opts.generate_page_images = True
    opts.images_scale = args.scale

    converter = DocumentConverter(
        format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=opts)}
    )

    print(f"Converting: {pdf.name}  pages={args.pages or 'all'}  ocr={args.ocr}")
    t0 = time.time()
    doc = converter.convert(str(pdf), page_range=(start, end)).document
    print(f"Converted in {time.time() - t0:.0f}s. Writing pages...")

    count = 0
    for n in sorted(doc.pages):
        if n < start or n > end:
            continue

        md = doc.export_to_markdown(page_no=n, image_mode=ImageRefMode.PLACEHOLDER)
        (out / f"p{n:04d}.md").write_text(
            f"<!-- PAGE {n} -->\n{md.strip()}\n", encoding="utf-8"
        )

        img = doc.pages[n].image
        if img is not None and img.pil_image is not None:
            img.pil_image.save(out / f"p{n:04d}.png")

        count += 1

    if count == 0:
        sys.exit("No pages were converted. Check the page range.")

    print(f"Done: {count} pages -> {out}")


if __name__ == "__main__":
    main()
