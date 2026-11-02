---
name: analysis
description: Giai đoạn 10 của auto-research — phân tích kết quả mô phỏng; mọi bảng và hình sinh từ analysis/run_all.py tất định (kèm file .data.csv cho mỗi hình) để cổng Tái lập chạy lại được.
---

# Phân tích

## Hợp đồng với cổng Tái lập
- Một điểm vào duy nhất: `analysis/run_all.py`, chạy từ thư mục chạy (`cwd = <run>`), chỉ đọc `results/` (và `extraction/` nếu
  so sánh tài liệu), ghi:
  - `analysis/tables/<tên>.csv` — mỗi bảng trong bản thảo một file;
  - `analysis/figures/<tên>.png` (+ `.pdf` nếu LaTeX) và `analysis/figures/<tên>.data.csv` — dữ liệu vẽ đúng hình đó.
- Tất định: seed cố định, sắp xếp ổn định, `matplotlib.use("Agg")`, không ghi thời gian hiện tại vào CSV,
  làm tròn số trong CSV tới số chữ số sẽ dùng trong bản thảo.
- Không mô phỏng lại trong phân tích (đó là giai đoạn 9).

## Nội dung tối thiểu
1. Bảng hội tụ lưới và bảng kiểm chứng với kết quả đã công bố.
2. Bảng tổng hợp đại lượng chính theo tham số.
3. 3–6 hình: xu hướng theo tham số, so sánh, (nếu có) trường ứng suất/biến dạng từ ảnh solver đã lưu trong results/.
4. Phân tích độ nhạy hoặc khoảng tin cậy nếu có lặp.
5. `analysis/findings.md`: 3–6 phát hiện chính, mỗi phát hiện kèm file bảng/hình và con số (copy từ CSV, không gõ tay).

Phân tích cho thấy kết quả vô nghĩa hoặc kiểm chứng sai lệch không thể giải thích ⇒ `state.py fallback --reason "..."`.

Kiểm tra trước khi `done 10`: `python "${CLAUDE_PLUGIN_ROOT}/scripts/rerun_analysis.py" --run "<run>"` phải PASS.
