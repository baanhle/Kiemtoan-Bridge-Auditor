"""Giai đoạn 1: truy vấn OpenAlex, Semantic Scholar, Crossref, arXiv → literature/candidates.csv.

  python lit_search.py [--run DIR] [--query "..."] [--per-source 50]
Nguồn nào lỗi mạng thì bỏ qua và ghi vào logs/search.log, không dừng pipeline.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
import time
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import find_run_dir, http_get, http_json, load_profile, norm_doi, norm_title, write_csv  # noqa: E402

FIELDS = ["doi", "title", "year", "authors", "venue", "abstract", "citations", "source", "url", "query"]


def openalex(q, y0, n, email):
    url = ("https://api.openalex.org/works?" + urllib.parse.urlencode({
        "search": q, "filter": f"from_publication_date:{y0}-01-01", "per-page": min(n, 200),
        "mailto": email or ""}))
    out = []
    for w in (http_json(url, email=email) or {}).get("results", []):
        inv = w.get("abstract_inverted_index") or {}
        words = sorted(((p, wd) for wd, ps in inv.items() for p in ps))
        out.append(dict(doi=norm_doi(w.get("doi") or ""), title=w.get("title") or "",
                        year=w.get("publication_year") or "",
                        authors="; ".join(a["author"]["display_name"] for a in w.get("authorships", [])[:6]),
                        venue=((w.get("primary_location") or {}).get("source") or {}).get("display_name", ""),
                        abstract=" ".join(wd for _, wd in words), citations=w.get("cited_by_count", 0),
                        source="openalex", url=w.get("id", "")))
    return out


def semantic_scholar(q, y0, n, email):
    url = ("https://api.semanticscholar.org/graph/v1/paper/search?" + urllib.parse.urlencode({
        "query": q, "year": f"{y0}-", "limit": min(n, 100),
        "fields": "title,year,abstract,citationCount,externalIds,authors,venue,url"}))
    out = []
    for p in (http_json(url, email=email) or {}).get("data", []):
        ext = p.get("externalIds") or {}
        doi = ext.get("DOI") or (f"10.48550/arxiv.{ext['ArXiv']}" if ext.get("ArXiv") else "")
        out.append(dict(doi=norm_doi(doi), title=p.get("title") or "", year=p.get("year") or "",
                        authors="; ".join(a.get("name", "") for a in (p.get("authors") or [])[:6]),
                        venue=p.get("venue") or "", abstract=p.get("abstract") or "",
                        citations=p.get("citationCount") or 0, source="semanticscholar", url=p.get("url", "")))
    return out


def crossref(q, y0, n, email):
    url = ("https://api.crossref.org/works?" + urllib.parse.urlencode({
        "query.bibliographic": q, "filter": f"from-pub-date:{y0},type:journal-article",
        "rows": min(n, 100), "mailto": email or ""}))
    out = []
    for it in ((http_json(url, email=email) or {}).get("message") or {}).get("items", []):
        year = ((it.get("issued") or {}).get("date-parts") or [[""]])[0][0]
        abs_ = re.sub(r"<[^>]+>", " ", it.get("abstract", "") or "")
        out.append(dict(doi=norm_doi(it.get("DOI", "")), title=(it.get("title") or [""])[0], year=year,
                        authors="; ".join(f"{a.get('given', '')} {a.get('family', '')}".strip()
                                          for a in (it.get("author") or [])[:6]),
                        venue=(it.get("container-title") or [""])[0], abstract=" ".join(abs_.split()),
                        citations=it.get("is-referenced-by-count", 0), source="crossref", url=it.get("URL", "")))
    return out


def arxiv(q, y0, n, email):
    url = "http://export.arxiv.org/api/query?" + urllib.parse.urlencode({
        "search_query": f"all:{q}", "start": 0, "max_results": min(n, 100), "sortBy": "relevance"})
    b = http_get(url, email=email, accept="application/atom+xml")
    ns = {"a": "http://www.w3.org/2005/Atom", "x": "http://arxiv.org/schemas/atom"}
    out = []
    if not b:
        return out
    for e in ET.fromstring(b).findall("a:entry", ns):
        year = (e.findtext("a:published", "", ns) or "")[:4]
        if year and int(year) < y0:
            continue
        aid = (e.findtext("a:id", "", ns) or "").rsplit("/abs/", 1)[-1]
        aid_nov = re.sub(r"v\d+$", "", aid)
        doi = e.findtext("x:doi", "", ns) or f"10.48550/arxiv.{aid_nov}"
        out.append(dict(doi=norm_doi(doi), title=" ".join((e.findtext("a:title", "", ns) or "").split()),
                        year=year, authors="; ".join(a.findtext("a:name", "", ns) for a in e.findall("a:author", ns)[:6]),
                        venue="arXiv", abstract=" ".join((e.findtext("a:summary", "", ns) or "").split()),
                        citations=0, source="arxiv", url=f"https://arxiv.org/abs/{aid}"))
    return out


SOURCES = [("openalex", openalex), ("semanticscholar", semantic_scholar), ("crossref", crossref), ("arxiv", arxiv)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run"); ap.add_argument("--query", action="append")
    ap.add_argument("--per-source", type=int, default=50)
    ap.add_argument("--out", default="literature/candidates.csv")
    a = ap.parse_args()
    rd = Path(a.run) if a.run else find_run_dir()
    prof = load_profile(rd)
    email = prof.get("contact_email", "")
    y0 = dt.date.today().year - int(prof.get("years_back", 5))
    queries = a.query or prof.get("search_queries") or [" ".join(prof.get("keywords", [])[:4])]
    log = open(rd / "logs" / "search.log", "a", encoding="utf-8")
    merged: dict[str, dict] = {}
    for q in queries:
        for name, fn in SOURCES:
            try:
                rows = fn(q, y0, a.per_source, email)
                log.write(f"OK {name} q={q!r} n={len(rows)}\n")
            except Exception as e:  # nguồn lỗi → bỏ qua
                log.write(f"FAIL {name} q={q!r}: {e}\n"); rows = []
            for r in rows:
                if not r["title"]:
                    continue
                key = r["doi"] or "t:" + norm_title(r["title"])
                r["query"] = q
                old = merged.get(key)
                if old is None:
                    merged[key] = r
                else:  # gộp: giữ abstract dài nhất, số trích dẫn lớn nhất
                    if len(r["abstract"]) > len(old["abstract"]):
                        old["abstract"] = r["abstract"]
                    old["citations"] = max(int(old["citations"] or 0), int(r["citations"] or 0))
                    if r["source"] not in old["source"]:
                        old["source"] += "+" + r["source"]
                    old["doi"] = old["doi"] or r["doi"]
            time.sleep(1)
    rows = sorted(merged.values(), key=lambda r: -int(r["citations"] or 0))
    write_csv(rd / a.out, rows, FIELDS)
    log.close()
    print(json.dumps({"candidates": len(rows), "file": str(rd / a.out)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
