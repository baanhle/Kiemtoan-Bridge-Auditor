# auto-research — plugin Claude Code

Pipeline nghiên cứu khép kín 13 giai đoạn: tìm tài liệu → sàng lọc → tải toàn văn → trích xuất → khoảng trống →
kiểm tra tính mới → chọn câu hỏi → kế hoạch → mô phỏng → phân tích → bản thảo → phản biện → kiểm tra cuối.
Agent không hỏi người dùng; mọi quyết định ghi vào `DECISIONS.md`. Bản thảo chỉ được bàn giao khi đạt 5 cổng
(trích dẫn, số liệu, tái lập, tính mới, nhất quán). Người dùng chỉ đọc `manuscript/` và `SUMMARY.md`.

## 1. Cài đặt trên Windows

Yêu cầu: Windows 10/11, [Claude Code CLI](https://code.claude.com/docs) (cần Git for Windows), Python ≥ 3.10 trên PATH
(lệnh `python`), Pandoc (nếu xuất Word), Google Chrome + extension **Claude in Chrome** (cho giai đoạn 3).

Mở **PowerShell**:

```powershell
# Công cụ
winget install Python.Python.3.12
winget install JohnMacFarlane.Pandoc
python -m pip install pyyaml numpy scipy matplotlib pandas

# Thư mục làm việc
New-Item -ItemType Directory -Force D:\Research\auto-research, D:\Research\.claude | Out-Null
```

Cài plugin (chọn một cách):

```powershell
# a) Từ GitHub (marketplace trong repo này)
claude plugin marketplace add baanhle/Kiemtoan-Bridge-Auditor
claude plugin install auto-research@baanhle-research

# b) Từ bản clone cục bộ
git clone https://github.com/baanhle/Kiemtoan-Bridge-Auditor D:\Tools\kiemtoan
claude plugin marketplace add D:\Tools\kiemtoan
claude plugin install auto-research@baanhle-research
```

Chép file mẫu (thay `<plugin>` bằng thư mục plugin, ví dụ `D:\Tools\kiemtoan\auto-research`; nếu cài từ GitHub,
plugin nằm trong `%USERPROFILE%\.claude\plugins\`):

```powershell
Copy-Item <plugin>\templates\profile.yaml  D:\Research\profile.yaml
Copy-Item <plugin>\templates\settings.json D:\Research\.claude\settings.json
Copy-Item <plugin>\templates\CLAUDE.md     D:\Research\auto-research\CLAUDE.md
```

Kiểm tra: `cd D:\Research; claude` rồi gõ `/` — phải thấy `/auto-research` (tên đầy đủ `/auto-research:auto-research`).

## 2. Điền `D:\Research\profile.yaml` (một lần)

| Khoá | Ý nghĩa |
|---|---|
| `researcher.expertise` | Chuyên môn — để chấm “khớp chuyên môn” |
| `contact_email` | **Bắt buộc**: Unpaywall và Crossref yêu cầu email |
| `keywords`, `keywords_en`, `search_queries` | Lĩnh vực/từ khoá; truy vấn tiếng Anh dùng để tìm |
| `tools.fem`, `tools.languages`, `tools.solver_commands`, `tools.compute` | Công cụ có sẵn — căn cứ chấm tính khả thi |
| `target_journals`, `manuscript_language`, `output_format` | Tạp chí, ngôn ngữ (`en`/`vi`), `word` hoặc `latex` |
| `years_back` (5), `max_fulltext` (30) | Khoảng năm, số bài toàn văn tối đa mỗi lần chạy |
| `download_delay_seconds` (20) | Giãn cách giữa các lần tải — không giảm |
| `max_parallel_subagents` (3) | Giới hạn chi phí |
| `institutional_access` | Bật/tắt tải qua OpenAthens/db.vista |

Nếu dùng solver khác Abaqus/CalculiX, thêm lệnh tương ứng vào `allow` của `D:\Research\.claude\settings.json`
(ví dụ `"Bash(ansys:*)"`).

## 3. Chạy lần đầu

1. Mở Chrome, đăng nhập OpenAthens/db.vista (agent **không bao giờ** nhập mật khẩu), bật extension Claude in Chrome.
2. Tắt chế độ ngủ nếu chạy qua đêm: `powercfg /change standby-timeout-ac 0`.
3. Chạy thử 1–7 với 5 bài (sửa `max_fulltext: 5` trong profile):
   ```powershell
   cd D:\Research
   claude --chrome
   ```
   rồi trong Claude Code: `/auto-research cấu trúc lưới TPMS chịu va đập --until 7`.
   Kết quả: `D:\Research\auto-research\<yyyy-mm-dd>-<slug>\brief.md`.
4. Chạy đầy đủ: `/auto-research` (để trống thì dùng từ khoá profile).
5. Chạy lại từ một giai đoạn, dùng file đã có: `/auto-research --from novelty` (hoặc số 1–13).
   Thêm `--run D:/Research/auto-research/<thư mục>` để chọn lần chạy khác lần gần nhất.

Không dùng `--dangerously-skip-permissions` trên máy chính; `settings.json` đã có allowlist để không phải duyệt giữa chừng.

## 4. Thư mục mỗi lần chạy

```
D:/Research/auto-research/<yyyy-mm-dd>-<slug>/
  profile.yaml (snapshot)  state.json  DECISIONS.md
  literature/candidates.csv, prescreen.csv, shortlist.csv
  papers/*.pdf, papers/index.csv          (full | pending | abstract-only)
  extraction/*.json
  gaps/matrix.csv, candidates.md, novelty.md, novelty_G*.csv, scores.csv
  brief.md  plan.md  sim/  results/  analysis/{run_all.py,tables,figures}
  manuscript/{manuscript.md|main.tex, references.bib, numbers.csv}
  review/round-N.md
  SUMMARY.md  VERIFICATION.md  (STATUS_REPORT.md nếu cả 3 ứng viên thất bại)
```

## 5. Cấu trúc plugin

| Thành phần | Vai trò |
|---|---|
| `commands/auto-research.md` | Điều phối: đọc state.json, gọi skill theo thứ tự, `--from`, `--until`, nhánh quay lại |
| `skills/*/SKILL.md` | Hướng dẫn chi tiết từng giai đoạn, định dạng vào/ra |
| `agents/reviewer.md` | Reviewer ngữ cảnh mới, chỉ đọc bản thảo và dữ liệu |
| `hooks/hooks.json` | `Stop`: chặn kết thúc khi pipeline chưa xong hoặc cổng chưa đạt. `PostToolUse`: kiểm tra nhanh trích dẫn/số liệu khi sửa `manuscript/` |
| `scripts/state.py` | init / start / done / from / next / fallback / decision |
| `scripts/lit_search.py`, `screen.py`, `download.py`, `coverage_matrix.py`, `export_manuscript.py` | Phần cơ học của các giai đoạn |
| `scripts/verify_citations.py`, `verify_numbers.py`, `rerun_analysis.py`, `check_novelty.py`, `check_consistency.py`, `run_gates.py` | Năm cổng kiểm tra + ghi VERIFICATION.md |
| `templates/` | `profile.yaml`, `CLAUDE.md` (quy tắc tự chủ), `settings.json` (allowlist) |

Hook chỉ hoạt động khi có lần chạy đang `running` (tìm qua `state.json` ở cwd hoặc `D:/Research/auto-research/ACTIVE_RUN`);
các phiên Claude Code khác không bị ảnh hưởng. Để tránh vòng lặp vô hạn, hook nhả sau 10 lần cổng trượt (ghi rõ trong VERIFICATION.md).

## 6. Kiểm thử

```powershell
cd <plugin>
python -m unittest discover -s tests -v
```
17 kiểm thử offline (mạng giả lập bằng `AUTO_RESEARCH_HTTP_FIXTURES`): `--from`, nhánh quay lại/dừng, phiên OpenAthens
hết hạn → abstract-only và tải bù, DOI giả bị chặn, metadata sai bị chặn, con số không có nguồn bị chặn, tái lập,
nhất quán, tính mới, hook Stop.

Giả lập thủ công phiên hết hạn trong một lần chạy thật:
`python <plugin>\scripts\download.py expire --reason "test" --run D:\Research\auto-research\<thư mục>`.

## 7. Giới hạn đã biết

- Cổng số liệu miễn kiểm tra năm (1900–2100), số đánh mục (Fig. 3, Eq. (2)) và số nguyên 0–10; dùng `--strict` để kiểm cả số nhỏ.
- Cổng tái lập so sánh CSV; ảnh PNG được so qua file `<tên>.data.csv` đi kèm.
- Trích dẫn không có DOI bị loại. Trích dẫn arXiv được xác minh qua API arXiv.
- Giai đoạn 4 với nhiều bài có thể tách sang công cụ khác (Antigravity) miễn ghi đúng schema `extraction/*.json`.
