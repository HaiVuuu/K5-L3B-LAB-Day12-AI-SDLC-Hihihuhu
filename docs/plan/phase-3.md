# Kế hoạch Phase 3 — Change Request “Mùa Nước Nổi” (1:55–2:30 · Tag `phase-3` trước 2:30)

## 1. Phân tích tác động (Impact Analysis — Test Contract v1.2)
Thay đổi phá vỡ (breaking change) lớn nhất: **kho đếm theo loại → kho cá thể `{id, kind, fresh}`** và **giữ chỗ theo lượng → giữ chỗ theo `id`**, **giá niêm yết → `base_price` theo độ tươi**.

| Thành phần | File cần đổi | Test ảnh hưởng | Người phụ trách |
|---|---|---|---|
| Contract & Inventory adapter | `game.contract.json`, `chonoi/inventory.py` | `test_smoke_p1.py` (schema kho mới), `test_smoke_p3.py` | Nguyễn Đình Minh (Integrator) |
| Buổi sáng (`gather` + độ tươi) | `chonoi/sim/gather.py`, `chonoi/sim/monsters.py` | `test_gather_p3.py` (thêm), `test_gather_p2.py` (`lost` cá thể) | Nguyễn Đình Minh |
| Buổi tối (`quan` + `day` + `CHANGELOG`) | `chonoi/sim/quan.py`, `chonoi/sim/day.py`, `CHANGELOG.md` | `test_quan_p3.py` (thêm), `test_quan.py` / `test_quan_p2.py` (cập nhật schema kho) | Nguyễn Đình Vũ Hải |
| Giao diện (`client/ui`) | `chonoi/web/index.html`, `docs/clarify.md` | Kiểm thủ công trên `chonoi.live` | Đoàn Xuân Duy Bảo |
| Scenario & QA | `chonoi/scenario.py`, `docs/verification/phase-3.md`, `docs/retro.md`, `docs/ai-usage-log.md` | `test_smoke_p3.py` (thêm), regression P1–P2 | Vũ Tiến Hùng |

## 2. Thứ tự tích hợp giữ `main` luôn chạy được
1. **Phút 0–7 (Commit mở màn trên `main` bởi Integrator — Nguyễn Đình Minh):**
   - Nâng `game.contract.json` lên `contract_version: "1.2"`, thêm `freshness: {"initial": 100, "gather_decay_per_s": 0.5, "quan_decay_per_s": 0.25, "spoiled_below": 30}`.
   - Cập nhật `chonoi/inventory.py` đọc/ghi schema cá thể `{"items": [{"id", "kind", "fresh"}]}`, trả mã `2` cho file kho đếm hoặc sai schema/trùng `id`/`fresh` ngoài `[0, 100]`.
   - Cả nhóm `git pull` từ `main` rồi tách/cập nhật nhánh cá nhân.
2. **Phút 7–25 (4 người làm song song, không đụng file của nhau):**
   - **Nguyễn Đình Minh (`sim/gather` · Integrator):**
     - `hold` lưu cá thể `{id, kind, fresh}` với `IdAllocator` họ `"I"` liên tục xuyên pha/Ngày.
     - Hao tươi đầu bước (`-0.5/s`, dùng số nguyên 240 đơn vị/điểm tươi để chính xác tại ngưỡng `30`), phát `spoiled` (`location: "hold"`) theo `id` khi đi từ `≥ 30` xuống `< 30`.
     - `monster_hit`/`faint` trả `lost` là mảng cá thể theo thứ tự LIFO; `gather_end.data.inventory` xuất theo `id`.
   - **Nguyễn Đình Vũ Hải (`sim/quan` + `day` · Scrum/Release):**
     - `stock` lưu cá thể, `reserved` là mảng `id` cá thể; hao tươi `-0.25/s` đầu bước (kể cả đang giữ chỗ), phát `spoiled` (`location: "stock"`) theo `id`.
     - Nhả & thử giữ lại đúng 1 lần khi cá thể giữ bị ươn (theo `order_tick`, `table_id`, chọn tươi nhất rồi `id` nhỏ); thiếu thì đơn chuyển `unfulfillable`.
     - Nấu tiêu đúng `id` giữ, phát `cook_started.data.items` (sắp `kind`, `id`), chốt `base_price = floor(giá × avg_fresh / 100)`, boa `floor(base_price × 0.2)`.
     - `DaySession`: giữ bộ đếm `id` họ `"I"` xuyên ngày; bàn giao cùng tick không hao thêm; ghi breaking change vào `CHANGELOG.md`.
   - **Đoàn Xuân Duy Bảo (`client/ui` · PO):**
     - Cập nhật `chonoi/web/index.html` hiển thị độ tươi từng cá thể trong giỏ (`gather`) và kho (`quan`/`shop`), tô màu/nhãn cảnh báo khi `fresh < 30` (hàng ươn).
     - Ghi các điểm làm rõ vào `docs/clarify.md`.
   - **Vũ Tiến Hùng (`qa` · QA Lead):**
     - Cập nhật `chonoi/scenario.py` kiểm tra mảng cá thể `gather.hold`, `quan.stock`, `customers[].reserved` (duy nhất `id`, không dùng ươn/trùng đơn, lỗi → mã 2).
     - Viết `tests/test_smoke_p3.py` (ngưỡng `fresh: 30` → `spoiled` tick 1, bàn giao file `gather → quan`, giữ lại khi ươn, `base_price`), chạy regression P1–P2 (ghi lý do các test cũ đổi theo luật mới), hoàn thiện `docs/verification/phase-3.md`, `docs/proof/phase-3/`, `docs/retro.md`, `docs/ai-usage-log.md`.

## 3. Điểm đồng bộ & kiểm soát rủi ro (35 phút)
- **Phút 20 (Checkpoint):** Standup 2–3 phút; chạy smoke bàn giao file `gather --inventory-out → quan --inventory` và kiểm ngưỡng `fresh: 30` ở tick 1, lưu bằng chứng vào `docs/proof/phase-3/`.
- **Phút 25–32:** Gộp theo thứ tự `sim/gather` → `sim/quan` → `scenario` + `client/ui` → `qa` verification; cập nhật các test P1–P2 cũ có fixture kho đếm sang kho cá thể và ghi rõ lý do trong commit/`verification/phase-3.md`.
- **Phút 32–35 (trước 2:30):** Integrator kiểm xanh toàn bộ trên `main` và đẩy tag `phase-3`.
- **Quy tắc tránh xung đột:** Nhóm 4 người làm lõi độ tươi đúng trước; không bật mở rộng (`current` / `reservations`) khi DoD lõi chưa xanh.
