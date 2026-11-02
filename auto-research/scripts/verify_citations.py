"""Cổng TRÍCH DẪN: mọi DOI đối chiếu Crossref (arXiv qua API arXiv); tiêu đề, tác giả, năm phải khớp.

  python verify_citations.py [--run DIR] [--prune] [--json]
Thoát mã 1 nếu có trích dẫn không đạt. --prune: xoá mục không đạt khỏi references.bib và
ghi manuscript/rejected_citations.csv (agent phải sửa câu trích dẫn trong bản thảo sau đó).
"""
from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import find_run_dir, http_get, http_json, norm_doi, norm_title, read_csv, write_csv  # noqa: E402
from manuscript_io import (body_without_references, cited_keys, find_manuscript, parse_bib,  # noqa: E402
                           read_text, strip_comments)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def family(name: str) -> str:
    name = name.strip()
    fam = name.split(",")[0] if "," in name else (name.split()[-1] if name.split() else "")
    return norm_title(fam)


def lookup(doi: str, email: str) -> dict | None:
    m = re.match(r"10\.48550/arxiv\.(.+)", doi)
    if m:
        b = http_get("http://export.arxiv.org/api/query?id_list=" + m.group(1), email=email,
                     accept="application/atom+xml")
        ns = {"a": "http://www.w3.org/2005/Atom"}
        e = ET.fromstring(b).find("a:entry", ns) if b else None
        if e is None or not e.findtext("a:title", "", ns) or e.findtext("a:title", "", ns).strip() == "Error":
            return None
        return dict(title=e.findtext("a:title", "", ns), years={int(e.findtext("a:published", "", ns)[:4])},
                    families=[family(a.findtext("a:name", "", ns)) for a in e.findall("a:author", ns)])
    j = http_json("https://api.crossref.org/works/" + urllib.parse.quote(doi), email=email)
    if not j:
        return None
    it = j["message"]
    years = set()
    for k in ("issued", "published-print", "published-online", "published", "created"):
        dp = (it.get(k) or {}).get("date-parts") or [[None]]
        if dp[0] and dp[0][0]:
            years.add(int(dp[0][0]))
    return dict(title=" ".join(it.get("title") or [""]), years=years,
                families=[norm_title(a.get("family") or a.get("name") or "") for a in it.get("author") or []])


def check_entry(key: str, e: dict, email: str, cache: dict) -> tuple[str, str]:
    doi = norm_doi(e.get("doi", ""))
    if not doi:
        return "fail", "không có DOI"
    if doi in cache:
        meta = cache[doi]
        if meta and "years" in meta:
            meta = dict(meta, years=set(meta["years"]))
    else:
        try:
            meta = lookup(doi, email)
        except Exception as ex:
            return "fail", f"không tra được Crossref (mạng): {ex}"
        cache[doi] = dict(meta, years=sorted(meta["years"])) if meta else None
    if meta is None:
        return "fail", f"DOI không tồn tại trên Crossref/arXiv: {doi}"
    probs = []
    ratio = difflib.SequenceMatcher(None, norm_title(e.get("title", "")), norm_title(meta["title"])).ratio()
    if ratio < 0.85:
        probs.append(f"tiêu đề lệch (giống {ratio:.2f}): bib={e.get('title', '')!r} vs nguồn={meta['title']!r}")
    try:
        y = int(re.findall(r"\d{4}", e.get("year", "") or e.get("date", ""))[0])
        if meta["years"] and y not in meta["years"]:
            probs.append(f"năm lệch: bib={y} vs nguồn={sorted(meta['years'])}")
    except IndexError:
        probs.append("thiếu năm")
    authors = [a for a in re.split(r"\s+and\s+", e.get("author", "")) if a.strip()]
    if not authors:
        probs.append("thiếu tác giả")
    elif meta["families"] and family(authors[0]) not in meta["families"]:
        probs.append(f"tác giả đầu lệch: {authors[0]!r} không có trong {meta['families'][:5]}")
    return ("fail", "; ".join(probs)) if probs else ("pass", "khớp")


def run(rd: Path, prune: bool = False) -> dict:
    ms, kind = find_manuscript(rd)
    if not ms:
        return {"gate": "citations", "pass": False, "items": [], "summary": "chưa có bản thảo"}
    text = strip_comments(read_text(ms), kind)
    bib = parse_bib(rd / "manuscript/references.bib")
    keys = cited_keys(body_without_references(text, kind), kind)
    email = ""
    try:
        from common import load_profile
        email = load_profile(rd).get("contact_email", "")
    except SystemExit:
        pass
    cache_p = rd / "manuscript/.citation_cache.json"
    cache = json.loads(cache_p.read_text(encoding="utf-8")) if cache_p.is_file() else {}
    items = []
    for k in keys:
        if k not in bib:
            items.append(dict(key=k, doi="", status="fail", detail="được trích nhưng không có trong references.bib"))
            continue
        st, det = check_entry(k, bib[k], email, cache)
        items.append(dict(key=k, doi=norm_doi(bib[k].get("doi", "")), status=st, detail=det))
    cache_p.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
    bad = [i for i in items if i["status"] != "pass"]
    if prune and bad:
        bibp = rd / "manuscript/references.bib"; s = bibp.read_text(encoding="utf-8")
        for k in sorted((i["key"] for i in bad if i["key"] in bib), key=lambda k: -bib[k]["_span"][0]):
            a, b = bib[k]["_span"]; s = s[:a] + s[b:]
        bibp.write_text(s, encoding="utf-8")
        old = read_csv(rd / "manuscript/rejected_citations.csv")
        write_csv(rd / "manuscript/rejected_citations.csv", old + bad, ["key", "doi", "status", "detail"])
    return {"gate": "citations", "pass": not bad and bool(keys) or (not keys and not bib),
            "items": items, "summary": f"{len(items) - len(bad)}/{len(items)} trích dẫn đạt"}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--run"); ap.add_argument("--prune", action="store_true")
    ap.add_argument("--json", action="store_true"); a = ap.parse_args()
    rd = Path(a.run) if a.run else find_run_dir()
    r = run(rd, a.prune)
    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
    else:
        print(("PASS " if r["pass"] else "FAIL ") + r["summary"])
        for i in r["items"]:
            if i["status"] != "pass":
                print(f"  - [{i['key']}] {i['doi']}: {i['detail']}")
    sys.exit(0 if r["pass"] else 1)


if __name__ == "__main__":
    main()
