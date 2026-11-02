"""Cổng NHẤT QUÁN: mọi hình/bảng/phương trình được tham chiếu đều tồn tại và đánh số đúng.

Markdown (pandoc-crossref): định nghĩa {#fig:x} {#tbl:x} {#eq:x}, tham chiếu @fig:x.
LaTeX: \\label{fig:x} và \\ref/\\eqref/\\autoref/\\cref{fig:x}.
Kiểm tra: tham chiếu có nhãn; nhãn không trùng; file ảnh tồn tại; mỗi hình/bảng được nhắc ít
nhất một lần; số tham chiếu thủ công (Fig. 3 / Table 2) không vượt số lượng và xuất hiện lần
đầu theo thứ tự tăng dần.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import find_run_dir  # noqa: E402
from manuscript_io import body_without_references, find_manuscript, read_text, strip_comments  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def run(rd: Path) -> dict:
    ms, kind = find_manuscript(rd)
    if not ms:
        return {"gate": "consistency", "pass": False, "items": [], "summary": "chưa có bản thảo"}
    t = body_without_references(strip_comments(read_text(ms), kind), kind)
    items = []
    if kind == "md":
        labels = re.findall(r"\{#((?:fig|tbl|eq|sec):[\w-]+)", t)
        refs = re.findall(r"@((?:fig|tbl|eq|sec):[\w-]+)", t)
        images = re.findall(r"!\[[^\]]*\]\(([^)\s]+)", t)
        n_fig = len([l for l in labels if l.startswith("fig:")]) or len(images)
        n_tbl = len([l for l in labels if l.startswith("tbl:")])
    else:
        labels = re.findall(r"\\label\{([^}]+)\}", t)
        refs = [k.strip() for g in re.findall(r"\\(?:ref|eqref|autoref|cref|Cref|pageref)\{([^}]+)\}", t) for k in g.split(",")]
        images = re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", t)
        n_fig = len(re.findall(r"\\begin\{figure\*?\}", t))
        n_tbl = len(re.findall(r"\\begin\{table\*?\}", t))
    for l in sorted({l for l in labels if labels.count(l) > 1}):
        items.append(dict(item=l, status="fail", detail="nhãn bị trùng"))
    for r in sorted(set(refs)):
        items.append(dict(item=r, status="pass" if r in labels else "fail",
                          detail="" if r in labels else "tham chiếu tới nhãn không tồn tại"))
    for l in labels:
        if re.match(r"(fig|tbl|tab):", l) and l not in refs:
            items.append(dict(item=l, status="fail", detail="hình/bảng không được nhắc tới trong văn bản"))
    for img in images:
        cands = [ms.parent / img, rd / img]
        if kind == "tex" and not Path(img).suffix:
            cands += [ms.parent / (img + e) for e in (".pdf", ".png", ".jpg", ".eps")]
        ok = any(c.is_file() for c in cands)
        items.append(dict(item=img, status="pass" if ok else "fail", detail="" if ok else "file hình không tồn tại"))
    for word, total in ((r"(?:Fig(?:ure)?s?\.?|Hình)", n_fig), (r"(?:Tables?|Bảng)", n_tbl)):
        nums = [int(x) for x in re.findall(word + r"\s+(\d+)", t)]
        first = []
        for n in nums:
            if n not in first:
                first.append(n)
        for n in first:
            if n > total or n < 1:
                items.append(dict(item=f"{word} {n}", status="fail", detail=f"chỉ có {total} mục"))
        if first and first != sorted(first):
            items.append(dict(item=word, status="fail", detail=f"thứ tự nhắc lần đầu không tăng dần: {first}"))
    bad = [i for i in items if i["status"] != "pass"]
    return {"gate": "consistency", "pass": not bad, "items": items,
            "summary": f"{len(items) - len(bad)}/{len(items)} mục nhất quán"}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--run"); ap.add_argument("--json", action="store_true")
    a = ap.parse_args(); rd = Path(a.run) if a.run else find_run_dir()
    r = run(rd)
    print(json.dumps(r, ensure_ascii=False, indent=2) if a.json else ("PASS " if r["pass"] else "FAIL ") + r["summary"])
    if not a.json:
        for i in r["items"]:
            if i["status"] != "pass":
                print(f"  - {i['item']}: {i['detail']}")
    sys.exit(0 if r["pass"] else 1)


if __name__ == "__main__":
    main()
