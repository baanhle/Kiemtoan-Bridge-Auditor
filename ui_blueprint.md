# Bản Mô Tả Chi Tiết Giao Diện (UI Blueprint) 
*Phục vụ cho việc cấp Prompt cho các tool gen code UI (như Stitch-MCP)*

## 1. Bố cục tổng thể (Overall Layout)
- **Phong cách:** Hiện đại, Kỹ thuật (Engineering but sleek), Clean UI, Hỗ trợ Dark/Light mode toggle. Sử dụng CSS Grid hoặc Flexbox linh hoạt.
- **Cấu trúc màn hình:** Chia làm hai phần chính khi dùng trên Desktop (Split View):
  - **Left Panel (55% width):** Vùng Nhập liệu (Form Panel) - Có thanh cuộn (scrollable).
  - **Right Panel (45% width):** Vùng Hiển thị Kết toán & Trợ lý AI (Results & AI Panel) - Fixed/Sticky để luôn nhìn thấy khi cuộn form bên trái.

## 2. Chi tiết Thành phần (Components Breakdown)

### A. Header (Thanh Điều Hướng Trên Cùng)
- **Title:** "Kiểm Toán Mặt Cắt Cầu Pro"
- **Author Information:** "PGS.TS. Lê Bá Anh - Trường Đại học GTVT"
- **Standard Selector (Tâm điểm):** Dropdown lớn chọn Tiêu chuẩn: `TCVN 11823:2017`, `AASHTO LRFD`, `Eurocode`. 
- **Theme Toggle:** Nút chuyển đổi Light/Dark (giữ lại tính năng này cho bộ máy).

### B. Left Panel - Vùng Nhập Liệu (Inputs Area)
1. **Card 1: Thông số Hình học Mặt cắt (Geometry Profile)**
   - Diện tích mặt cắt (A) `[cm²]`
   - Moment quán tính (I) `[cm⁴]`
   - Chiều cao dầm cấu tạo (h) `[cm]`
   - Bề rộng cánh trên (Top Flange Width) `[cm]`
   - Bề rộng cánh dưới (Bottom Flange Width) `[cm]`
   - Bề dày bản nắp / đáy (Slab Thickness) `[cm]`
   - Các thông số hình học bổ trợ khác.

2. **Card 2: Cấu tạo Cốt thép & Cáp Dự ứng lực (Reinforcement)**
   - **Cốt thép thường (Regular Rebar):** Đường kính, Số thanh, Vị trí trọng tâm.
   - **Cáp Dự ứng lực (PT Tendons):**
     - Số lượng bó cáp (No. of Tendons).
     - Số lượng tao cáp trên mỗi bó (Strands per Tendon).
     - Khoảng cách / Vị trí trọng tâm cáp dự ứng lực (Eccentricity).

3. **Card 3: Tải trọng & Nội lực (Internal Forces)**
   - Moment uốn (Mu) `[kN.m]`
   - Lực cắt (Vu) `[kN]`
   - Lực dọc (Nu) `[kN]`

4. **Action Buttons (Cuối Left Panel)**
   - Nút **"CHẠY KIỂM TOÁN"** (Màu xanh, Primary).
   - Nút **"XÓA DỮ LIỆU"** (Nút phụ, Secondary).

### C. Right Panel - Vùng Kết Quả & Trợ Lý AI
Gồm hai màn hình chính chuyển đổi qua Tab (Result Tab | Smart Assistant Tab):

**Tab 1: Results & Reports (Kết quả kiểm toán)**
- **Status Banner:** Hiển thị thẻ lớn màu Xanh lục (PASSED) hoặc Đỏ (FAILED).
- **Sumary Table:** Bảng tóm tắt:
  - Sức kháng uốn: `<phi>Mn` so với `Mu` -> Tỉ lệ (%)
  - Sức kháng cắt: `<phi>Vn` so với `Vu` -> Tỉ lệ (%)
- **Export Buttons:** Hai nút kề nhau (Icon Word và Icon PDF): **"Tải Báo cáo Word" / "Tải Báo cáo PDF"**.

**Tab 2: Trợ Lý AI (AI Smart Assistant)**
- **Khối Cài Đặt LLM (Settings Block):**
  - Dropdown **Provider**: Lựa chọn `OpenAI`, `Claude`, `Gemini`.
  - Dropdown **Model**: Cập nhật động theo Provider (VD: chọn OpenAI thì xổ ra `gpt-4o`, `gpt-4-turbo`).
  - Input Feature: Ô nhập **API Key** (dạng password, có nút cự li con mắt để xem). Có kèm dòng chữ nhỏ: *"Key chỉ lưu ở RAM browser, không lưu trữ máy chủ."*
- **Khối Chatbot (Chat UI):**
  - Khung hiển thị tin nhắn giống Messenger/ChatGPT.
  - Sau khi User ấn "Run Audit", hệ thống tự bắn 1 tin nhắn hệ thống vào khung Chat báo cáo tính trạng đạt/không đạt.
  - Ô chat ở dưới để kĩ sư gõ: *"Tại sao Sức kháng chịu cắt lại bị thiếu 10%?"*, AI sẽ trả lời giải thích số liệu.

## 3. Micro-Interactions & Styling
- Validation: Hỗ trợ báo lỗi màu đỏ (border-red) nến kĩ sư nhập số âm vào ô Diện Tích hoặc Bỏ trống ô API key khi chat.
- Tooltips: Đưa chuột vào biểu tượng `[?]` kế bên biến số 'Ixx' sẽ hiện công thức nhắc nhở.
- Loading states: Thấy Spinner hoặc loading skeleton ở Right Panel lúc gọi API.
