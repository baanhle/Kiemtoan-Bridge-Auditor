"""Cổng TÁI LẬP: chạy lại analysis/run_all.py từ đầu, so sánh bảng và hình với bản đã có.

Quy ước: analysis/run_all.py sinh analysis/tables/*.csv và analysis/figures/*.(png|pdf|svg),
mỗi hình kèm file dữ liệu analysis/figures/<tên>.data.csv. So sánh: nội dung CSV (số làm tròn
10 chữ số có nghĩa) phải trùng; tập tên file hình phải trùng (ảnh PNG có metadata thay đổi nên
so qua file .data.csv).

  python rerun_analysis.py [--run DIR] [--json] [--timeout 3600]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import find_run_dir  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def canon_csv(p: Path) -> str:
    def r(m):
        try:
            return f"{float(m.group(0)):.10g}"
        except ValueError:
            return m.group(0)
    txt = p.read_text(encoding="utf-8", errors="ignore").replace("\r\n", "\n").strip()
    return re.sub(r"-?\d+\.\d+(?:[eE][-+]?\d+)?", r, txt)


def snapshot(d: Path) -> dict[str, str]:
    out = {}
    for sub in ("tables", "figures"):
        for p in sorted((d / sub).glob("*")) if (d / sub).is_dir() else []:
            if p.suffix.lower() == ".csv":
                out[f"{sub}/{p.name}"] = canon_csv(p)
            elif p.is_file():
                out[f"{sub}/{p.name}"] = "<binary>"
    return out


def run(rd: Path, timeout: int = 3600) -> dict:
    script = rd / "analysis/run_all.py"
    if not script.is_file():
        return {"gate": "reproducibility", "pass": False, "items": [], "summary": "thiếu analysis/run_all.py"}
    before = snapshot(rd / "analysis")
    if not before:
        return {"gate": "reproducibility", "pass": False, "items": [], "summary": "analysis/ chưa có bảng/hình"}
    backup = Path(tempfile.mkdtemp(prefix="ar_backup_"))
    for sub in ("tables", "figures"):
        if (rd / "analysis" / sub).is_dir():
            shutil.move(str(rd / "analysis" / sub), str(backup / sub))
    env = dict(os.environ, MPLBACKEND="Agg", PYTHONHASHSEED="0", PYTHONIOENCODING="utf-8")
    try:
        proc = subprocess.run([sys.executable, str(script)], cwd=str(rd), env=env, capture_output=True,
                              text=True, timeout=timeout, encoding="utf-8", errors="replace")
        rc, err = proc.returncode, proc.stderr[-2000:]
    except subprocess.TimeoutExpired:
        rc, err = -1, "timeout"
    after = snapshot(rd / "analysis")
    items = []
    if rc != 0:
        items.append(dict(file="analysis/run_all.py", status="fail", detail=f"exit {rc}: {err}"))
        for sub in ("tables", "figures"):  # khôi phục bản cũ để không mất kết quả
            if (backup / sub).is_dir():
                shutil.rmtree(rd / "analysis" / sub, ignore_errors=True)
                shutil.move(str(backup / sub), str(rd / "analysis" / sub))
    else:
        for k in sorted(set(before) | set(after)):
            if k not in after:
                items.append(dict(file=k, status="fail", detail="không được sinh lại"))
            elif k not in before:
                items.append(dict(file=k, status="fail", detail="file mới, không có ở lần trước"))
            elif before[k] != after[k]:
                items.append(dict(file=k, status="fail", detail="nội dung khác lần trước"))
            else:
                items.append(dict(file=k, status="pass", detail=""))
        figs = [k for k in after if k.startswith("figures/") and not k.endswith(".csv")]
        for f in figs:
            stem = f.rsplit(".", 1)[0]
            if stem + ".data.csv" not in after:
                items.append(dict(file=f, status="fail", detail="thiếu file dữ liệu .data.csv đi kèm hình"))
    shutil.rmtree(backup, ignore_errors=True)
    bad = [i for i in items if i["status"] != "pass"]
    return {"gate": "reproducibility", "pass": not bad, "items": items,
            "summary": f"{len(items) - len(bad)}/{len(items)} đầu ra tái lập giống hệt"}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--run"); ap.add_argument("--json", action="store_true")
    ap.add_argument("--timeout", type=int, default=3600); a = ap.parse_args()
    rd = Path(a.run) if a.run else find_run_dir()
    r = run(rd, a.timeout)
    print(json.dumps(r, ensure_ascii=False, indent=2) if a.json else ("PASS " if r["pass"] else "FAIL ") + r["summary"])
    if not a.json:
        for i in r["items"]:
            if i["status"] != "pass":
                print(f"  - {i['file']}: {i['detail']}")
    sys.exit(0 if r["pass"] else 1)


if __name__ == "__main__":
    main()
