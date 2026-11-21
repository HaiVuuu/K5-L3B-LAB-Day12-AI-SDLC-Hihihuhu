# Ma trận truy vết Phase 2 — Một ngày ở chợ nổi (Test Contract v1.1)

| AC | Cách kiểm chứng | Bằng chứng | Kết quả (đạt / chưa đạt) |
|---|---|---|---|
| AC-P2-01: Số chuẩn v1.1 (`N5–N6`, `ca_keo`, `keo_neo`, 2 bếp, 4 bàn, 6 món, `day_plan` D1–D5, `shop`) | `tests/test_gather_p2.py::P2ManifestAndInputs` | [gather-p2-tests.txt](../members/minhh25-phase-2/gather-p2-tests.txt) | Đạt |
| AC-P2-02: Cá bơi, phản xạ mép, đổi hướng 120 tick, sinh cá 360·k (trần 12) | `tests/test_gather_p2.py::P2Fish` | [gather-p2-tests.txt](../members/minhh25-phase-2/gather-p2-tests.txt) | Đạt |
| AC-P2-03: Cá Sấu Năm Chèo (`M1`/`M2`, `patrol`/`chase`/`recoil`, mất `floor(hold/2)` LIFO, bất tử 90 tick) | `tests/test_gather_p2.py::P2Monsters` | [gather-p2-tests.txt](../members/minhh25-phase-2/gather-p2-tests.txt) | Đạt |
| AC-P2-04: Quán 2B/4T/6 món, bếp lấy đơn `reserved` cũ nhất `(order_tick, table_id)`, đóng ca | `tests/test_quan_p2.py` | [proof/phase-2/quan.md](../proof/phase-2/quan.md) | Đạt |
| AC-P2-05: Vòng ngày `gather → quan → shop` (`--mode day`), `Shop` (`oxygen`/`hp`), `pause`/`resumed` | `tests/test_quan_p2.py`, `tests/test_gather_p2.py::P2UpgradesAndHeadless` | [integration-p2.txt](../members/minhh25-phase-2/integration-p2.txt) | Đạt |
| AC-P2-06: Menu chính, `DayIntro`/`EveningIntro`/`DayResult`/`Summary`, màn `Shop`, `Esc`/`P` pause & HUD | `tests/test_live_ui.py` | [merge-main-tests.txt](../members/minhh25-phase-2/merge-main-tests.txt) | Đạt |

## Đánh giá ngắn
- Toàn bộ 4 lát lõi Phase 2 (`gather` cá/Cá Sấu, `quan` 2B/4T/6 món, `day`/`Shop`/`pause`, `client/ui`) đã tích hợp lên `main` và vượt qua 74/74 test tại thời điểm chốt Phase 2 (`de90282`).
- Điều chỉnh cho Phase 3: Tách quyền sở hữu file theo `docs/plan/phase-3.md` và chuyển kho đếm sang kho cá thể `{id, kind, fresh}`.
