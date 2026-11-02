---
name: novelty-check
description: Giai đoạn 6 của auto-research — với mỗi ứng viên khoảng trống, chạy một vòng tìm kiếm riêng để kiểm tra đã có công bố chưa, loại ứng viên trùng, giữ bằng chứng trong gaps/novelty.md.
---

# Kiểm tra tính mới

Với từng ứng viên `G<n>` trong `gaps/candidates.md`:
1. Soạn 3–5 truy vấn khác nhau (thuật ngữ đồng nghĩa, tổ hợp vật liệu+tải+phương pháp chính xác).
2. Chạy, ghi ra file riêng để giữ bằng chứng:
   ```
   python "${CLAUDE_PLUGIN_ROOT}/scripts/lit_search.py" --run "<run>" --query "q1" --query "q2" --query "q3" --per-source 25 --out gaps/novelty_G<n>.csv
   ```
   (Không giới hạn năm cho bước này nếu cần: thêm truy vấn bằng WebSearch và ghi kết quả.)
3. Đọc tiêu đề/abstract các bài trả về có độ tương đồng cao nhất (tối đa 30). Phán quyết:
   - `novel`: không bài nào trả lời đúng câu hỏi;
   - `partially-novel`: có bài gần nhưng khác ít nhất một chiều quan trọng (vật liệu/tải/phương pháp/thang đo) — nêu rõ chiều khác;
   - `published`: đã có bài trả lời ⇒ loại.
4. Ghi `gaps/novelty.md`, mỗi ứng viên một khối đúng định dạng (cổng Tính mới đọc định dạng này):
   ```
   ### G1
   Verdict: novel
   - query: "gyroid TPMS concrete interpenetrating impact" | db: openalex+s2+crossref+arxiv | date: 2026-11-02 | hits: 14
   - query: ... | db: ... | date: ... | hits: ...
   - query: ... | db: ... | date: ... | hits: ...
   Closest work: DOI — khác ở ...
   Evidence file: gaps/novelty_G1.csv
   ```
5. Nếu mọi ứng viên đều `published` ⇒ quay lại giai đoạn 5 (`state.py from 5`) với tiêu chí rộng hơn, ghi DECISIONS.md.
