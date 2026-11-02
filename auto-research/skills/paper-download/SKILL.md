---
name: paper-download
description: Giai đoạn 3 của auto-research — tải toàn văn các bài trong shortlist qua Unpaywall/arXiv, phần còn thiếu qua OpenAthens/db.vista bằng Claude in Chrome; tôn trọng giới hạn và giãn cách, xử lý phiên hết hạn bằng cách đánh dấu abstract-only.
---

# Tải toàn văn

## Quy tắc bắt buộc (vi phạm có thể khiến cả trường bị khoá)
- CHỈ tải bài có trong `literature/shortlist.csv`. Không quá `max_fulltext` bài 'full'.
- Giãn cách ≥ `download_delay_seconds` giữa hai lần tải (script `download.py next-delay` cho biết số giây cần chờ;
  dùng `python -c "import time; time.sleep(N)"` để chờ).
- KHÔNG BAO GIỜ nhập mật khẩu, mã OTP, bấm đăng nhập, hay điền form xác thực. Không dùng chức năng tải hàng loạt.
- Không hỏi người dùng.

## Bước 1 — Nguồn mở
```
python "${CLAUDE_PLUGIN_ROOT}/scripts/download.py" oa --run "<run>"
```
Tạo/cập nhật `papers/index.csv` (doi, title, source, status ∈ {full, pending, abstract-only}, file, note, updated).
Bài 'abstract-only' từ lần chạy trước (phiên hết hạn) được thử tải bù tự động.

## Bước 2 — Qua trường bằng Chrome (chỉ khi `institutional_access.enabled` và có công cụ `mcp__claude-in-chrome__*`)
1. `python ".../download.py" pending --run "<run>"` → JSON danh sách `todo` (đã cắt theo chỗ trống còn lại).
2. Nếu không có công cụ Chrome (không chạy với `--chrome`): `download.py expire --reason "không có Chrome"` và sang giai đoạn 4.
3. Với từng bài, tuần tự (không song song):
   a. Chờ `next-delay` giây.
   b. Mở tab mới tới `https://doi.org/<doi>` (hoặc qua `start_url` của portal nếu nhà xuất bản yêu cầu).
   c. Đọc trang. **Phát hiện phiên hết hạn**: URL/tiêu đề chứa `login`, `signin`, `openathens.net/...auth`,
      `idp`, `Shibboleth`, hoặc trang có ô mật khẩu ⇒ DỪNG thao tác Chrome ngay, chạy
      `download.py expire --reason "OpenAthens session expired at <doi>"` (mọi bài còn pending → abstract-only, sẽ tải bù lần sau),
      rồi kết thúc giai đoạn 3 bình thường.
   d. Nếu có nút/link "Download PDF" của chính bài đó: bấm một lần, file vào thư mục Downloads; chép sang
      `papers/<tên trong todo.file>` bằng Python (`shutil.copy`), rồi
      `download.py mark --doi <doi> --status full --source openathens --file papers/<tên>`.
      Script từ chối nếu file không phải PDF.
   e. Không có quyền truy cập (paywall, "Purchase"): `download.py mark --doi <doi> --status abstract-only --note "no access"`.
4. Đóng tab đã mở.

## Bước 3 — Ghi chú
- Mọi bài không 'full' sẽ được liệt kê trong VERIFICATION.md. Giai đoạn 4 dùng abstract cho các bài này và đánh dấu.
- `state.py done 3 --outputs papers/index.csv`.

## Giả lập phiên hết hạn (kiểm thử)
`download.py expire --reason "test"` cho kết quả giống hệt bước 3c: các bài pending → abstract-only, pipeline chạy tiếp.
