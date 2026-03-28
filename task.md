# Danh sách công việc: Ứng dụng kiểm toán mặt cắt cầu

## 1. Giai đoạn Lên kế hoạch (Planning)
- [x] Lập kế hoạch kiến trúc phần mềm và chọn công nghệ (Implementation Plan).
- [x] Sếp duyệt kế hoạch. (Approved & Deployed)

## 2. Giai đoạn Xây dựng Lõi Tính Toán (Core Engine - Backend)
- [ ] Thiết lập backend kiến trúc module hóa.
- [ ] Xây dựng cấu trúc dữ liệu mô tả mặt cắt:
  - Thông số hình học: diện tích mặt cắt (A), moment quán tính (I), chiều cao dầm, bề rộng nắp, bề rộng đáy, v.v.
  - Cốt thép: Số lượng & khoảng cách cốt thép thường, cốt thép dự ứng lực.
  - Nội lực: Các giá trị nội lực do người dùng tự nhập.
- [ ] Viết module **Chuẩn hóa đơn vị và validation dữ liệu** (cực kỳ quan trọng để tránh lỗi nhập sai đơn vị).
- [ ] Viết thuật toán tính toán theo chuẩn TCVN 11823:2017 (Core scope).
- [ ] Viết thuật toán tính toán theo chuẩn AASHTO LRFD (Core scope).
- [ ] Viết thuật toán tính toán theo chuẩn Eurocode (Core scope).

## 3. Giai đoạn Báo Cáo (Report Generation - Template Driven)
- [ ] Soạn thảo các **Template Word riêng biệt cho từng tiêu chuẩn** (TCVN, AASHTO, Eurocode) khớp với cấu trúc và thuật ngữ của từng tiêu chuẩn.
- [ ] Xây dựng module xuất định dạng mặc định là file Word thông qua `docxtpl`.
- [ ] Tích hợp `LibreOffice headless` để convert chuẩn xác từ Word sang PDF (hỗ trợ đóng dấu bản quyền).

## 4. Giai đoạn Giao Diện (Frontend / UI Blueprint)
- [x] Lên bản nháp thiết kế Layout chi tiết cắt lớp (UI Blueprint) chuẩn bị dùng cho AI sinh giao diện.
- [x] Khởi tạo Project trên Stitch-MCP.
- [x] Xây dựng giao diện Desktop Light Mode Tiếng Việt chi tiết (2 cột).
- [x] Tạo option dropdown cho phép người dùng **chọn tiêu chuẩn kiểm toán**.
- [ ] Giao diện hiển thị nhanh kết quả (Pass/Fail) và cung cấp nút tải Báo cáo Word/PDF.

## 5. Giai đoạn Tích hợp AI (Smart Assistant - Optional)
- [ ] Lập trình mục Policy & Security Privacy rõ ràng trên UI.
- [ ] Xây dựng UI cho phép người dùng **lựa chọn Provider (OpenAI, Claude, Gemini)**.
- [ ] Thêm tính năng **chọn Model tương ứng** với Provider đã chọn (VD: gpt-4o, claude-3.5-sonnet, gemini-1.5-pro).
- [ ] Tạo ô nhập API Key AI an toàn (chỉ xử lý realtime trên bộ nhớ Runtime, không lưu vết, không log).
- [ ] Tích hợp Prompt Engineering để AI nhận kết quả tính và phân tích/kết luận mà không "can thiệp" hay "tự phịa" số liệu toán học.

## 6. Giai đoạn Tích hợp & Kiểm thử (Integration & Verification)
- [ ] Lắp ghép Frontend, Backend Python, Core Engine và LibreOffice Module.
- [ ] Thử nghiệm với các bài toán mẫu (Benchmark) để rà soát đơn vị tính và format báo cáo.

## 7. Giai đoạn Triển Khai (Deployment Ops)
- [ ] Biên dịch Desktop Standalone: Python backend + Local Web UI tạo thành file tự động chạy không cần cài cắm cho Môi trường Offline.
- [x] Viết `Dockerfile` phục vụ nhu cầu đưa bộ công cụ lên VPS khi cần. (Render Backend)
- [x] Triển khai Cloud (Live):
  - [x] Push mã nguồn lên Git: [Kiemtoan-Bridge-Auditor](https://github.com/baanhle/Kiemtoan-Bridge-Auditor.git)
  - [x] Frontend: Live on **Vercel**
  - [x] Backend: Live on **Render** (Dockerized)

---
*Cập nhật lần cuối: 2026-03-28 bởi Bé Nhi (Thư ký)*
