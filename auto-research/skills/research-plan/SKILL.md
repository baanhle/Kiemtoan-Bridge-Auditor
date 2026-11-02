---
name: research-plan
description: Giai đoạn 8 của auto-research — lập plan.md cho câu hỏi đã chọn - mô hình, tham số, ma trận mô phỏng, tiêu chí kiểm chứng (hội tụ lưới, so sánh với kết quả đã công bố), ngân sách tài nguyên và điều kiện bỏ cuộc.
---

# Kế hoạch nghiên cứu

Đọc `brief.md`, `extraction/*.json` của các bài liên quan, `profile.yaml`. Viết `plan.md` gồm:

1. **Mô hình**: hình học (kích thước, cách sinh — vd hàm ẩn TPMS), vật liệu (mô hình cấu thành + tham số, mỗi tham số
   có nguồn DOI+locator), điều kiện biên, tải, phần tử, solver (chỉ dùng công cụ trong profile).
2. **Tham số khảo sát** và **ma trận mô phỏng** (bảng: id, tham số, giá trị). Ghi vào `sim/matrix.csv`.
3. **Kiểm chứng**:
   - Hội tụ lưới: ≥ 3 mức lưới, tiêu chí sai khác < 2–5% cho đại lượng chính.
   - So sánh với ít nhất một kết quả đã công bố (DOI, locator, giá trị, sai số chấp nhận được).
4. **Ngân sách**: ước tính thời gian/mô phỏng × số mô phỏng ≤ `compute`. Vượt ⇒ thu gọn ma trận trước; vẫn vượt ⇒ không khả thi.
5. **Đầu ra kỳ vọng**: các đại lượng sẽ báo cáo, file kết quả dự kiến trong `results/`.
6. **Điều kiện bỏ cuộc** (kích hoạt nhánh quay lại): thiếu tham số vật liệu không thể lấy từ tài liệu; không hội tụ sau
   3 biện pháp (tinh lưới, giảm bước, ổn định hoá); vượt ngân sách sau khi thu gọn; kiểm chứng sai lệch > 30% không giải thích được.

Nếu ngay ở bước này câu hỏi đã không khả thi: `state.py fallback --reason "..."` và quay về giai đoạn 7.
