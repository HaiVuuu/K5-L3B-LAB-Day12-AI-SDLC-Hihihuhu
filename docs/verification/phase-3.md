# Ma trận truy vết Phase 3 (QA) — Change Request "Mùa Nước Nổi" (Test Contract v1.2)

Ghi trung thực: Phase 3 đổi **kho đếm theo loại → kho cá thể `{id, kind, fresh}`**. Ở thời điểm viết, `game.contract.json` trên `main` vẫn là **1.1** (không có khối `freshness`), `chonoi/inventory.py` còn schema đếm, sim `gather`/`quan` chưa có độ tươi. Vì vậy **chưa thể kiểm chứng hành vi v1.2 trên sim thật**. Phần QA đã làm được: kiểm scenario theo cả v1.1 và v1.2, và dựng sẵn smoke v1.2 tự kích hoạt khi contract lên 1.2.

| Mục | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|
| Scenario nhận đủ 6 nguyên liệu v1.1 (`ca_keo`, `keo_neo`), nút `keo_neo`, cá `ca_keo` | `tests/test_scenario_qa.py::Kinds` | [scenario-qa.txt](../proof/phase-3/scenario-qa.txt) | Đạt (sửa lỗi còn sót ở Phase 2: `scenario.py` cứng 4 loại nên từ chối với mã 2) |
| Scenario `monsters` (loài, vị trí, dải độ sâu, state, waypoints, id trùng) và headless nhận/từ chối đúng | `Monsters` | [scenario-qa.txt](../proof/phase-3/scenario-qa.txt) | Đạt |
| Scenario v1.2: giỏ/kho là mảng cá thể; id duy nhất; `fresh` ∈ [0,100]; sức chứa; kho đếm cũ bị từ chối | `KhoCaThe` (chèn `freshness` vào tuning) | [scenario-qa.txt](../proof/phase-3/scenario-qa.txt) | Đạt ở mức hàm kiểm scenario; **chưa** chạy qua sim v1.2 |
| Giữ chỗ theo `id`: id phải có trong kho, không ươn (`fresh < 30`), không trùng giữa các đơn, không giữ theo lượng | `test_giu_cho_theo_id`, `test_ngung_o_dung_30` | [scenario-qa.txt](../proof/phase-3/scenario-qa.txt) | Đạt ở mức hàm kiểm scenario |
| Scenario v1.1 vẫn dùng bộ đếm cũ (không vỡ regression) | `test_v11_van_dung_bo_dem_cu` + toàn bộ test P1/P2 cũ | [full-suite.txt](../proof/phase-3/full-suite.txt) | Đạt: 129 test, OK (skipped=10) |
| `spoiled` ở tick 1 khi `fresh` từ 30 xuống < 30 (hao đầu bước) | `test_smoke_p3.py::Spoilage` | [smoke-p3-skip.txt](../proof/phase-3/smoke-p3-skip.txt) | **Chưa kiểm chứng**: test đã viết nhưng đang tự bỏ qua vì contract chưa có `freshness` |
| Bàn giao file kho cá thể `gather → quan`, quán tick 0 không hao thêm | `Spoilage::test_ban_giao_cung_tick_khong_hao_them` | như trên | **Chưa kiểm chứng** (cùng lý do) |
| File kho sai schema → mã 2 (kho đếm, trùng id, `fresh` ngoài [0,100], thiếu `fresh`, loại lạ) | `KhoSai` | như trên | **Chưa kiểm chứng** (cùng lý do) |
| `base_price = floor(giá × avg_fresh / 100)`, boa `floor(base_price × 0.2)` | — | — | **Chưa làm**: plan chưa nêu đủ (làm tròn `avg_fresh`? hao trong lúc nấu?), tránh đoán; để `skip` có ghi lý do |
| Nhả & thử giữ lại đúng 1 lần khi cá thể giữ bị ươn; thiếu thì `unfulfillable` | — | — | **Chưa làm** (chờ sim/quan v1.2) |
| UI hiển thị độ tươi, cảnh báo hàng ươn | Kiểm bằng snapshot giả kiểu v1.2, nhánh `feat/p3-bao-ui` | CL-09 trong `docs/clarify.md` | Đạt trên snapshot giả; chưa kiểm với sim v1.2 thật |

## Điều chưa xác nhận
- Chưa có Ticket-03 trong repo; mọi điều trên dựa vào `docs/plan/phase-3.md`. Tên trường của sự kiện `spoiled` (`id`? `item_id`?) chưa rõ nên smoke chỉ kiểm `location` và có chứa id.
- Chưa chạy lại regression Phase 1–2 trên sim v1.2 (chưa có). Khi v1.2 vào `main`: chạy `python -m unittest discover -s tests`, các test cũ dùng kho đếm sẽ đổi theo luật mới và **phải ghi lý do từng thay đổi ở đây**.
- Chưa tag `phase-3`, chưa xác nhận DoD toàn nhóm.
