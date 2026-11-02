"""Chạy năm cổng kiểm tra và ghi VERIFICATION.md. Dùng cả làm hook lẫn CLI.

  python run_gates.py                 # CLI: chạy cả 5 cổng, in kết quả, mã thoát 1 nếu trượt
  python run_gates.py --hook stop     # hook Stop/SubagentStop: chặn kết thúc phiên nếu chưa đạt
  python run_gates.py --hook edit     # hook PostToolUse(Write|Edit): kiểm tra nhanh khi sửa bản thảo
  python run_gates.py --skip-rerun    # bỏ cổng tái lập (chạy nhanh khi đang sửa)

Hook đọc JSON từ stdin (cwd, stop_hook_active, tool_input...). Không có thư mục chạy đang
hoạt động ⇒ không làm gì (exit 0), để plugin không ảnh hưởng các phiên khác.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_consistency  # noqa: E402
import check_novelty  # noqa: E402
import rerun_analysis  # noqa: E402
import verify_citations  # noqa: E402
import verify_numbers  # noqa: E402
from common import find_run_dir, load_state, now_iso, read_csv, save_state  # noqa: E402
from manuscript_io import find_manuscript  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

MAX_GATE_ATTEMPTS = 10
MAX_STOP_BLOCKS = 30
GATE_LABEL = {"citations": "Trích dẫn", "numbers": "Số liệu", "reproducibility": "Tái lập",
              "novelty": "Tính mới", "consistency": "Nhất quán"}
GATE_ACTION = {"citations": "Loại trích dẫn sai (`verify_citations.py --prune`), sửa câu trích dẫn trong bản thảo",
               "numbers": "Thêm dòng nguồn vào manuscript/numbers.csv hoặc sửa/bỏ con số",
               "reproducibility": "Sửa analysis/run_all.py cho tất định rồi chạy lại",
               "novelty": "Quay lại giai đoạn 6 (`state.py from 6`), bổ sung bằng chứng",
               "consistency": "Sửa nhãn/tham chiếu/đánh số trong bản thảo"}


def all_gates(rd: Path, skip_rerun=False) -> list[dict]:
    res = [verify_citations.run(rd), verify_numbers.run(rd)]
    res.append({"gate": "reproducibility", "pass": False, "items": [], "summary": "bỏ qua (--skip-rerun)"}
               if skip_rerun else rerun_analysis.run(rd))
    res += [check_novelty.run(rd), check_consistency.run(rd)]
    return res


def write_verification(rd: Path, res: list[dict]) -> None:
    L = [f"# VERIFICATION\n\nCập nhật: {now_iso()}\n\n## Kết quả năm cổng\n",
         "| Cổng | Kết quả | Tóm tắt |", "|---|---|---|"]
    for r in res:
        L.append(f"| {GATE_LABEL[r['gate']]} | {'ĐẠT' if r['pass'] else 'KHÔNG ĐẠT'} | {r['summary']} |")
    for r in res:
        bad = [i for i in r["items"] if i.get("status") != "pass"]
        if bad:
            L.append(f"\n### Lỗi — {GATE_LABEL[r['gate']]}\n")
            L += [f"- `{i.get('key') or i.get('value') or i.get('file') or i.get('item')}`: {i.get('detail', '')}" for i in bad[:100]]
    ao = [r for r in read_csv(rd / "papers/index.csv") if r.get("status") != "full"]
    L.append(f"\n## Bài chỉ có abstract ({len(ao)})\n")
    L += [f"- {r['doi']} — {r['title']} ({r['status']}; {r.get('note', '')})" for r in ao] or ["- (không có)"]
    rej = read_csv(rd / "manuscript/rejected_citations.csv")
    L.append(f"\n## Trích dẫn bị loại ({len(rej)})\n")
    L += [f"- [{r['key']}] {r['doi']}: {r['detail']}" for r in rej] or ["- (không có)"]
    (rd / "VERIFICATION.md").write_text("\n".join(L) + "\n", encoding="utf-8")


def block(reason: str):
    print(json.dumps({"decision": "block", "reason": reason}, ensure_ascii=False))
    sys.exit(0)


def hook_stop(rd: Path, skip_rerun: bool):
    st = load_state(rd)
    status = st.get("status")
    if status == "delivered":
        return
    if status == "stopped":
        if not (rd / "STATUS_REPORT.md").is_file():
            block("Pipeline đã dừng (cả 3 ứng viên thất bại) nhưng chưa có STATUS_REPORT.md. Viết báo cáo tình trạng rồi kết thúc.")
        return
    st["stop_blocks"] = st.get("stop_blocks", 0) + 1
    if st["stop_blocks"] > MAX_STOP_BLOCKS:
        st["status"] = "stopped"; save_state(rd, st)
        return
    nxt = next((int(k) for k, s in sorted(st["stages"].items(), key=lambda x: int(x[0])) if s["status"] != "done"), 0)
    until = int(st.get("until") or 13)
    if nxt and nxt > until:
        st["status"] = "paused"; save_state(rd, st)
        return
    ms, _ = find_manuscript(rd)
    if (nxt and nxt < 11) or not ms:
        save_state(rd, st)
        block(f"Pipeline chưa xong: giai đoạn {nxt} ({st['stages'][str(nxt)]['name']}) còn '{st['stages'][str(nxt)]['status']}'. "
              "Không hỏi người dùng — tiếp tục theo commands/auto-research.md (ghi DECISIONS.md nếu mơ hồ).")
    res = all_gates(rd, skip_rerun)
    write_verification(rd, res)
    failed = [r for r in res if not r["pass"]]
    if failed:
        st["gate_attempts"] = st.get("gate_attempts", 0) + 1
        save_state(rd, st)
        if st["gate_attempts"] > MAX_GATE_ATTEMPTS:
            return  # tránh vòng lặp vô hạn; VERIFICATION.md ghi rõ cổng chưa đạt
        msg = [f"Cổng kiểm tra chưa đạt (lần {st['gate_attempts']}/{MAX_GATE_ATTEMPTS}). Tự sửa, không báo người dùng:"]
        for r in failed:
            bad = [i for i in r["items"] if i.get("status") != "pass"][:8]
            msg.append(f"- {GATE_LABEL[r['gate']]}: {r['summary']} → {GATE_ACTION[r['gate']]}")
            msg += [f"    · {i.get('key') or i.get('value') or i.get('file') or i.get('item')}: {i.get('detail', '')[:200]}" for i in bad]
        msg.append("Chi tiết: VERIFICATION.md")
        block("\n".join(msg))
    missing = [f for f in ("SUMMARY.md", "DECISIONS.md", "VERIFICATION.md") if not (rd / f).is_file()]
    if missing or st["stages"]["13"]["status"] != "done":
        save_state(rd, st)
        block(f"Năm cổng đã ĐẠT. Hoàn tất giai đoạn 13: tạo {', '.join(missing) or 'bộ bàn giao'}, "
              "xuất bản thảo theo định dạng profile, rồi `python scripts/state.py done 13`.")


def hook_edit(rd: Path, payload: dict):
    fp = str((payload.get("tool_input") or {}).get("file_path", "")).replace("\\", "/")
    if "/manuscript/" not in fp:
        return
    msgs = []
    if fp.endswith((".bib", ".md", ".tex")):
        r = verify_citations.run(rd)
        if not r["pass"]:
            msgs.append("Trích dẫn: " + r["summary"] + "\n" + "\n".join(
                f"  - [{i['key']}] {i['doi']}: {i['detail']}" for i in r["items"] if i["status"] != "pass"))
    if fp.endswith((".md", ".tex", "numbers.csv")):
        r = verify_numbers.run(rd)
        if not r["pass"]:
            msgs.append("Số liệu: " + r["summary"] + "\n" + "\n".join(
                [f"  - {i['value']}: {i['detail'][:160]}" for i in r["items"] if i["status"] != "pass"][:15]))
    if msgs:
        print("Cổng kiểm tra (nhanh) phát hiện lỗi sau khi sửa " + fp + ":\n" + "\n\n".join(msgs), file=sys.stderr)
        sys.exit(2)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--run"); ap.add_argument("--hook", choices=["stop", "edit"])
    ap.add_argument("--skip-rerun", action="store_true"); a = ap.parse_args()
    payload = {}
    if a.hook:
        try:
            raw = sys.stdin.read()
            payload = json.loads(raw) if raw.strip() else {}
        except Exception:
            payload = {}
    start = Path(payload["cwd"]) if payload.get("cwd") else None
    rd = Path(a.run) if a.run else find_run_dir(start)
    if not rd or not (rd / "state.json").is_file():
        if a.hook:
            sys.exit(0)
        sys.exit("Không tìm thấy thư mục chạy.")
    if a.hook == "stop":
        hook_stop(rd, a.skip_rerun); sys.exit(0)
    if a.hook == "edit":
        hook_edit(rd, payload); sys.exit(0)
    res = all_gates(rd, a.skip_rerun)
    write_verification(rd, res)
    for r in res:
        print(f"{'PASS' if r['pass'] else 'FAIL'} {GATE_LABEL[r['gate']]}: {r['summary']}")
    sys.exit(0 if all(r["pass"] for r in res) else 1)


if __name__ == "__main__":
    main()
