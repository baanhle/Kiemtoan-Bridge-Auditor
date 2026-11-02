---
description: Chạy pipeline nghiên cứu tự động 13 giai đoạn (tài liệu → câu hỏi → mô phỏng → bản thảo) không hỏi người dùng
argument-hint: "[chủ đề] | --from <giai đoạn> [--until <giai đoạn>]"
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, WebFetch, WebSearch, Skill, Task
---

# /auto-research — bộ điều phối

Tham số: `$ARGUMENTS`

Bạn là agent chính của pipeline auto-research. Đọc và tuân thủ tuyệt đối các quy tắc dưới đây
(bản đầy đủ: `${CLAUDE_PLUGIN_ROOT}/templates/CLAUDE.md`).

**Quy tắc cứng**
1. KHÔNG hỏi người dùng ở bất kỳ giai đoạn nào (kể cả subagent). Mơ hồ ⇒ chọn phương án hợp lý nhất,
   ghi `state.py decision ...` vào DECISIONS.md, làm tiếp.
2. Không dừng giữa chừng. Hook Stop sẽ chặn kết thúc phiên cho tới khi pipeline xong và năm cổng đạt.
3. Không bịa trích dẫn hay con số.
4. Môi trường Windows: gọi `python` (không `python3`), đường dẫn dùng `/`.

Ký hiệu: `S = python "${CLAUDE_PLUGIN_ROOT}/scripts/state.py"`, `P = ${CLAUDE_PLUGIN_ROOT}/scripts`.

## Bước 0 — Khởi tạo hoặc tiếp tục

Phân tích `$ARGUMENTS`:
- Có `--from <giai đoạn>` (số 1–13 hoặc tên: search, screen, download, extract, gaps, novelty, select,
  plan, sim, analysis, write, review, final): tìm thư mục chạy gần nhất (file `D:/Research/auto-research/ACTIVE_RUN`
  hoặc `--run <thư mục>` nếu có), rồi `S --run <dir> from <giai đoạn> [--until N]`. Dùng lại mọi file đã có
  của các giai đoạn trước; không chạy lại chúng.
- Ngược lại: `S init --topic "<chủ đề hoặc rỗng>" [--until N]` → in đường dẫn thư mục chạy
  `D:/Research/auto-research/<yyyy-mm-dd>-<slug>/`. Profile lấy từ `D:/Research/profile.yaml`
  (snapshot vào thư mục chạy). Nếu chủ đề rỗng, dùng từ khoá trong profile.
- Nếu `D:/Research/auto-research/CLAUDE.md` chưa có, chép từ `${CLAUDE_PLUGIN_ROOT}/templates/CLAUDE.md`.

Đặt biến môi trường cho mọi lệnh Bash sau đó: thêm `--run "<dir>"` vào mọi script, hoặc làm việc với cwd là `<dir>`.

## Vòng lặp giai đoạn

Lặp: `N = S --run <dir> next`. Nếu `N == 0` ⇒ xong. Nếu `N > until` (state.json) ⇒ dừng hợp lệ, in tóm tắt ngắn.
Với mỗi N: `S start N` → thực hiện theo skill tương ứng (gọi Skill tool với tên skill) → kiểm tra đầu ra tồn tại → `S done N --outputs <file>`.

| N | Skill | Đầu ra bắt buộc |
|---|---|---|
| 1 | `auto-research:literature-search` (phần tìm) | literature/candidates.csv |
| 2 | `auto-research:literature-search` (phần sàng lọc) | literature/shortlist.csv |
| 3 | `auto-research:paper-download` | papers/index.csv, papers/*.pdf |
| 4 | `auto-research:paper-extraction` | extraction/*.json |
| 5 | `auto-research:gap-finding` | gaps/matrix.csv, gaps/candidates.md |
| 6 | `auto-research:novelty-check` | gaps/novelty.md |
| 7 | `auto-research:question-selection` | brief.md |
| 8 | `auto-research:research-plan` | plan.md |
| 9 | `auto-research:simulation` | sim/, results/ |
| 10 | `auto-research:analysis` | analysis/run_all.py, analysis/tables, analysis/figures |
| 11 | `auto-research:manuscript-writing` | manuscript/ |
| 12 | agent `reviewer` (xem dưới) | review/round-N.md |
| 13 | cổng kiểm tra + bàn giao (xem dưới) | SUMMARY.md, VERIFICATION.md |

### Nhánh quay lại (giai đoạn 8–10)
Nếu kế hoạch/mô phỏng/phân tích cho thấy câu hỏi không khả thi (thiếu dữ liệu đầu vào, mô hình không hội tụ sau
các biện pháp hợp lý, ước tính vượt tài nguyên trong profile): `S fallback --reason "<lý do cụ thể>"`.
- In `7` ⇒ chạy lại giai đoạn 7 với `candidate_index` mới (ứng viên kế tiếp trong top 3), rồi tiếp tục 8…
- In `STOP` ⇒ viết `STATUS_REPORT.md` (các ứng viên đã thử, lý do thất bại từng cái, đầu ra còn dùng được,
  đề xuất cho người dùng) và kết thúc.

### Giai đoạn 12 — Phản biện
Tối đa 3 vòng. Mỗi vòng k: gọi Task với `subagent_type: "auto-research:reviewer"` (agent ngữ cảnh mới),
prompt CHỈ gồm: đường dẫn thư mục chạy, số vòng k, đường dẫn bản thảo, `analysis/`, `results/`,
`manuscript/numbers.csv`, `references.bib`, `brief.md` — KHÔNG kể quá trình làm. Reviewer ghi `review/round-k.md`.
Sau đó bạn sửa bản thảo theo từng nhận xét, ghi phản hồi vào `review/response-k.md`. Dừng khi reviewer
ghi `Major issues: 0` hoặc đủ 3 vòng (khi đó ghi DECISIONS.md về các vấn đề còn tồn tại).

### Giai đoạn 13 — Kiểm tra cuối và bàn giao
1. `python "P/run_gates.py" --run <dir>` — chạy 5 cổng, ghi VERIFICATION.md.
2. Cổng nào trượt thì tự sửa (không báo người dùng) và chạy lại:
   - Trích dẫn: `python "P/verify_citations.py" --run <dir> --prune`, rồi sửa/bỏ câu dùng trích dẫn bị loại.
   - Số liệu: thêm dòng nguồn vào numbers.csv hoặc sửa/bỏ con số.
   - Tái lập: sửa analysis/run_all.py cho tất định (seed cố định), chạy lại.
   - Tính mới: `S from 6` và làm lại 6–7 cho đúng câu hỏi đã chọn (giữ candidate_index).
   - Nhất quán: sửa nhãn/tham chiếu/đánh số.
3. `python "P/export_manuscript.py" --run <dir>` xuất định dạng profile.
4. Viết `SUMMARY.md` (đúng MỘT trang): câu hỏi được chọn; top 3 thay thế; bằng chứng tính mới (tóm tắt
   truy vấn + kết quả); kết quả chính (mỗi số kèm nguồn trong numbers.csv); giới hạn (gồm số bài abstract-only).
5. `S done 13`. Bộ bàn giao: `manuscript/`, `SUMMARY.md`, `DECISIONS.md`, `VERIFICATION.md`.

## Song song và chi phí
- Không chạy quá `max_parallel_subagents` (profile) subagent cùng lúc.
- Fan-out lớn (giai đoạn 4 với nhiều bài) có thể tách ra công cụ khác (ví dụ Antigravity) — khi đó chỉ cần
  file `extraction/*.json` đúng schema; ghi DECISIONS.md.

## Kết thúc
Khi xong (hoặc dừng hợp lệ), in cho người dùng 5–10 dòng: thư mục chạy, câu hỏi được chọn, trạng thái năm cổng,
đường dẫn bản thảo và SUMMARY.md. Không hỏi gì thêm.
