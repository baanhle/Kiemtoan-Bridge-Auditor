---
name: literature-search
description: Giai đoạn 1–2 của auto-research — truy vấn OpenAlex, Semantic Scholar, Crossref, arXiv theo từ khoá profile, rồi sàng lọc abstract ra shortlist. Dùng khi /auto-research đang ở giai đoạn 1 hoặc 2.
---

# Tìm tài liệu (1) và sàng lọc abstract (2)

Không hỏi người dùng. Mơ hồ ⇒ quyết định và ghi `state.py decision`.

## Giai đoạn 1 — Tìm
1. Đọc `<run>/profile.yaml`. Nếu có chủ đề trong state.json (`topic`) khác từ khoá profile, soạn 2–4 truy vấn
   tiếng Anh từ chủ đề (thuật ngữ chuẩn trong lĩnh vực, có từ đồng nghĩa) và ghi DECISIONS.md.
2. Chạy:
   ```
   python "${CLAUDE_PLUGIN_ROOT}/scripts/lit_search.py" --run "<run>" --query "q1" --query "q2" --per-source 50
   ```
   Không có `--query` thì dùng `search_queries`/`keywords_en` trong profile.
3. Đọc `logs/search.log`. Nếu một nguồn lỗi, vẫn tiếp tục với nguồn khác. Nếu tổng < 20 bài, nới truy vấn (bỏ bớt
   ràng buộc) và chạy lại một lần; ghi DECISIONS.md.
4. Đầu ra: `literature/candidates.csv` (doi, title, year, authors, venue, abstract, citations, source, url, query).

## Giai đoạn 2 — Sàng lọc
1. `python "${CLAUDE_PLUGIN_ROOT}/scripts/screen.py" --run "<run>"` → `literature/prescreen.csv` (xếp theo kw_score).
2. Đọc tiêu đề + abstract của tối đa 150 bài đầu. Với mỗi bài điền cột `relevance` (0–10) và `reason` (≤ 15 từ):
   - 9–10: trực tiếp về chủ đề, có phương pháp/kết quả định lượng dùng được;
   - 5–8: liên quan (cùng vật liệu hoặc cùng kiểu tải/phương pháp);
   - 0–4: lạc đề, review quá chung, không có abstract và tiêu đề không rõ.
   Ưu tiên đa dạng (không để một nhóm tác giả chiếm > 30% shortlist). Ghi lại file bằng Python (csv module, UTF-8).
3. `python "${CLAUDE_PLUGIN_ROOT}/scripts/screen.py" finalize --run "<run>"` → `literature/shortlist.csv`
   (relevance ≥ 5, tối đa `max_fulltext`).
4. Kiểm tra số dòng shortlist > 0; nếu 0 thì hạ ngưỡng xuống 4 bằng cách chỉnh điểm, ghi DECISIONS.md.
