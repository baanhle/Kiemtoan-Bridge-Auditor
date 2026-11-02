---
name: question-selection
description: Giai đoạn 7 của auto-research — chấm điểm các ứng viên còn lại theo tính mới, khả thi với công cụ trong profile, khớp chuyên môn, khả năng đăng; chọn top 1, lưu top 3 vào brief.md. Cũng dùng khi quay lại từ giai đoạn 8–10 để lấy ứng viên kế tiếp.
---

# Chấm điểm và chọn câu hỏi

1. Lấy các ứng viên có `Verdict: novel | partially-novel` trong `gaps/novelty.md`.
2. Chấm 1–5 từng tiêu chí, có trọng số:
   | Tiêu chí | Trọng số | Căn cứ |
   |---|---|---|
   | Tính mới | 0.30 | novel=5, partially-novel=3–4 tuỳ khoảng cách với closest work |
   | Khả thi | 0.30 | công cụ trong `profile.tools`, ước tính tài nguyên ≤ `compute`, có dữ liệu kiểm chứng đã công bố |
   | Khớp chuyên môn | 0.20 | `researcher.expertise` |
   | Khả năng đăng | 0.20 | phạm vi `target_journals`, mức độ quan tâm (trích dẫn của bài liên quan) |
   Điểm = Σ trọng số × điểm. Hoà ⇒ ưu tiên khả thi cao hơn.
3. Ghi `gaps/scores.csv` (id, novelty, feasibility, expertise, publishability, total, rationale) — điểm ổn định giữa các lần quay lại.
4. Đọc `candidate_index` trong state.json (0 = top 1; 1 = top 2 sau một lần fallback; 2 = top 3).
   Chọn ứng viên ở vị trí đó trong top 3. Ứng viên đã thất bại (xem `fallbacks` trong state.json) không được chọn lại.
5. Viết `brief.md` (định dạng bắt buộc — cổng Tính mới kiểm tra):
   ```
   # Brief — <tiêu đề câu hỏi>
   Selected: G<n>
   Candidate index: <k>

   ## Câu hỏi nghiên cứu
   ...
   ## Giả thuyết và đóng góp dự kiến
   ...
   ## Top 3
   1. G.. — điểm .. — một dòng lý do
   2. ...
   3. ...
   ## Bằng chứng tính mới
   - query: ... | db: ... | date: YYYY-MM-DD | hits: N
   - (≥ 3 dòng, chép từ gaps/novelty.md của ứng viên được chọn)
   Closest work: ...
   ## Khả thi
   Công cụ, ước tính số mô phỏng và thời gian, dữ liệu kiểm chứng (DOI + locator).
   ```
6. Ghi DECISIONS.md: ứng viên được chọn, lý do, các ứng viên bị loại.
