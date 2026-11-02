---
name: paper-extraction
description: Giai đoạn 4 của auto-research — trích xuất có cấu trúc mỗi bài (vật liệu, hình học, kiểu tải, phương pháp, kết quả chính, limitations, future work) thành extraction/<id>.json.
---

# Trích xuất có cấu trúc

Đầu vào: `papers/index.csv`, `papers/*.pdf`, `literature/shortlist.csv`.
Đầu ra: một file `extraction/<doi_an_toàn>.json` cho mỗi bài trong index (tên = DOI thay ký tự lạ bằng `_`).

## Schema (bắt buộc đủ khoá; giá trị không có ⇒ `null` hoặc `[]`)
```json
{
  "doi": "10.xxxx/...",
  "title": "...",
  "year": 2024,
  "basis": "full | abstract-only",
  "material": ["Ti-6Al-4V", "PLA"],
  "geometry": ["gyroid TPMS", "relative density 0.1–0.3"],
  "loading": ["quasi-static compression", "impact"],
  "method": ["experiment", "FEM (Abaqus/Explicit)", "homogenization"],
  "key_results": [
    {"quantity": "specific energy absorption", "value": 12.3, "unit": "J/g", "condition": "RD=0.2", "locator": "Table 3"}
  ],
  "limitations": ["..."],
  "future_work": ["..."],
  "validation": "mesh convergence / experiment comparison / none",
  "notes": "..."
}
```
- Chuẩn hoá nhãn về tiếng Anh, chữ thường, dạng ngắn (vd `"quasi-static compression"`), để ma trận phủ ở giai đoạn 5 gom được.
- `key_results` chỉ ghi số thực sự có trong bài, kèm `locator` (bảng/hình/trang). Bài abstract-only: chỉ số trong abstract, `locator: "abstract"`.
- Không suy diễn limitations nếu bài không nêu; có thể thêm vào `notes` với tiền tố `inferred:`.

## Cách làm
1. Đọc PDF bằng công cụ Read (tham số `pages`, tối đa 20 trang/lần; ưu tiên Abstract, Methods, Results, Conclusions).
2. Nhiều bài ⇒ chia lô, giao subagent (Task, `subagent_type: general-purpose`), tối đa `max_parallel_subagents` lô song song.
   Prompt subagent phải gồm: schema trên, danh sách file, đường dẫn đầu ra, câu "Không hỏi người dùng; không bịa số; trả về danh sách file đã ghi".
3. Kiểm tra: mỗi DOI trong index có đúng một JSON hợp lệ (`python -c "import json,glob; [json.load(open(f,encoding='utf-8')) for f in glob.glob('extraction/*.json')]"`).
