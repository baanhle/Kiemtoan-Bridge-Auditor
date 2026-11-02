"""Cổng TÍNH MỚI: brief.md phải nêu câu hỏi được chọn kèm bằng chứng tìm kiếm.

Yêu cầu:
  brief.md có dòng `Selected: G<n>` và mục `## Bằng chứng tính mới` liệt kê ≥ 3 truy vấn
  (mỗi dòng dạng `- query: ... | db: ... | date: YYYY-MM-DD | hits: N`).
  gaps/novelty.md có mục `### G<n>` với dòng `Verdict: novel` (hoặc `partially-novel`).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import find_run_dir  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def run(rd: Path) -> dict:
    items = []
    brief = rd / "brief.md"; nov = rd / "gaps/novelty.md"
    if not brief.is_file():
        return {"gate": "novelty", "pass": False, "items": [], "summary": "thiếu brief.md"}
    b = brief.read_text(encoding="utf-8")
    m = re.search(r"^Selected:\s*(G\d+)", b, re.M)
    sel = m.group(1) if m else None
    items.append(dict(item="Selected", status="pass" if sel else "fail", detail="" if sel else "thiếu dòng `Selected: G<n>`"))
    sec = re.split(r"^##\s*(?:Bằng chứng tính mới|Novelty evidence)\s*$", b, flags=re.M | re.I)
    queries = re.findall(r"^-\s*query:.*\|\s*date:\s*\d{4}-\d{2}-\d{2}", sec[1], re.M | re.I) if len(sec) > 1 else []
    items.append(dict(item="evidence", status="pass" if len(queries) >= 3 else "fail",
                      detail=f"{len(queries)} truy vấn có ngày (cần ≥ 3)"))
    if sel:
        n = nov.read_text(encoding="utf-8") if nov.is_file() else ""
        blk = re.split(rf"^###\s*{sel}\b", n, flags=re.M)
        verdict = re.search(r"^Verdict:\s*([\w-]+)", blk[1].split("\n###")[0], re.M) if len(blk) > 1 else None
        ok = bool(verdict and verdict.group(1).lower() in ("novel", "partially-novel"))
        items.append(dict(item=f"novelty.md {sel}", status="pass" if ok else "fail",
                          detail="" if ok else "gaps/novelty.md không có Verdict novel cho ứng viên được chọn"))
    bad = [i for i in items if i["status"] != "pass"]
    return {"gate": "novelty", "pass": not bad, "items": items, "summary": f"ứng viên {sel}: {len(items) - len(bad)}/{len(items)} đạt"}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--run"); ap.add_argument("--json", action="store_true")
    a = ap.parse_args(); rd = Path(a.run) if a.run else find_run_dir()
    r = run(rd)
    print(json.dumps(r, ensure_ascii=False, indent=2) if a.json else ("PASS " if r["pass"] else "FAIL ") + r["summary"])
    sys.exit(0 if r["pass"] else 1)


if __name__ == "__main__":
    main()
