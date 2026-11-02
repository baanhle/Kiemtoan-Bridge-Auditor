"""Giai đoạn 3: tải toàn văn, ghi papers/index.csv (doi, title, source, status, file, note, updated).

  python download.py oa        # Unpaywall + arXiv cho mọi bài trong shortlist chưa có 'full'
  python download.py pending   # in JSON các bài cần tải qua OpenAthens/db.vista bằng Chrome
  python download.py mark --doi D --status full --source openathens --file papers/x.pdf
  python download.py mark --doi D --status abstract-only --note "không có quyền truy cập"
  python download.py expire --reason "OpenAthens hết phiên"   # mọi bài pending → abstract-only
  python download.py next-delay # số giây phải chờ trước lần tải kế tiếp (giãn cách)

Quy tắc: chỉ bài trong shortlist; tổng số bài 'full' không vượt max_fulltext;
giãn cách download_delay_seconds giữa các lần tải. Bài 'abstract-only' vì hết phiên sẽ
được thử tải bù ở lần chạy sau (status không phải 'full' ⇒ vẫn nằm trong danh sách cần tải).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (find_run_dir, http_get, http_json, load_profile, norm_doi, now_iso,  # noqa: E402
                    read_csv, write_csv)

FIELDS = ["doi", "title", "source", "status", "file", "note", "updated"]


def safe_name(doi: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", doi)[:120] + ".pdf"


class Index:
    def __init__(self, rd: Path):
        self.rd = rd
        self.path = rd / "papers/index.csv"
        self.rows = {norm_doi(r["doi"]): r for r in read_csv(self.path)}
        for r in read_csv(rd / "literature/shortlist.csv"):
            d = norm_doi(r["doi"]) or "title:" + r["title"][:60]
            self.rows.setdefault(d, dict(doi=d, title=r["title"], source="", status="pending",
                                         file="", note="", updated=now_iso()))

    def save(self):
        write_csv(self.path, list(self.rows.values()), FIELDS)

    def n_full(self):
        return sum(1 for r in self.rows.values() if r["status"] == "full")

    def set(self, doi, **kw):
        r = self.rows.setdefault(norm_doi(doi), dict(doi=norm_doi(doi), title="", source="", status="pending",
                                                    file="", note="", updated=""))
        r.update(kw); r["updated"] = now_iso(); self.save()


def throttle(rd: Path, delay: int):
    stamp = rd / "papers/.last_download"
    if stamp.exists():
        wait = delay - (time.time() - stamp.stat().st_mtime)
        if wait > 0:
            time.sleep(wait)
    stamp.touch()


def fetch_pdf(url: str, dest: Path, email: str) -> bool:
    try:
        b = http_get(url, email=email, accept="application/pdf", timeout=60)
    except Exception:
        return False
    if not b or not b.startswith(b"%PDF"):
        return False
    dest.write_bytes(b)
    return True


def oa(rd, prof):
    idx = Index(rd); email = prof.get("contact_email", "")
    limit = int(prof["max_fulltext"]); delay = int(prof["download_delay_seconds"])
    for doi, r in list(idx.rows.items()):
        if r["status"] == "full" or doi.startswith("title:"):
            continue
        if idx.n_full() >= limit:
            break
        dest = rd / "papers" / safe_name(doi)
        m = re.match(r"10\.48550/arxiv\.(.+)", doi)
        got = None
        if m:
            throttle(rd, min(delay, 5))
            if fetch_pdf(f"https://arxiv.org/pdf/{m.group(1)}", dest, email):
                got = "arxiv"
        if not got and email:
            try:
                u = http_json(f"https://api.unpaywall.org/v2/{urllib.parse.quote(doi)}?email={email}", email=email)
            except Exception:
                u = None
            locs = ((u or {}).get("oa_locations") or [])
            for loc in locs:
                pdf = loc.get("url_for_pdf")
                if pdf:
                    throttle(rd, delay)
                    if fetch_pdf(pdf, dest, email):
                        got = "unpaywall"; break
        if got:
            idx.set(doi, status="full", source=got, file=f"papers/{dest.name}", note="")
        else:
            idx.set(doi, status="pending", note="cần OpenAthens/db.vista (Chrome)")
    idx.save()
    print(json.dumps({"full": idx.n_full(), "pending": sum(r["status"] == "pending" for r in idx.rows.values())}))


def pending(rd, prof):
    idx = Index(rd)
    room = max(0, int(prof["max_fulltext"]) - idx.n_full())
    todo = [dict(doi=r["doi"], title=r["title"], file=f"papers/{safe_name(r['doi'])}")
            for r in idx.rows.values() if r["status"] != "full" and not r["doi"].startswith("title:")][:room]
    print(json.dumps({"room": room, "delay_seconds": int(prof["download_delay_seconds"]), "todo": todo},
                     ensure_ascii=False, indent=2))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["oa", "pending", "mark", "expire", "next-delay"])
    ap.add_argument("--run"); ap.add_argument("--doi"); ap.add_argument("--status")
    ap.add_argument("--source", default=""); ap.add_argument("--file", default="")
    ap.add_argument("--note", default=""); ap.add_argument("--reason", default="OpenAthens session expired")
    a = ap.parse_args()
    rd = Path(a.run) if a.run else find_run_dir()
    prof = load_profile(rd)
    if a.cmd == "oa":
        oa(rd, prof)
    elif a.cmd == "pending":
        pending(rd, prof)
    elif a.cmd == "mark":
        idx = Index(rd)
        if a.status == "full":
            f = rd / a.file
            if not f.is_file() or not f.read_bytes()[:4] == b"%PDF":
                sys.exit(f"File không phải PDF hợp lệ: {f}")
            if idx.n_full() >= int(prof["max_fulltext"]) and idx.rows.get(norm_doi(a.doi), {}).get("status") != "full":
                sys.exit("Đã đạt max_fulltext — không ghi thêm.")
        idx.set(a.doi, status=a.status, source=a.source, file=a.file, note=a.note)
        print("ok")
    elif a.cmd == "expire":
        idx = Index(rd); n = 0
        for doi, r in idx.rows.items():
            if r["status"] == "pending":
                r.update(status="abstract-only", note=f"session-expired: {a.reason}; tải bù lần sau",
                         updated=now_iso()); n += 1
        idx.save()
        with open(rd / "logs/download.log", "a", encoding="utf-8") as f:
            f.write(f"{now_iso()} EXPIRE {a.reason}: {n} bài → abstract-only\n")
        print(json.dumps({"marked_abstract_only": n}))
    elif a.cmd == "next-delay":
        stamp = rd / "papers/.last_download"
        wait = 0 if not stamp.exists() else max(0, int(prof["download_delay_seconds"] - (time.time() - stamp.stat().st_mtime)))
        print(wait)


if __name__ == "__main__":
    main()
