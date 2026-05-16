"""Build Reports/final_report_v3.pdf from final_report_v3.tex.

Mirrors the latex-document-skill `compile_latex.sh` logic in pure Python:
  - probes pdflatex + biber; emits install instructions if missing
  - multi-pass: pdflatex -> biber -> pdflatex -> pdflatex
  - parses .log for the most common errors and translates to plain English
  - optional: generates Reports/figures/final_report_v3_p<N>.png previews
              if pdftoppm is on PATH (poppler-utils)

Usage (no CLI flags -- edit CONFIG block below):
    cd Reports
    python build_pdf_v3.py
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

# ============================ CONFIG ============================
TEX_FILE = "final_report_v3.tex"
PDF_FILE = "final_report_v3.pdf"
PREVIEW_PAGES = True       # set False to skip per-page PNG previews
EXPECTED_PAGES = 5
TIMEOUT_SEC = 600          # first run can be slow if MiKTeX auto-installs packages
# ================================================================

ROOT = Path(__file__).resolve().parent
LOG = ROOT / (Path(TEX_FILE).stem + ".log")
AUX = ROOT / (Path(TEX_FILE).stem + ".aux")
BCF = ROOT / (Path(TEX_FILE).stem + ".bcf")

ERROR_HINTS = [
    (r"Missing \$ inserted", "math symbol used outside $...$ -- wrap it in dollar signs"),
    (r"Undefined control sequence", "unknown LaTeX command -- check spelling or add the right \\usepackage"),
    (r"Too many \}'s", "extra closing brace -- count your { and } pairs"),
    (r"File `(.+?)' not found", lambda m: f"missing package {m.group(1)} -- install with `mpm --install={m.group(1)[:-4]}` (MiKTeX) or `tlmgr install {m.group(1)[:-4]}` (TeX Live)"),
    (r"Package biblatex Warning: Please \(re\)run Biber", "rerun build; biber needs to update the .bbl"),
    (r"LaTeX Warning: Reference `(.+?)' on page", lambda m: f"undefined reference '{m.group(1)}' -- another pass will fix it"),
    (r"Overfull \\hbox", "line is slightly too wide; add \\usepackage{microtype} if not already there (it is)"),
]


def find_engine(name: str) -> str | None:
    candidates = [
        shutil.which(name),
        shutil.which(name + ".exe"),
    ]
    # Common MiKTeX install paths on Windows
    miktex_user = Path.home() / "AppData" / "Local" / "Programs" / "MiKTeX" / "miktex" / "bin" / "x64" / (name + ".exe")
    miktex_sys = Path("C:/Program Files/MiKTeX/miktex/bin/x64") / (name + ".exe")
    for p in (miktex_user, miktex_sys):
        if p.exists():
            candidates.append(str(p))
    for c in candidates:
        if c and Path(c).exists():
            return c
    return None


def run(cmd: list[str], cwd: Path, label: str) -> tuple[int, str, str]:
    print(f"  [{label}] {' '.join(Path(c).name for c in cmd[:1])} {' '.join(cmd[1:])}")
    try:
        proc = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, timeout=TIMEOUT_SEC)
        return proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired:
        return -1, "", f"TIMEOUT after {TIMEOUT_SEC}s"


def translate_errors() -> list[str]:
    if not LOG.exists():
        return ["(no .log file)"]
    text = LOG.read_text(encoding="utf-8", errors="replace")
    hits: list[str] = []
    for pattern, hint in ERROR_HINTS:
        for m in re.finditer(pattern, text):
            if callable(hint):
                hits.append(hint(m))
            else:
                hits.append(hint)
    if not hits:
        # surface lines starting with "!"
        for line in text.splitlines():
            if line.startswith("!"):
                hits.append(line.strip())
    seen: set[str] = set()
    unique = []
    for h in hits:
        if h not in seen:
            seen.add(h)
            unique.append(h)
    return unique[:12]


def render_previews(pdftoppm: str, out_dir: Path) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    prefix = str(out_dir / "final_report_v3_p")
    cmd = [pdftoppm, "-png", "-r", "150", str(ROOT / PDF_FILE), prefix]
    rc, out, err = run(cmd, ROOT, "pdftoppm")
    if rc == 0:
        produced = sorted(out_dir.glob("final_report_v3_p*.png"))
        return len(produced)
    print(f"  pdftoppm failed (rc={rc}); skipping previews")
    return 0


def main() -> None:
    print("=" * 60)
    print("BUILD: Reports/final_report_v3.pdf")
    print("=" * 60)

    pdflatex = find_engine("pdflatex")
    biber = find_engine("biber")

    if pdflatex is None:
        print("\n[err] pdflatex not found on PATH or in standard MiKTeX locations.")
        print("\nInstall MiKTeX (Windows, ~10 min, ~1.5 GB):")
        print("    winget install --silent --accept-source-agreements MiKTeX.MiKTeX --scope user")
        print("\nOr a smaller alternative (TinyTeX, ~150 MB):")
        print("    pip install tinytex && python -m tinytex install")
        sys.exit(1)
    if biber is None:
        print(f"\n[warn] biber not found -- bibliography will be empty. (pdflatex={pdflatex})")

    print(f"  pdflatex: {pdflatex}")
    print(f"  biber:    {biber or '(missing)'}")
    print()

    # Enable MiKTeX on-demand installer for the first run (no-op on TeX Live).
    extra_args = ["-enable-installer"] if "MiKTeX" in pdflatex else []

    print("Pass 1: pdflatex (may auto-install packages on first run, can take 5+ min)")
    rc, _, _ = run([pdflatex, *extra_args, "-interaction=nonstopmode", "-halt-on-error=false", TEX_FILE], ROOT, "tex 1")
    if rc != 0:
        print(f"\n  pass 1 returned {rc}; trying to continue (often succeeds on multi-pass)")

    if biber is not None and BCF.exists():
        print("Pass 2: biber")
        rc, _, _ = run([biber, Path(TEX_FILE).stem], ROOT, "biber")
        if rc != 0:
            print(f"\n  biber returned {rc}; bibliography may be incomplete")

    print("Pass 3: pdflatex")
    run([pdflatex, *extra_args, "-interaction=nonstopmode", TEX_FILE], ROOT, "tex 2")

    print("Pass 4: pdflatex")
    rc, _, _ = run([pdflatex, *extra_args, "-interaction=nonstopmode", TEX_FILE], ROOT, "tex 3")

    pdf = ROOT / PDF_FILE
    if not pdf.exists():
        print(f"\n[FAIL] {PDF_FILE} not produced.")
        for h in translate_errors():
            print(f"  - {h}")
        sys.exit(1)

    pages = "?"
    try:
        # use pdfinfo if available
        info = find_engine("pdfinfo")
        if info:
            _, out, _ = run([info, str(pdf)], ROOT, "pdfinfo")
            m = re.search(r"Pages:\s+(\d+)", out)
            if m:
                pages = m.group(1)
    except Exception:
        pass

    size_kb = pdf.stat().st_size / 1024
    print(f"\n[OK] wrote {PDF_FILE}  size={size_kb:.1f} KB  pages={pages}")

    hints = translate_errors()
    if hints:
        print("\n[hints from .log]")
        for h in hints[:5]:
            print(f"  - {h}")

    if PREVIEW_PAGES:
        pdftoppm = find_engine("pdftoppm")
        if pdftoppm:
            print("\nGenerating per-page previews...")
            n = render_previews(pdftoppm, ROOT / "figures")
            print(f"  produced {n} PNGs in Reports/figures/")
        else:
            print("\npdftoppm not on PATH -- skipping previews.")

    if str(pages).isdigit() and int(pages) != EXPECTED_PAGES:
        print(f"\n[warn] expected {EXPECTED_PAGES} pages, got {pages}. Adjust content density.")


if __name__ == "__main__":
    main()
