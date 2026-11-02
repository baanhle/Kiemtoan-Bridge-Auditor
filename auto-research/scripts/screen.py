"""Giai đoạn 2 (phần cơ học): tính điểm từ khoá sơ bộ cho candidates.csv.

Agent đọc literature/screen_scores.csv rồi tự chấm lại độ liên quan (0–10) và ghi shortlist.
  python screen.py [--run DIR]                     # ghi literature/prescreen.csv
  python screen.py finalize [--run DIR]            # đọc cột relevance trong prescreen.csv → shortlist.csv
"""
from __future__ import annotations

import argparse
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import find_run_dir, load_profile, read_csv, write_csv  # noqa: E402

FIELDS = ["doi", "title", "year", "authors", "venue", "abstract", "citations", "source", "url",
          "kw_score", "relevance", "reason"]


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("mode", nargs="?", default="score")
    ap.add_argument("--run"); a = ap.parse_args()
    rd = Path(a.run) if a.run else find_run_dir()
    prof = load_profile(rd)
    limit = int(prof.get("max_fulltext", 30))
    if a.mode == "score":
        kws = [k.lower() for k in prof.get("keywords", [])] + [k.lower() for k in prof.get("keywords_en", [])]
        rows = read_csv(rd / "literature/candidates.csv")
        for r in rows:
            text = (r["title"] + " " + r["abstract"]).lower()
            hits = sum(1 for k in kws for t in re.split(r"\s+", k) if len(t) > 3 and t in text)
            r["kw_score"] = round(hits + math.log1p(int(r["citations"] or 0)) * 0.3 + (1 if r["abstract"] else -2), 2)
            r.setdefault("relevance", ""); r.setdefault("reason", "")
        rows.sort(key=lambda r: -float(r["kw_score"]))
        write_csv(rd / "literature/prescreen.csv", rows, FIELDS)
        print(f"prescreen: {len(rows)} bài; giới hạn shortlist = {limit}")
    else:
        rows = read_csv(rd / "literature/prescreen.csv")
        rows = [r for r in rows if (r.get("relevance") or "").strip()]
        rows.sort(key=lambda r: (-float(r["relevance"]), -float(r.get("kw_score") or 0)))
        keep = [r for r in rows if float(r["relevance"]) >= 5][:limit]
        write_csv(rd / "literature/shortlist.csv", keep, FIELDS)
        print(f"shortlist: {len(keep)} bài (giới hạn {limit})")


if __name__ == "__main__":
    main()
