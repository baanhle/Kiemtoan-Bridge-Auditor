# Quy tắc tự chủ cho auto-research

File này được chép vào D:/Research/auto-research/CLAUDE.md. Áp dụng cho agent chính, reviewer và mọi subagent.

## 1. Không hỏi người dùng
- Không bao giờ hỏi người dùng, không dùng AskUserQuestion, không dừng để chờ xác nhận, ở bất kỳ giai đoạn nào.
- Khi mơ hồ: chọn phương án hợp lý nhất, ghi vào `DECISIONS.md` (lựa chọn, lý do, phương án bị loại) bằng
  `python "<plugin>/scripts/state.py" decision --stage N --choice "..." --reason "..." --rejected "..."`, rồi làm tiếp.
- Khi giao việc cho subagent: nhắc lại quy tắc này trong prompt.

## 2. Tự chuyển hướng thay vì dừng
- Câu hỏi nghiên cứu không khả thi (thiếu dữ liệu, không hội tụ, vượt tài nguyên) ở giai đoạn 8–10:
  `state.py fallback --reason "..."` → quay về giai đoạn 7, lấy ứng viên kế tiếp trong top 3.
- Chỉ dừng khi cả 3 ứng viên thất bại (`fallback` in ra `STOP`). Khi đó viết `STATUS_REPORT.md`
  (đã thử gì, vì sao thất bại, file đầu ra còn dùng được, đề xuất) rồi mới kết thúc.

## 3. Trạng thái và chạy lại
- Mỗi giai đoạn: `state.py start N` → ghi file đầu ra → `state.py done N --outputs ...`.
- Không xoá đầu ra của giai đoạn trước. Khi chạy `--from N`, dùng lại file đã có.

## 4. Không bịa
- Mọi trích dẫn phải có DOI xác minh qua Crossref/arXiv (`verify_citations.py`).
- Mọi con số trong bản thảo phải có dòng trong `manuscript/numbers.csv` trỏ tới file kết quả hoặc bài đã xác minh.
- Mọi bảng/hình sinh từ `analysis/run_all.py`. Không gõ tay số liệu vào bảng.
- Không trích nội dung toàn văn của bài chỉ có abstract như thể đã đọc toàn văn.

## 5. Tải bài (bắt buộc)
- Chỉ tải bài trong `literature/shortlist.csv`; không vượt `max_fulltext`; giãn cách `download_delay_seconds`.
- Không bao giờ nhập mật khẩu, không điền form đăng nhập, không bấm "Sign in". Gặp trang đăng nhập ⇒ phiên hết hạn ⇒
  `download.py expire --reason "..."` và chạy tiếp.
- Không dùng tính năng "tải tất cả"/bulk export của nhà xuất bản.

## 6. Môi trường
- Windows + PowerShell. Dùng `python` (không `python3`), đường dẫn dạng `D:/Research/...`, không dùng lệnh chỉ có trên Linux
  (`grep`, `sed`, `rm -rf`...); dùng công cụ Read/Write/Edit/Glob/Grep của Claude Code hoặc Python.
