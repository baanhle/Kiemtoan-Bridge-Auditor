"""Tiện ích dùng chung cho các script auto-research (chỉ dùng thư viện chuẩn + PyYAML).

Chạy được trên Windows/PowerShell: mọi đường dẫn dùng pathlib, mọi file mở bằng UTF-8.
"""
from __future__ import annotations

import csv
import datetime as _dt
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

STAGES = [
    (1, "literature-search", "Tìm tài liệu"),
    (2, "literature-search", "Sàng lọc abstract"),
    (3, "paper-download", "Tải toàn văn"),
    (4, "paper-extraction", "Trích xuất có cấu trúc"),
    (5, "gap-finding", "Tìm khoảng trống"),
    (6, "novelty-check", "Kiểm tra tính mới"),
    (7, "question-selection", "Chấm điểm và chọn"),
    (8, "research-plan", "Kế hoạch nghiên cứu"),
    (9, "simulation", "Mô phỏng và tính toán"),
    (10, "analysis", "Phân tích"),
    (11, "manuscript-writing", "Viết bản thảo"),
    (12, "reviewer", "Phản biện"),
    (13, "final-gates", "Kiểm tra cuối và bàn giao"),
]
STAGE_NAMES = {s[1]: s[0] for s in STAGES}
STAGE_ALIASES = {
    "search": 1, "screen": 2, "download": 3, "extract": 4, "extraction": 4,
    "gaps": 5, "gap": 5, "novelty": 6, "select": 7, "selection": 7, "plan": 8,
    "sim": 9, "simulate": 9, "analysis": 10, "analyze": 10, "write": 11,
    "manuscript": 11, "review": 12, "final": 13, "gates": 13,
}

DEFAULT_ROOT = Path(os.environ.get("AUTO_RESEARCH_ROOT", "D:/Research"))
USER_AGENT = "auto-research/0.1 (Claude Code plugin; mailto:{email})"


def parse_stage(value: str) -> int:
    v = str(value).strip().lower()
    if v.isdigit() and 1 <= int(v) <= 13:
        return int(v)
    if v in STAGE_ALIASES:
        return STAGE_ALIASES[v]
    if v in STAGE_NAMES:
        return STAGE_NAMES[v]
    raise SystemExit(f"Giai đoạn không hợp lệ: {value!r}")


def now_iso() -> str:
    return _dt.datetime.now().replace(microsecond=0).isoformat()


def slugify(text: str, maxlen: int = 50) -> str:
    import unicodedata
    t = unicodedata.normalize("NFKD", text.replace("đ", "d").replace("Đ", "D"))
    t = t.encode("ascii", "ignore").decode().lower()
    t = re.sub(r"[^a-z0-9]+", "-", t).strip("-")
    return (t[:maxlen].strip("-")) or "topic"


# ---------------------------------------------------------------- profile
def load_yaml(path: Path) -> dict:
    try:
        import yaml  # type: ignore
    except ImportError:
        sys.exit("Thiếu PyYAML: chạy `python -m pip install pyyaml`")
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def find_profile(run_dir: Path | None = None) -> Path:
    cands = []
    if run_dir:
        cands.append(run_dir / "profile.yaml")
    if os.environ.get("AUTO_RESEARCH_PROFILE"):
        cands.append(Path(os.environ["AUTO_RESEARCH_PROFILE"]))
    cands += [Path.cwd() / "profile.yaml", DEFAULT_ROOT / "profile.yaml",
              DEFAULT_ROOT / "auto-research" / "profile.yaml"]
    for c in cands:
        if c.is_file():
            return c
    sys.exit("Không tìm thấy profile.yaml (đặt ở D:/Research/profile.yaml)")


def load_profile(run_dir: Path | None = None) -> dict:
    p = load_yaml(find_profile(run_dir))
    p.setdefault("years_back", 5)
    p.setdefault("max_fulltext", 30)
    p.setdefault("download_delay_seconds", 20)
    p.setdefault("max_parallel_subagents", 3)
    return p


# ---------------------------------------------------------------- run dir / state
def runs_root(root: Path | None = None) -> Path:
    return (root or DEFAULT_ROOT) / "auto-research"


def find_run_dir(start: Path | None = None) -> Path | None:
    """Thư mục chạy hiện tại: biến môi trường, cwd (hoặc cha) có state.json, hoặc con trỏ ACTIVE_RUN."""
    if os.environ.get("AUTO_RESEARCH_RUN"):
        p = Path(os.environ["AUTO_RESEARCH_RUN"])
        if (p / "state.json").is_file():
            return p
    start = (start or Path.cwd()).resolve()
    for d in [start, *start.parents]:
        if (d / "state.json").is_file():
            return d
        for ptr in (d / "ACTIVE_RUN", d / "auto-research" / "ACTIVE_RUN"):
            if ptr.is_file():
                p = Path(ptr.read_text(encoding="utf-8").strip())
                if (p / "state.json").is_file():
                    return p
    return None


def load_state(run_dir: Path) -> dict:
    with open(run_dir / "state.json", encoding="utf-8") as f:
        return json.load(f)


def save_state(run_dir: Path, state: dict) -> None:
    state["updated"] = now_iso()
    tmp = run_dir / "state.json.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    os.replace(tmp, run_dir / "state.json")


def append_decision(run_dir: Path, stage: int | str, choice: str, reason: str, rejected: str = "") -> None:
    p = run_dir / "DECISIONS.md"
    new = not p.exists()
    with open(p, "a", encoding="utf-8") as f:
        if new:
            f.write("# DECISIONS\n\nNhật ký mọi quyết định agent tự đưa ra.\n\n")
        f.write(f"## {now_iso()} — giai đoạn {stage}\n- **Lựa chọn:** {choice}\n- **Lý do:** {reason}\n")
        if rejected:
            f.write(f"- **Phương án bị loại:** {rejected}\n")
        f.write("\n")


# ---------------------------------------------------------------- CSV
def read_csv(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


# ---------------------------------------------------------------- HTTP
def http_get(url: str, *, email: str = "", accept: str = "application/json",
             timeout: int = 30, retries: int = 3) -> bytes | None:
    """GET có retry/backoff. Trả None nếu 404; ném lỗi nếu mạng hỏng hẳn.

    Kiểm thử offline: đặt AUTO_RESEARCH_HTTP_FIXTURES=<file.json> dạng {url: "nội dung" | null};
    URL không có trong file ⇒ coi như 404.
    """
    fx = os.environ.get("AUTO_RESEARCH_HTTP_FIXTURES")
    if fx:
        with open(fx, encoding="utf-8") as f:
            body = json.load(f).get(url)
        return body.encode("utf-8") if isinstance(body, str) else None
    headers = {"User-Agent": USER_AGENT.format(email=email or "unknown@example.org"), "Accept": accept}
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            last = e
            if e.code in (429, 500, 502, 503, 504):
                time.sleep(2 ** (i + 1))
                continue
            raise
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            last = e
            time.sleep(2 ** (i + 1))
    raise ConnectionError(f"GET thất bại: {url}: {last}")


def http_json(url: str, **kw) -> dict | None:
    b = http_get(url, **kw)
    return json.loads(b.decode("utf-8")) if b else None


def norm_doi(doi: str) -> str:
    d = (doi or "").strip().lower()
    d = re.sub(r"^(https?://(dx\.)?doi\.org/|doi:\s*)", "", d)
    return d


def norm_title(t: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (t or "").lower()).strip()
