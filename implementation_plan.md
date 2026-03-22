# Kế Hoạch Triển Khai: Ứng Dụng Kiểm Toán Mặt Cắt Cầu

Cung cấp công cụ phục vụ kiểm toán mặt cắt cầu chuyên sâu theo 3 tiêu chuẩn cốt lõi: TCVN, AASHTO, Eurocode. 

## User Review Required

> [!IMPORTANT]
> Sếp vui lòng xem lại bản kế hoạch Version 2 đã được cập nhật sâu sát theo đúng yêu cầu: sử dụng LibreOffice để convert PDF, định nghĩa rõ input hình học, tách riêng template cho từng tiêu chuẩn, và làm rõ chính sách bảo mật của AI.

## Proposed Changes

### 1. Kiến Trúc Lõi Tính Toán & Dữ Liệu
**Thông số đầu vào nhận từ UI:**
- **Thông số hình học:** Tiết diện, moment quán tính, chiều cao dầm, bề rộng đáy, bề rộng nắp.
- **Cốt thép:** Số lượng cốt thép dự ứng lực, số lượng cốt thép thường, và các khoảng cách tương ứng.
- **Nội lực:** Người dùng tự nhập các giá trị moment, lực cắt, lực dọc tương ứng.

**Pipeline xử lý tính toán:**
1. **Validation & Unit Converter:** Module chuẩn hóa đơn vị và bắt lỗi nhập liệu (bắt buộc phải có để tránh rủi ro người dùng nhập sai thứ nguyên).
2. **Core Engine:** Khối tính toán độc lập, tuân thủ tuyệt đối các công thức của TCVN, AASHTO, hoặc Eurocode (lựa chọn từ UI).

### 2. Định Dạng Báo Cáo (Default: Word)
- Báo cáo **Mặc định là Microsoft Word**.
- **Cơ chế Template:** Hệ thống sử dụng thư viện `docxtpl` kết hợp với các **Template Word được thiết kế riêng biệt cho từng tiêu chuẩn** (TCVN, AASHTO, Eurocode). Đảm bảo thuật ngữ, ký hiệu toán học và cấu trúc báo cáo "chuẩn chỉ" theo đúng luật định.
- **Tùy chọn xuất PDF:** Gọi trực tiếp công cụ `LibreOffice headless` (chạy ngầm) để convert file Word vừa sinh ra sang định dạng PDF. (Cách này bảo toàn 100% format bảng biểu, ngắt trang của Word tốt hơn là dùng WeasyPrint). PDF xuất ra có thể nhúng Watermark chống sao chép.

### 3. Phương Án Triển Khai (Deployment Web / Desktop)
Kiến trúc tách rời cho phép tuỳ biến phương thức đóng gói dựa vào nhu cầu:
- **Offline / Standalone (Độc lập):** Đóng gói Frontend + Backend thành một cấu trúc Python + Local Web UI hoặc Tauri (Rust) tạo thành file chạy trần trên máy tính Sếp mà không cần kết nối mạng.
- **Online / VPS (Dùng chung cho team/sinh viên):** Bọc toàn bộ source code vào Docker Container để quăng lên Host/VPS, bất kỳ ai có link đều truy cập được.

### 4. Tích Hợp Tùy Chọn AI (Smart Assistant - Optional)
- Nhằm giải thích số liệu và hướng dẫn kỹ sư phân tích các chỉ số không đạt. Tính năng này đóng vai trò "Trợ giảng" chứ **TUYỆT ĐỐI KHÔNG** can thiệp hay thay thế công thức tính toán lõi của hệ thống.
- **Đa dạng Provider & Model:** Người dùng có quyền lựa chọn hệ sinh thái AI mình muốn: **OpenAI, Claude (Anthropic), hoặc Gemini (Google)**. 
- Khi chọn Provider nào, UI sẽ hiển thị ô **nhập API Key tương ứng** và danh sách Dropdown để **lựa chọn Model** (ví dụ: `gpt-4o`, `claude-3-5-sonnet`, `gemini-1.5-pro`).
- **Chính sách Quyền riêng tư (Privacy Policy):** Cụm AI chỉ được kích hoạt khi User tự nguyện dán API Key. Key chỉ được xử lý tạm thời trên RAM memory, hệ thống **không lưu database, không tạo cache, không đẩy log file đính kèm API Key** nhằm đảm bảo tuyệt đối tài sản số của người dùng.
