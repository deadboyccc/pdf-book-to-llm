"""Helpers shared by the end-to-end tests."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
REQUIRED = os.environ.get("BOOK2MD_REQUIRE_DOCLING") == "1"

# A4 in PDF points; Docling renders page images at `scale` pixels per point.
PAGE_WIDTH_PT = 595.28


def require(module: str) -> None:
    try:
        __import__(module)
    except ImportError as e:
        if REQUIRED:
            raise
        pytest.skip(f"{module} is not installed ({e}); run `uv sync` to install Docling")


@dataclass
class Run:
    exit_code: int
    stdout: str
    stderr: str
    pages_dir: Path


def run_book2md(pdf: Path, out_root: Path, *args: str) -> Run:
    """Run the installed `book2md` command (falling back to the script) as a real process."""
    command = shutil.which("book2md")
    argv = [command] if command else [sys.executable, str(REPO / "book2md.py")]
    result = subprocess.run(
        [*argv, str(pdf), "--out", str(out_root), *args],
        capture_output=True,
        text=True,
        timeout=1800,
        check=False,
    )
    suffix = ""
    if "--pages" in args:
        start, _, end = args[args.index("--pages") + 1].partition("-")
        suffix = f"_p{start}-{end or start}"
    return Run(result.returncode, result.stdout, result.stderr, out_root / f"{pdf.stem}{suffix}" / "pages")
