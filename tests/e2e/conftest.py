"""Fixtures for end-to-end tests that run the real Docling models.

Docling, its models (downloaded on first use) and fpdf2 are needed. Without
them the tests are skipped — unless BOOK2MD_REQUIRE_DOCLING=1, which CI sets so
a broken install fails loudly instead of skipping.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

import pytest

from .support import Run, require, run_book2md


@pytest.fixture(autouse=True)
def _needs_docling() -> None:
    """Every end-to-end test runs the real converter."""
    require("docling")


def _figure_png(path: Path) -> None:
    """A raster diagram (boxes, arrows, labels), the kind of figure a book contains."""
    from PIL import Image, ImageDraw

    image = Image.new("RGB", (600, 300), "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle((30, 100, 200, 200), outline="black", width=4, fill=(220, 235, 255))
    draw.rectangle((400, 40, 570, 120), outline="black", width=4, fill=(220, 255, 225))
    draw.rectangle((400, 180, 570, 260), outline="black", width=4, fill=(220, 255, 225))
    draw.line((200, 150, 400, 80), fill="black", width=4)
    draw.line((200, 150, 400, 220), fill="black", width=4)
    draw.text((70, 140), "leader", fill="black")
    draw.text((440, 75), "follower 1", fill="black")
    draw.text((440, 215), "follower 2", fill="black")
    image.save(path)


@pytest.fixture(scope="session")
def sample_book(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A three-page 'book': prose, a table, then a code listing with a figure."""
    require("fpdf")
    from fpdf import FPDF

    work = tmp_path_factory.mktemp("book")
    figure = work / "figure.png"
    _figure_png(figure)

    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=20)

    pdf.add_page()
    pdf.set_font("Helvetica", "B", 22)
    pdf.cell(0, 14, "Problems with Replication Lag", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    pdf.set_font("Helvetica", size=12)
    pdf.multi_cell(
        0,
        7,
        "Leader-based replication requires all writes to go through a single node, while "
        "read-only queries can go to any replica. When an application reads from an "
        "asynchronous follower, it may see outdated information if the follower has fallen "
        "behind. This inconsistency is a temporary state known as eventual consistency.",
    )

    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 12, "Consistency Guarantees", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    pdf.set_font("Helvetica", size=12)
    with pdf.table(col_widths=(60, 110), text_align="LEFT") as table:
        for row in (
            ("Guarantee", "Prevents"),
            ("Read-after-write", "Reading stale own writes"),
            ("Monotonic reads", "Seeing time go backwards"),
            ("Consistent prefix", "Answers before questions"),
        ):
            cells = table.row()
            for value in row:
                cells.cell(value)

    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 12, "Appending to the Log", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    pdf.set_font("Courier", size=11)
    pdf.set_fill_color(240, 240, 240)
    for line in (
        "public void write(String key, String value) {",
        "    long offset = leader.append(key, value);",
        "    followers.forEach(f -> f.replicate(offset));",
        "}",
    ):
        pdf.cell(0, 6, line, new_x="LMARGIN", new_y="NEXT", fill=True)
    pdf.ln(8)
    pdf.image(str(figure), w=150)
    pdf.set_font("Helvetica", "I", 11)
    pdf.cell(0, 8, "Figure 1. A leader replicating to two followers.", new_x="LMARGIN", new_y="NEXT")

    path = work / "replication.pdf"
    pdf.output(str(path))
    return path


@pytest.fixture(scope="session")
def full_run(sample_book: Path, tmp_path_factory: pytest.TempPathFactory) -> Run:
    """Convert the whole sample book once; most tests only inspect the result."""
    require("docling")
    run = run_book2md(sample_book, tmp_path_factory.mktemp("corpus"))
    artifacts = os.environ.get("BOOK2MD_E2E_ARTIFACTS")
    if artifacts and run.pages_dir.is_dir():
        shutil.copytree(run.pages_dir, Path(artifacts) / "full-run", dirs_exist_ok=True)
        shutil.copy2(sample_book, Path(artifacts) / sample_book.name)
    return run
