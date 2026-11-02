"""Giai đoạn 5 (phần cơ học): ma trận phủ vật liệu × kiểu tải × phương pháp từ extraction/*.json.

  python coverage_matrix.py [--run DIR]
→ gaps/matrix.csv (gồm cả tổ hợp n_papers=0 từ các nhãn đã gặp), gaps/future_work.csv
"""
from __future__ import annotations

import argparse
import collections
import itertools
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import find_run_dir, write_csv  # noqa: E402


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", str(s).strip().lower())


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--run"); a = ap.parse_args()
    rd = Path(a.run) if a.run else find_run_dir()
    cells = collections.defaultdict(set)
    mats, loads, meths = collections.Counter(), collections.Counter(), collections.Counter()
    fw = collections.defaultdict(set)
    for f in sorted((rd / "extraction").glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        doi = d.get("doi", f.stem)
        M = [norm(x) for x in d.get("material") or []] or ["(unspecified)"]
        L = [norm(x) for x in d.get("loading") or []] or ["(unspecified)"]
        T = [norm(x) for x in d.get("method") or []] or ["(unspecified)"]
        mats.update(M); loads.update(L); meths.update(T)
        for c in itertools.product(M, L, T):
            cells[c].add(doi)
        for x in d.get("future_work") or []:
            fw[norm(x)].add(doi)
    rows = []
    for m, l, t in itertools.product(mats, loads, meths):
        ds = cells.get((m, l, t), set())
        rows.append(dict(material=m, loading=l, method=t, n_papers=len(ds), dois="; ".join(sorted(ds)),
                         neighbour_density=mats[m] + loads[l] + meths[t]))
    rows.sort(key=lambda r: (r["n_papers"], -r["neighbour_density"]))
    write_csv(rd / "gaps/matrix.csv", rows, ["material", "loading", "method", "n_papers", "dois", "neighbour_density"])
    fwr = sorted(({"future_work": k, "n": len(v), "dois": "; ".join(sorted(v))} for k, v in fw.items()),
                 key=lambda r: -r["n"])
    write_csv(rd / "gaps/future_work.csv", fwr, ["future_work", "n", "dois"])
    print(json.dumps({"cells": len(rows), "empty": sum(r["n_papers"] == 0 for r in rows), "future_work": len(fwr)}))


if __name__ == "__main__":
    main()
