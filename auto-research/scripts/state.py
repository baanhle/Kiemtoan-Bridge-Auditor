"""Quản lý state.json của một lần chạy.

  python state.py init --topic "..." [--root D:/Research] [--profile path]
  python state.py show
  python state.py start <stage>          # đánh dấu đang chạy
  python state.py done <stage> [--outputs a b]
  python state.py fail <stage> --reason "..."
  python state.py from <stage> [--until N]         # --from: reset các giai đoạn >= stage về pending
  python state.py next                   # in số giai đoạn kế tiếp cần chạy
  python state.py fallback --reason "..." # quay về giai đoạn 7, lấy ứng viên kế tiếp
  python state.py decision --stage N --choice ... --reason ... [--rejected ...]
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (STAGES, append_decision, find_profile, find_run_dir, load_yaml,  # noqa: E402
                    load_state, now_iso, parse_stage, runs_root, save_state, slugify)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def need_run(args) -> Path:
    rd = Path(args.run) if args.run else find_run_dir()
    if not rd or not (rd / "state.json").is_file():
        sys.exit("Không tìm thấy thư mục chạy (state.json). Dùng --run hoặc cd vào thư mục chạy.")
    return rd


def cmd_init(args):
    root = Path(args.root) if args.root else None
    prof_path = Path(args.profile) if args.profile else find_profile()
    prof = load_yaml(prof_path)
    topic = args.topic or ", ".join(prof.get("keywords", [])[:3]) or "research"
    date = dt.date.today().isoformat()
    base = runs_root(root)
    rd = base / f"{date}-{slugify(topic)}"
    i = 2
    while (rd / "state.json").exists() and not args.reuse:
        rd = base / f"{date}-{slugify(topic)}-{i}"
        i += 1
    rd.mkdir(parents=True, exist_ok=True)
    for sub in ["literature", "papers", "extraction", "gaps", "sim", "results",
                "analysis", "manuscript", "review", "logs"]:
        (rd / sub).mkdir(exist_ok=True)
    if not (rd / "profile.yaml").exists():
        shutil.copyfile(prof_path, rd / "profile.yaml")  # snapshot để chạy lại tái lập
    if not (rd / "state.json").exists():
        st = {
            "topic": topic, "created": now_iso(), "status": "running",
            "current_stage": 1, "candidate_index": 0, "fallbacks": [],
            "gate_attempts": 0, "until": 13,
            "stages": {str(n): {"name": label, "skill": skill, "status": "pending"}
                       for n, skill, label in STAGES},
        }
        save_state(rd, st)
    st = load_state(rd)
    st["until"] = int(args.until or 13); st["status"] = "running"
    save_state(rd, st)
    if not (rd / "DECISIONS.md").exists():
        append_decision(rd, 0, f"Chủ đề: {topic}", "Từ tham số lệnh hoặc từ khoá profile.yaml")
    (base / "ACTIVE_RUN").write_text(str(rd), encoding="utf-8")
    print(rd)


def cmd_show(args):
    rd = need_run(args)
    print(json.dumps(load_state(rd), ensure_ascii=False, indent=2))


def cmd_start(args):
    rd = need_run(args); st = load_state(rd); n = parse_stage(args.stage)
    s = st["stages"][str(n)]
    s.update(status="running", started=now_iso())
    st["current_stage"] = n
    save_state(rd, st); print(f"stage {n} running")


def cmd_done(args):
    rd = need_run(args); st = load_state(rd); n = parse_stage(args.stage)
    s = st["stages"][str(n)]
    s.update(status="done", finished=now_iso())
    if args.outputs:
        s["outputs"] = args.outputs
    st["current_stage"] = min(n + 1, 13)
    if n == 13:
        st["status"] = "delivered"
    save_state(rd, st); print(f"stage {n} done")


def cmd_fail(args):
    rd = need_run(args); st = load_state(rd); n = parse_stage(args.stage)
    st["stages"][str(n)].update(status="failed", reason=args.reason, finished=now_iso())
    save_state(rd, st)
    append_decision(rd, n, "Giai đoạn thất bại", args.reason)
    print(f"stage {n} failed")


def reset_from(st: dict, n: int):
    for k, s in st["stages"].items():
        if int(k) >= n:
            s["status"] = "pending"
            for key in ("started", "finished", "reason"):
                s.pop(key, None)
    st["current_stage"] = n
    st["status"] = "running"
    st["gate_attempts"] = 0
    st["stop_blocks"] = 0


def cmd_from(args):
    rd = need_run(args); st = load_state(rd); n = parse_stage(args.stage)
    missing = [k for k, s in st["stages"].items() if int(k) < n and s["status"] != "done"]
    reset_from(st, n)
    if args.until:
        st["until"] = int(args.until)
    save_state(rd, st)
    append_decision(rd, n, f"Chạy lại từ giai đoạn {n} (--from)",
                    "Yêu cầu của lệnh khởi động; dùng lại file đầu ra đã có của các giai đoạn trước",
                    "" if not missing else f"Cảnh báo: giai đoạn {missing} trước đó chưa 'done'")
    print(n)


def cmd_next(args):
    rd = need_run(args); st = load_state(rd)
    for n, _, _ in STAGES:
        if st["stages"][str(n)]["status"] != "done":
            print(n); return
    print(0)


def cmd_fallback(args):
    rd = need_run(args); st = load_state(rd)
    idx = st.get("candidate_index", 0) + 1
    st.setdefault("fallbacks", []).append({"time": now_iso(), "from_stage": st.get("current_stage"),
                                           "reason": args.reason, "new_index": idx})
    if idx >= 3:
        st["status"] = "stopped"
        save_state(rd, st)
        append_decision(rd, st.get("current_stage"), "DỪNG: cả 3 ứng viên đều thất bại", args.reason)
        print("STOP"); return
    st["candidate_index"] = idx
    reset_from(st, 7)
    st["candidate_index"] = idx
    save_state(rd, st)
    append_decision(rd, 7, f"Quay về giai đoạn 7, dùng ứng viên top-{idx + 1}", args.reason,
                    f"Ứng viên top-{idx} (không khả thi)")
    print(7)


def cmd_decision(args):
    rd = need_run(args)
    append_decision(rd, args.stage, args.choice, args.reason, args.rejected or "")
    print("ok")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", help="Thư mục chạy (mặc định: tự tìm)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("init"); p.add_argument("--topic", default=""); p.add_argument("--root")
    p.add_argument("--profile"); p.add_argument("--reuse", action="store_true")
    p.add_argument("--until", type=int, help="Dừng hợp lệ sau giai đoạn này (vd 7 khi chạy thử)")
    sub.add_parser("show"); sub.add_parser("next")
    p = sub.add_parser("start"); p.add_argument("stage")
    p = sub.add_parser("done"); p.add_argument("stage"); p.add_argument("--outputs", nargs="*")
    p = sub.add_parser("fail"); p.add_argument("stage"); p.add_argument("--reason", required=True)
    p = sub.add_parser("from"); p.add_argument("stage"); p.add_argument("--until", type=int)
    p = sub.add_parser("fallback"); p.add_argument("--reason", required=True)
    p = sub.add_parser("decision"); p.add_argument("--stage", default="?")
    p.add_argument("--choice", required=True); p.add_argument("--reason", required=True)
    p.add_argument("--rejected")
    args = ap.parse_args()
    globals()["cmd_" + args.cmd](args)


if __name__ == "__main__":
    main()
