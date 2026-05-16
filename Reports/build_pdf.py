"""Build the 5-page PDF from final_report.md using pandoc.

Usage:
    cd Reports
    python build_pdf.py

Requires `pandoc` on PATH and a LaTeX engine (e.g., MiKTeX on Windows or
texlive-xetex on Linux). On Windows: `winget install JohnMacFarlane.Pandoc`
plus `winget install MiKTeX.MiKTeX`.

If pandoc is missing, this script prints a fallback instruction to use
an online converter or Word.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MD = ROOT / "final_report.md"
PDF = ROOT / "final_report.pdf"


def main() -> None:
    if not MD.exists():
        print(f"[err] {MD} not found")
        sys.exit(1)

    pandoc = shutil.which("pandoc")
    if pandoc is None:
        print(
            "[err] pandoc not found on PATH.\n"
            "      Install: `winget install JohnMacFarlane.Pandoc` (Windows)\n"
            "               `brew install pandoc` (macOS)\n"
            "               `apt install pandoc texlive-xetex` (Linux)\n"
            "      Fallback: open final_report.md in VS Code with Markdown PDF extension,\n"
            "      OR paste into pandoc.org's online converter."
        )
        sys.exit(1)

    cmd = [
        pandoc,
        str(MD),
        "-o",
        str(PDF),
        "--pdf-engine=xelatex",
        "-V",
        "geometry:margin=2cm",
        "-V",
        "fontsize=10pt",
        "--toc-depth=2",
    ]

    print(f"[pdf] running: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
    except Exception as e:
        print(f"[err] pandoc execution failed: {e}")
        sys.exit(1)

    if result.returncode != 0:
        print("[err] pandoc returned non-zero exit code")
        print(result.stdout)
        print(result.stderr)
        print(
            "\n[hint] If LaTeX engine is missing, install MiKTeX (Windows) or texlive-xetex (Linux),\n"
            "       OR use:  pandoc final_report.md -o final_report.html  (no LaTeX needed)\n"
            "       and print HTML to PDF from a browser."
        )
        sys.exit(1)

    print(f"[ok] wrote {PDF}  size={PDF.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
