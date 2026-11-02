---
name: manuscript-writing
description: Giai đoạn 11 của auto-research — viết bản thảo theo định dạng tạp chí trong profile (Markdown→Word hoặc LaTeX), kèm references.bib đã xác minh DOI và manuscript/numbers.csv ghi nguồn cho mọi con số.
---

# Viết bản thảo

## File
- Word: `manuscript/manuscript.md` (Pandoc Markdown, cú pháp pandoc-crossref) → xuất `.docx` bằng `export_manuscript.py`.
- LaTeX: `manuscript/main.tex` (dùng class của tạp chí nếu có, ví dụ `elsarticle`), có thể `\input` các file con.
- `manuscript/references.bib` — CHỈ các bài có DOI. Lấy metadata từ Crossref (`https://api.crossref.org/works/<doi>`),
  không gõ tay tiêu đề/tác giả/năm.
- `manuscript/numbers.csv` — cột: `value,unit,context,source_type,source,locator`.
- Hình: tham chiếu trực tiếp `../analysis/figures/<tên>.png` (hoặc chép vào `manuscript/figures/`).

## Quy ước tham chiếu
- Markdown: `![Caption](../analysis/figures/x.png){#fig:x}`, bảng có `: Caption {#tbl:y}`, phương trình `$$...$$ {#eq:z}`,
  trích dẫn `[@key]`, tham chiếu `@fig:x`, `@tbl:y`, `@eq:z`.
- LaTeX: `\label{fig:x}`, `\ref{fig:x}`, `\eqref{eq:z}`, `\cite{key}`.
- Hình/bảng đánh số theo thứ tự nhắc lần đầu; mọi hình/bảng phải được nhắc trong văn bản.

## Quy tắc số liệu (cổng Số liệu)
- Mọi con số (trừ năm, số đánh mục, số nguyên 0–10 dùng để đếm) phải có một dòng trong `numbers.csv`:
  - kết quả của mình: `source_type=result`, `source=analysis/tables/x.csv` (hoặc `results/...`), giá trị phải có trong file;
  - tham số đầu vào: `source_type=setup`, `source=sim/params.yaml`;
  - số từ tài liệu: `source_type=paper`, `source=<DOI>`, `locator=Table 2` — DOI phải nằm trong references.bib.
- Viết số đúng như trong file nguồn (làm tròn được, nhưng không đổi đơn vị mà không có dòng nguồn riêng).

## Cấu trúc
Title, Abstract (≤ 250 từ), Keywords, 1 Introduction (khoảng trống + câu hỏi từ brief.md), 2 Methods (theo plan.md),
3 Verification (hội tụ lưới, so sánh đã công bố), 4 Results, 5 Discussion (giới hạn, gồm việc một số bài chỉ đọc
abstract), 6 Conclusions, Data availability, References. Ngôn ngữ theo `manuscript_language`.

## Kiểm tra trước khi `done 11`
```
python "${CLAUDE_PLUGIN_ROOT}/scripts/verify_citations.py" --run "<run>"
python "${CLAUDE_PLUGIN_ROOT}/scripts/verify_numbers.py" --run "<run>"
python "${CLAUDE_PLUGIN_ROOT}/scripts/check_consistency.py" --run "<run>"
```
Hook PostToolUse cũng chạy hai kiểm tra đầu sau mỗi lần sửa file trong manuscript/ và báo lỗi ngay.
