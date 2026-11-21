# Kế hoạch Phase 4 — Phát hành `v1.0.0` (2:30–3:00 · Tag `phase-4` & Release `v1.0.0` trước 3:00)

## 1. Mục tiêu
- Nâng `game.contract.json` lên `contract_version: "1.3"`, khai báo `bench_cmd` và `soak_cmd` ở gốc manifest (gameplay/tuning/kho/JSONL giữ nguyên v1.2).
- Hoàn thiện 4 hạng mục lõi: (1) `<bench_cmd>` xuất `bench.json`, (2) `<soak_cmd>` chạy 10 ngày xuất `soak.json`, (3) 3 cảnh báo dễ nhận biết + chế độ tương phản cao trên UI, (4) kiểm từ clone sạch (≤ 3 lệnh), regression P1–P3, retro & đóng gói GitHub Release `v1.0.0`.
- Nhóm 4 người: **không bắt buộc mở rộng** (chỉ thêm nếu lõi + bằng chứng đã xanh hoàn toàn).

## 2. Phân công & quyền sở hữu file (không xung đột khi merge)

| Thành viên | Vai & Module | File sở hữu độc quyền (không sửa chéo) | Nhiệm vụ chính Phase 4 |
|---|---|---|---|
| **Nguyễn Đình Minh** | Release / Integrator | `game.contract.json`, `README.md`, `CREDITS.md`, tag `phase-4` & GitHub Release `v1.0.0` | Nâng `contract_version: "1.3"`, thêm `bench_cmd` & `soak_cmd`; hoàn thiện `README.md` (clone sạch chạy ≤ 3 lệnh, yêu cầu môi trường, điều khiển, lệnh test/headless/bench); rà `CREDITS.md`/license; viết release notes, gắn tag `phase-4` và công bố Release `v1.0.0` từ cùng commit trên `main`. |
| **Nguyễn Đình Vũ Hải** | Soak & Changelog / Scrum | `chonoi/soak.py`, `tests/test_soak_p4.py`, `CHANGELOG.md`, `docs/standup.md` | Viết `chonoi/soak.py` (`--seed`, `--days`, `--out soak.json`) chạy 10 Ngày liên tục trong 1 tiến trình (`D1–D5` lặp lại ở `D6–D10`), xuất `days`, `days_completed`, `crashes`, `results[]`, `duration_s`; chốt `CHANGELOG.md` đủ 4 phase. |
| **Đoàn Xuân Duy Bảo** | Cảnh báo UI & Bench / PO | `chonoi/web/index.html`, `chonoi/bench.py`, `docs/clarify.md` | Bổ sung 3 cảnh báo rõ ràng (thủy quái gần, oxy sắp hết, khách sắp giận) + **chế độ tương phản cao**; viết `chonoi/bench.py` (`--seed 42 --duration 30 --out bench.json`, 1280×720, làm nóng 3s + đo 30s, xuất `avg_fps`, `p1_low_fps`, `frames`, `measured_s`, `load_ms`). |
| **Vũ Tiến Hùng** | Bench/QA & Điều phối retro | `tests/test_smoke_p4.py`, `docs/verification/phase-4.md`, `docs/proof/phase-4/*`, `docs/retro.md`, `docs/ai-usage-log.md` | Chạy `<bench_cmd>`, `<soak_cmd> --seed 7 --days 10`, regression P1–P3 và thử clone sạch; lưu `bench.json`/`soak.json` vào `docs/proof/phase-4/`; điền `docs/verification/phase-4.md`; rà hành động P2 và chốt retro P4 trong `docs/retro.md`; kiểm `tools/check_team.py` và đủ `docs/members/<handle>.md`. |

> **File cá nhân:** Mỗi người kiểm tra lại `docs/members/<handle>.md` (≤ 200 từ) và dòng của mình trong `docs/ai-usage-log.md`.

## 3. Lịch trình 30 phút
- **0–15 phút:** Làm song song 4 luồng (`contract v1.3` + `README`, `soak.py`, `bench.py` + cảnh báo/tương phản cao, `test_smoke_p4.py`).
- **15–20 phút (Standup phút 20):** Gộp PR về `main`, chạy thử `<bench_cmd>` và `<soak_cmd --seed 7 --days 10>`, lưu artifact vào `docs/proof/phase-4/`.
- **20–25 phút:** Rà retro P2 → chốt retro P4 (`docs/retro.md`), hoàn thiện `docs/members/<handle>.md`, `docs/verification/phase-4.md` và `CHANGELOG.md`.
- **25–30 phút (trước 3:00):** Thử clone sạch chạy ≤ 3 lệnh + full regression trên `main`; Integrator gắn tag `phase-4` và phát hành GitHub Release `v1.0.0` (đính kèm bản đóng gói + release notes).

## 4. Checklist bàn giao trước 3:00 & Demo sau 3:00
- [ ] `contract_version: "1.3"`, `bench_cmd` & `soak_cmd` chạy đúng schema.
- [ ] `tools/check_team.py` xanh (đủ 4 GitHub handle trong `TEAM.md`), đủ 4 file `docs/members/<handle>.md`.
- [ ] `docs/verification/phase-4.md` khớp commit gắn tag `phase-4` và Release `v1.0.0`.
- [ ] Sẵn sàng demo (< 5 phút): chơi 1 Ngày (`gather → quan → shop`), chạy test xanh, chỉ ra đóng góp từng người và ma trận truy vết.
