"""End-to-end: the real `book2md` command and the real Docling models on a small book.

These close the gap the README used to list under *Caveats*: Docling's layout,
table and code models are exercised on content with a known answer.
"""

from __future__ import annotations

import struct
from pathlib import Path

import pytest

from .support import PAGE_WIDTH_PT, Run, run_book2md

pytestmark = pytest.mark.docling


def png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", f"{path.name} is not a PNG"
    width, height = struct.unpack(">II", data[16:24])
    return width, height


def page_md(run: Run, n: int) -> str:
    return (run.pages_dir / f"p{n:04d}.md").read_text(encoding="utf-8")


# ── the whole book ───────────────────────────────────────────────────────────


def test_every_page_gets_a_markdown_file_and_a_png(full_run: Run) -> None:
    assert full_run.exit_code == 0, full_run.stderr
    assert sorted(p.name for p in full_run.pages_dir.iterdir()) == [
        "p0001.md",
        "p0001.png",
        "p0002.md",
        "p0002.png",
        "p0003.md",
        "p0003.png",
    ]
    assert f"Done: 3 pages -> {full_run.pages_dir}" in full_run.stdout


def test_each_markdown_file_starts_with_its_page_marker(full_run: Run) -> None:
    for n in (1, 2, 3):
        assert page_md(full_run, n).startswith(f"<!-- PAGE {n} -->\n")


def test_page_images_are_rendered_at_the_default_scale(full_run: Run) -> None:
    width, height = png_size(full_run.pages_dir / "p0001.png")

    assert abs(width - PAGE_WIDTH_PT * 1.5) <= 2
    assert height > width  # portrait A4


def test_prose_page_keeps_heading_and_paragraph(full_run: Run) -> None:
    md = page_md(full_run, 1)

    assert "# Problems with Replication Lag" in md
    assert "eventual consistency" in md
    assert "asynchronous follower" in md


def test_table_page_becomes_a_markdown_table(full_run: Run) -> None:
    md = page_md(full_run, 2)
    rows = [line for line in md.splitlines() if line.startswith("|")]

    assert len(rows) >= 5, md  # header, separator, three rows
    assert set(rows[1].replace("|", "").strip()) <= set("-: ")
    assert "Guarantee" in rows[0] and "Prevents" in rows[0]
    assert any("Monotonic reads" in row and "Seeing time go backwards" in row for row in rows)


def test_code_page_keeps_the_listing_in_a_code_block(full_run: Run) -> None:
    md = page_md(full_run, 3)

    assert "```" in md, md
    code = md.split("```")[1]
    assert "leader.append(key, value);" in code
    assert "followers.forEach(f -> f.replicate(offset));" in code


def test_figure_is_a_placeholder_and_the_page_png_shows_it(full_run: Run) -> None:
    md = page_md(full_run, 3)

    assert "<!-- image -->" in md
    assert "Figure 1. A leader replicating to two followers." in md
    assert (full_run.pages_dir / "p0003.png").stat().st_size > 10_000


# ── options ──────────────────────────────────────────────────────────────────


def test_page_range_and_scale(sample_book: Path, tmp_path: Path) -> None:
    run = run_book2md(sample_book, tmp_path, "--pages", "2-3", "--scale", "2.0")

    assert run.exit_code == 0, run.stderr
    assert run.pages_dir == tmp_path / "replication_p2-3" / "pages"
    assert sorted(p.name for p in run.pages_dir.iterdir()) == [
        "p0002.md",
        "p0002.png",
        "p0003.md",
        "p0003.png",
    ]
    assert page_md(run, 2).startswith("<!-- PAGE 2 -->\n")  # PDF page numbers are kept
    assert abs(png_size(run.pages_dir / "p0002.png")[0] - PAGE_WIDTH_PT * 2.0) <= 2


# ── failures ─────────────────────────────────────────────────────────────────


def test_start_page_past_the_end_fails_cleanly(sample_book: Path, tmp_path: Path) -> None:
    run = run_book2md(sample_book, tmp_path, "--pages", "5-6")

    assert run.exit_code == 1
    assert "book2md: error:" in run.stderr
    assert "fewer than the requested page_range start 5" in run.stderr
    assert "Traceback" not in run.stderr
    assert not (tmp_path / "replication_p5-6").exists()


def test_a_file_that_is_not_a_pdf_fails_cleanly(tmp_path: Path) -> None:
    fake = tmp_path / "notes.pdf"
    fake.write_text("just some text, not a PDF", encoding="utf-8")

    run = run_book2md(fake, tmp_path / "corpus")

    assert run.exit_code == 1
    assert "book2md: error:" in run.stderr
    assert "Traceback" not in run.stderr
    assert not (tmp_path / "corpus").exists()
