"""Cổng SỐ LIỆU: mọi con số trong bản thảo phải có dòng nguồn trong manuscript/numbers.csv.

numbers.csv: value,unit,context,source_type,source,locator
  source_type = result → source là đường dẫn (tương đối thư mục chạy) tới file kết quả;
                         con số phải xuất hiện trong file đó (sau khi làm tròn đúng số chữ số).
  source_type = paper  → source là DOI có trong papers/index.csv hoặc references.bib;
                         locator chỉ vị trí (vd "Table 3", "p. 5").
  source_type = setup  → tham số đầu vào; source là file cấu hình trong sim/ chứa giá trị.

Miễn kiểm tra: số đánh mục (Fig. 3, Table 2, Eq. (4), Section 2.1), năm 1900–2100,
số trong trích dẫn/nhãn/lệnh LaTeX, khối code/toán hiển thị, và số nguyên 0–10 (đếm thường)
trừ khi dùng --strict.

  python verify_numbers.py [--run DIR] [--strict] [--json]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import find_run_dir, norm_doi, read_csv  # noqa: E402
from manuscript_io import body_without_references, find_manuscript, parse_bib, read_text, strip_comments  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

NUM = re.compile(r"(?<![\w.])[-−]?\d{1,3}(?:,\d{3})+(?:\.\d+)?(?![\w])|(?<![\w.])[-−]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?(?![\w])")


def clean(text: str, kind: str) -> str:
    t = body_without_references(strip_comments(text, kind), kind)
    if kind == "md":
        t = re.sub(r"^---\n.*?\n---\n", " ", t, flags=re.S)           # YAML front matter
        t = re.sub(r"```.*?```", " ", t, flags=re.S)
        t = re.sub(r"\$\$.*?\$\$", " ", t, flags=re.S)
        t = re.sub(r"!\[[^\]]*\]\([^)]*\)", lambda m: re.sub(r"\(.*\)", "", m.group(0)), t)  # giữ caption
        t = re.sub(r"\]\([^)]*\)", "]", t)                               # link URL
        t = re.sub(r"\{#[^}]*\}", " ", t)
        t = re.sub(r"\[[^\]]*@[^\]]*\]", " ", t)                          # [@key]
        t = re.sub(r"@[\w:.-]+", " ", t)
        t = re.sub(r"^#+\s*[\d.]*", " ", t, flags=re.M)                  # số mục heading
    else:
        t = re.sub(r"\\begin\{(equation|align|eqnarray|displaymath)\*?\}.*?\\end\{\1\*?\}", " ", t, flags=re.S)
        t = re.sub(r"\\(label|ref|eqref|autoref|cref|Cref|cite\w*|includegraphics|input|include|usepackage|documentclass|bibliography\w*|url|href|vspace|hspace|setlength)\*?(\[[^\]]*\])*\{[^}]*\}", " ", t)
        t = re.sub(r"\\begin\{tabular\}\{[^}]*\}", " ", t)
        t = re.sub(r"\\[a-zA-Z]+\*?", " ", t)
    # tham chiếu đánh số
    t = re.sub(r"\b(Fig(?:ure)?s?|Tables?|Eqs?|Equations?|Sections?|Sec|Hình|Bảng|Phương trình|Mục|Chương|Chapter|Appendix|Ref|Refs)\.?\s*\(?\d+(\.\d+)*[a-z]?\)?((\s*(,|–|-|and|và)\s*\(?\d+(\.\d+)*[a-z]?\)?)*)", " ", t, flags=re.I)
    t = re.sub(r"(?m)^\s*\d+\.\s", " ", t)                                # danh sách đánh số
    return t


def to_dec(s: str) -> Decimal | None:
    try:
        return Decimal(s.replace("−", "-").replace(",", ""))
    except InvalidOperation:
        return None


def decimals(s: str) -> int:
    s = s.replace(",", "")
    if "e" in s.lower():
        return 12
    return len(s.split(".")[1]) if "." in s else 0


def matches(ms_val: str, cand: str) -> bool:
    a, b = to_dec(ms_val), to_dec(cand)
    if a is None or b is None:
        return False
    if a == b:
        return True
    q = Decimal(1).scaleb(-decimals(ms_val))
    try:
        return b.quantize(q) == a or abs(b).quantize(q) == abs(a)
    except InvalidOperation:
        return False


def nums_in_file(p: Path) -> list[str]:
    try:
        return NUM.findall(p.read_text(encoding="utf-8", errors="ignore"))
    except OSError:
        return []


def run(rd: Path, strict: bool = False) -> dict:
    ms, kind = find_manuscript(rd)
    if not ms:
        return {"gate": "numbers", "pass": False, "items": [], "summary": "chưa có bản thảo"}
    text = clean(read_text(ms), kind)
    rows = read_csv(rd / "manuscript/numbers.csv")
    known_dois = {norm_doi(r["doi"]) for r in read_csv(rd / "papers/index.csv")}
    known_dois |= {norm_doi(e.get("doi", "")) for e in parse_bib(rd / "manuscript/references.bib").values()}
    # 1) mỗi dòng numbers.csv phải có nguồn hợp lệ
    row_status = []
    for r in rows:
        st, det = "pass", ""
        typ, src = (r.get("source_type") or "").strip(), (r.get("source") or "").strip()
        if typ in ("result", "setup"):
            p = rd / src
            if not src or not p.is_file():
                st, det = "fail", f"file nguồn không tồn tại: {src}"
            elif not any(matches(r["value"], c) for c in nums_in_file(p)):
                st, det = "fail", f"giá trị {r['value']} không có trong {src}"
        elif typ == "paper":
            if norm_doi(src) not in known_dois:
                st, det = "fail", f"DOI {src} chưa xác minh (không có trong papers/index.csv hoặc references.bib)"
            elif not (r.get("locator") or "").strip():
                st, det = "fail", "thiếu locator (vị trí trong bài)"
        else:
            st, det = "fail", f"source_type không hợp lệ: {typ!r}"
        row_status.append((r, st, det))
    good_vals = [r["value"] for r, st, _ in row_status if st == "pass"]
    # 2) mỗi con số trong bản thảo phải khớp một dòng hợp lệ
    items, seen = [], set()
    for m in NUM.finditer(text):
        s = m.group(0)
        d = to_dec(s)
        if d is None or s in seen:
            continue
        if "." not in s and "e" not in s.lower() and d == int(d):
            if 1900 <= d <= 2100 or (not strict and 0 <= abs(d) <= 10):
                continue
        seen.add(s)
        ok = any(matches(s, v) for v in good_vals)
        ctx = " ".join(text[max(0, m.start() - 40): m.end() + 40].split())
        items.append(dict(value=s, status="pass" if ok else "fail",
                          detail="" if ok else f"không có dòng nguồn hợp lệ trong numbers.csv — «…{ctx}…»"))
    for r, st, det in row_status:
        if st != "pass":
            items.append(dict(value=r.get("value", ""), status="fail", detail="numbers.csv: " + det))
    bad = [i for i in items if i["status"] != "pass"]
    return {"gate": "numbers", "pass": not bad, "items": items,
            "summary": f"{len(items) - len(bad)}/{len(items)} con số có nguồn hợp lệ"}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--run"); ap.add_argument("--strict", action="store_true")
    ap.add_argument("--json", action="store_true"); a = ap.parse_args()
    rd = Path(a.run) if a.run else find_run_dir()
    r = run(rd, a.strict)
    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
    else:
        print(("PASS " if r["pass"] else "FAIL ") + r["summary"])
        for i in r["items"]:
            if i["status"] != "pass":
                print(f"  - {i['value']}: {i['detail']}")
    sys.exit(0 if r["pass"] else 1)


if __name__ == "__main__":
    main()
