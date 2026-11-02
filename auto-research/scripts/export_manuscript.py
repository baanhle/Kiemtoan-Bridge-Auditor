"""Giai đoạn 11/13: xuất bản thảo theo định dạng trong profile (docx qua pandoc, hoặc PDF LaTeX).

  python export_manuscript.py [--run DIR]
Word: manuscript/manuscript.md + references.bib (+ manuscript/reference.docx nếu có) → manuscript/manuscript.docx
LaTeX: manuscript/main.tex → latexmk/pdflatex nếu có, ngược lại chỉ kiểm tra file nguồn.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import find_run_dir, load_profile  # noqa: E402


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--run"); a = ap.parse_args()
    rd = Path(a.run) if a.run else find_run_dir()
    prof = load_profile(rd); m = rd / "manuscript"
    fmt = str(prof.get("output_format", "word")).lower()
    if fmt.startswith("w") or fmt == "docx":
        if not shutil.which("pandoc"):
            sys.exit("Cần pandoc (winget install JohnMacFarlane.Pandoc)")
        cmd = ["pandoc", "manuscript.md", "-o", "manuscript.docx", "--citeproc",
               "--bibliography=references.bib", "--resource-path=.;..;../analysis".replace(";", ":" if sys.platform != "win32" else ";")]
        if shutil.which("pandoc-crossref"):
            cmd[2:2] = ["--filter", "pandoc-crossref"]
        if (m / "reference.docx").is_file():
            cmd.append("--reference-doc=reference.docx")
        if (m / "style.csl").is_file():
            cmd.append("--csl=style.csl")
        subprocess.run(cmd, cwd=str(m), check=True)
        print(m / "manuscript.docx")
    else:
        tool = shutil.which("latexmk")
        if tool:
            subprocess.run([tool, "-pdf", "-interaction=nonstopmode", "main.tex"], cwd=str(m), check=True)
            print(m / "main.pdf")
        else:
            print("Không có latexmk: giữ nguồn LaTeX (main.tex, references.bib, figures).")


if __name__ == "__main__":
    main()
