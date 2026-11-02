---
name: gap-finding
description: Giai đoạn 5 của auto-research — dựng ma trận phủ vật liệu × kiểu tải × phương pháp từ extraction/*.json, tìm ô trống, kết quả mâu thuẫn và future work lặp lại, ra 5–10 ứng viên khoảng trống nghiên cứu.
---

# Tìm khoảng trống

1. Dựng ma trận phủ:
   ```
   python "${CLAUDE_PLUGIN_ROOT}/scripts/coverage_matrix.py" --run "<run>"
   ```
   → `gaps/matrix.csv` (material, loading, method, n_papers, dois) và `gaps/future_work.csv` (cụm future work, số lần lặp).
   Script chỉ gom nhãn; bạn có thể chuẩn hoá nhãn đồng nghĩa (gộp "Abaqus FEM" và "FEM") bằng cách sửa JSON rồi chạy lại.
2. Tìm ba loại tín hiệu:
   - **Ô trống**: tổ hợp hợp lý về vật lý mà `n_papers = 0` trong khi hàng/cột lân cận dày.
   - **Mâu thuẫn**: cùng đại lượng, điều kiện tương tự, kết quả khác nhau đáng kể (> 20%) giữa các bài — trích `key_results`.
   - **Future work lặp lại**: cụm xuất hiện ở ≥ 2 bài.
3. Viết `gaps/candidates.md`, 5–10 ứng viên, mỗi ứng viên:
   ```
   ### G1 — <tiêu đề ngắn>
   - Câu hỏi nghiên cứu: ...
   - Loại tín hiệu: ô trống | mâu thuẫn | future work
   - Bằng chứng: DOI1 (locator), DOI2 ...
   - Phương pháp dự kiến: ...  (phải dùng công cụ trong profile)
   - Ước tính tài nguyên: số mô phỏng × thời gian/mô phỏng
   ```
4. Ít hơn 5 ứng viên ⇒ ghi DECISIONS.md và nới tiêu chí (ví dụ thêm biến thể hình học hoặc tham số).
