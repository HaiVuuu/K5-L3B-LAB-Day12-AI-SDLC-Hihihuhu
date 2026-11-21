# Kế hoạch Phase 2 — Một ngày ở chợ nổi (1:00–1:55 · Tag `phase-2` trước 1:55)

## 1. Mục tiêu
- Nâng cấp lên **Test Contract v1.1** (`contract_version: "1.1"`, số liệu chuẩn mục 1–2 của TICKET-02, 6 nguyên liệu, 6 món, 2 bếp `B1–B2`, 4 bàn `T1–T4`).
- Hoàn thành 4 phần lõi: (1) cá bơi/sinh + Cá Sấu Năm Chèo, (2) Quán 2B/4T/6 món + đóng ca, (3) Vòng ngày `--mode day --days 1..5` + Shop nâng cấp + `pause`, (4) Menu, pause, Shop & HUD hoàn chỉnh.
- Nhóm 4 người: **làm lõi đúng trước**, không bắt buộc mở rộng; mọi kiểm thử regression P1 + smoke P2 xanh trước khi gắn tag `phase-2`.

## 2. Chốt hợp đồng trước khi chia nhánh (phút 0–5)
**Integrator (Nguyễn Đình Minh)** cập nhật và đẩy lên `main` **trước** khi cả nhóm tách nhánh Phase 2 (tránh xung đột file dùng chung):
1. `game.contract.json`: nâng `contract_version: "1.1"`, thêm `N5–N6`, `ca_keo`, `keo_neo`, `fish_*`, `monsters`, `B2`, `T2–T4`, 3 món mới, `day_plan` (D1–D5), `shop.upgrades`.
2. `chonoi/inventory.py` (thêm `ca_keo`, `keo_neo`) & `chonoi/inputs.py` (thêm `pause`, `shop_done`, `buy`).

## 3. Phân công & quyền sở hữu file (không xung đột khi merge)

| Thành viên | Vai & Module | File sở hữu độc quyền (không sửa chéo) | Nhiệm vụ chính Phase 2 |
|---|---|---|---|
| **Nguyễn Đình Minh** | `sim/gather` · Integrator (dự phòng `sim/quan`) | `chonoi/sim/gather.py`, `chonoi/sim/monsters.py`, `tests/test_gather_p2.py`, `game.contract.json` | Cá linh/lóc/kèo bơi, phản xạ mép, đổi hướng 120 tick, sinh cá 360·k (trần 12); Cá Sấu `M1`/`M2` (`patrol`/`chase`/`recoil`, mất `floor(hold/2)` LIFO, bất tử 90 tick, ngất); nhận `active_upgrades` (`oxygen`/`hp`); chốt hợp đồng & gắn tag `phase-2`. |
| **Nguyễn Đình Vũ Hải** | `sim/quan` + `day`/`shop` · Scrum/Release (dự phòng `sim/gather`) | `chonoi/sim/quan.py`, `chonoi/sim/day.py`, `chonoi/runner.py`, `chonoi/headless.py`, `tests/test_quan_p2.py`, `docs/standup.md`, `CHANGELOG.md` | Quán `B1–B2`, `T1–T4`, 6 món, bếp lấy đơn `reserved` cũ nhất (`order_tick`, `table_id`), đóng ca; vòng ngày `DayIntro→gather→EveningIntro→quan→DayResult→Shop` (`--mode day --days 1..5`), Shop `oxygen`/`hp`, `pause`/`resumed`. |
| **Đoàn Xuân Duy Bảo** | `client/ui` · PO (dự phòng `qa`) | `chonoi/web/index.html`, `chonoi/web/*`, `docs/clarify.md`, `CREDITS.md` | Menu chính, `DayIntro`/`EveningIntro`/`DayResult`/`Summary`, màn hình `Shop`, `Esc`/`P` pause; HUD sáng (oxy <25%, đồng hồ ≤30s, danh sách cần lấy, `"Thủy quái!"` viền tím, `"Hết hơi!"`, cá/Cá Sấu); HUD quán (kiên nhẫn <25%, tiến độ bếp, chữ ≥18px ở 1280×720). |
| **Vũ Tiến Hùng** | `qa` · QA Lead (dự phòng `client/ui`) | `chonoi/scenario.py`, `tests/test_day_p2.py`, `tests/test_smoke_p2.py`, `docs/verification/phase-2.md`, `docs/proof/phase-2/*`, `docs/retro.md`, `docs/ai-usage-log.md` | Kiểm tra scenario v1.1 (`day`, `monsters`, `age_ticks`, `day_plan`); viết & chạy smoke P2 (`gather`, `quan`, `day --days 1..5`, `Shop`, `pause`), regression P1, đo tốc độ headless (`≤ 20s` / 22.200 tick); tổng hợp bằng chứng & retro. |

> **File cá nhân:** Mỗi người tự tạo/cập nhật `docs/members/<handle>.md` của riêng mình.

## 4. Lịch trình & điểm đồng bộ
- **0–5 phút:** Integrator đẩy commit `contract v1.1` lên `main`; cả nhóm `git pull` rồi tạo nhánh `feat/p2-<ten>`.
- **5–20 phút:** 4 người code & chạy unit test riêng của mình.
- **20 phút (Checkpoint 1):** Standup 2–3 phút; chạy smoke tích hợp `gather --inventory-out → quan --inventory`, lưu `docs/proof/phase-2/integration.*`.
- **20–35 phút:** Hoàn thiện `--mode day`, `Shop`, `pause` và HUD đầy đủ.
- **35–45 phút (Checkpoint 2):** Rebase `main`, chạy `test_smoke_p2.py` + `day --days 5` + regression P1; ghi `docs/verification/phase-2.md`.
- **45–50 phút:** Retro nhanh trong `docs/retro.md`, cập nhật `docs/ai-usage-log.md`.
- **50–55 phút (trước 1:55):** Integrator kiểm xanh toàn bộ trên `main` và đẩy tag `phase-2`.

## 5. Rủi ro & giảm thiểu
- **Xung đột ở `runner.py` / `headless.py` / `scenario.py`:** Tách rõ: Hải chỉ sửa luồng `day`/`pause` trong `runner.py` + `headless.py`; Hùng giữ `scenario.py`; Minh giữ `gather.py` + `game.contract.json`; Bảo chỉ sửa `chonoi/web/`.
- **Lệch schema snapshot giữa `day.py` và `web/index.html`:** Chốt ngay ở phút 5 các trường `day`, `day_plan`, `upgrades`, `active_upgrades`, `state: "paused"`, `monsters[]`, `shop` theo đúng mục 4.4 của TICKET-02.
- **Thiếu thời gian (55 phút):** Giữ nguyên tắc làm lõi đúng trước; tuyệt đối không thêm mở rộng khi `day --days 5` và regression P1 chưa xanh.
