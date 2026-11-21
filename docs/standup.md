# Standup giữa phase (mỗi người một dòng, 2–3 phút)

| Phase | Người | Đã xong | Sắp làm | Vướng gì |
|---|---|---|---|---|
| 1 | Nguyễn Đình Minh (minhh25) | Lõi gather lát 1–2; 23 test mới; 2 command nhóm; tài liệu kho/snapshot/event theo PRD E–G | Bàn giao nhánh cho Hải đọc chéo, phối hợp QA/UI và kiểm chứng trên main trước tag | Quan còn TODO; ba handle chưa điền; chưa có review người thật và Ticket các phase sau |
| Phase 1 | Nguyễn Đình Vũ Hải | Hoàn thành `sim/quan` (lát 3–4), `tests/test_quan.py`, `docs/proof/phase-1/quan.md` (11/11 test xanh) | Gộp vào `main` sau khi đồng đội review và kiểm tích hợp với `gather` | Không |
| Phase 2 | Nguyễn Đình Vũ Hải | Hoàn thành `sim/quan` P2 (ưu tiên đơn cũ, đóng ca, lọc `day_plan`), `chonoi/sim/day.py` (`DaySession`, `ShopSim`), `pause`/`resumed`, `tests/test_quan_p2.py` (14/14 test xanh) | Chờ `game.contract.json` v1.1 từ Integrator để chạy smoke `--mode day --days 5` | Không |
| Phase 3 | Nguyễn Đình Vũ Hải | Gộp `main` Phase 2 đầy đủ (74/74 test xanh); hoàn thành `sim/quan` & `day` cho v1.2 (kho cá thể, hao tươi `-0.25/s`, `spoiled`, giữ lại theo `id`, `base_price` theo `fresh`, `tests/test_quan_p3.py` — 77/77 test xanh) | Chờ Integrator bật `contract_version: "1.2"` trên `game.contract.json` & `inventory.py` | Không |
