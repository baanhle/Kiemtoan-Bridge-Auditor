---
name: simulation
description: Giai đoạn 9 của auto-research — viết và chạy script mô phỏng/tính toán tái lập được theo plan.md (sinh hình học, input solver, chạy, hậu xử lý ra results/), kiểm tra hội tụ lưới, kích hoạt nhánh quay lại khi không khả thi.
---

# Mô phỏng và tính toán

## Quy ước thư mục
```
sim/
  matrix.csv            # từ plan.md
  params.yaml           # mọi tham số đầu vào (nguồn ghi trong comment: DOI + locator)
  build_model.py        # sinh hình học/lưới/input deck từ params.yaml
  run_all.py            # chạy toàn bộ ma trận (bỏ qua case đã có kết quả hợp lệ ⇒ chạy tiếp được)
  postprocess.py        # đọc output solver → results/
results/
  <case_id>.json        # đại lượng chính mỗi case
  summary.csv           # tổng hợp toàn bộ ma trận
  convergence.csv       # nghiên cứu hội tụ lưới
  validation.csv        # so sánh với kết quả đã công bố
  run_log.csv           # case, trạng thái, thời gian chạy, ghi chú
```

## Quy tắc
- Python thuần + công cụ trong profile. Gọi solver bằng `subprocess` với danh sách đối số (không chuỗi shell), đường dẫn pathlib.
  Ví dụ Abaqus trên Windows: `subprocess.run(["abaqus", f"job={job}", "input=...", "cpus=4", "interactive"], shell=True, cwd=...)`
  (`abaqus` là .bat nên cần `shell=True` trên Windows).
- Seed cố định cho mọi thứ ngẫu nhiên. Không sửa tay file kết quả.
- Chạy hội tụ lưới TRƯỚC ma trận chính. Không hội tụ ⇒ thử lần lượt: tinh lưới, giảm bước thời gian, ổn định hoá/
  phần tử khác. Vẫn không ⇒ `state.py fallback --reason "không hội tụ: ..."`.
- Ước tính thời gian sau 2–3 case đầu; nếu tổng vượt `compute` ⇒ thu gọn ma trận (ghi DECISIONS.md), vẫn vượt ⇒ fallback.
- Không có solver FEM nào chạy được trên máy ⇒ chỉ được dùng mô hình giải tích/số tự viết nếu plan cho phép; nếu không ⇒ fallback.
- Chạy dài: chạy `run_all.py` nền và kiểm tra `results/run_log.csv` định kỳ, không hỏi người dùng.
