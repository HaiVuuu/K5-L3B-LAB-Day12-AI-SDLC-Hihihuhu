# Ma trận truy vết Phase 3 (QA) — Change Request "Mùa Nước Nổi" (Test Contract v1.2)

Ghi trung thực: Phase 3 đổi **kho đếm theo loại → kho cá thể `{id, kind, fresh}`**. Trên `main`, `game.contract.json` vẫn **1.1** và sim `gather`/`quan` chưa có độ tươi. Nhánh `origin/nguyendinhminh` của Minh có gather v1.2 "staged" (manifest ứng viên `docs/contracts/game.contract.v1.2.json`, Ticket-03 ở `docs/requirements/phase-3.txt`) nhưng **chưa vào `main`**, và `quan`/`day` v1.2 (Hải) **chưa có**. QA đã: (1) sửa/kiểm scenario theo v1.1 và v1.2, (2) dựng smoke v1.2 tự kích hoạt khi `contract_version == "1.2"`, (3) chạy thử smoke đó trên bản gather v1.2 của Minh trong thư mục tạm (không merge) để biết test nào đã chạy được thật.

| Mục | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|
| Scenario nhận đủ 6 nguyên liệu v1.1 (`ca_keo`, `keo_neo`), nút `keo_neo`, cá `ca_keo` | `tests/test_scenario_qa.py::Kinds` | [scenario-qa.txt](../proof/phase-3/scenario-qa.txt) | Đạt (sửa lỗi còn sót ở Phase 2: `scenario.py` cứng 4 loại nên từ chối với mã 2) |
| Scenario `monsters` (loài, vị trí, dải độ sâu, state, waypoints, id trùng) và headless nhận/từ chối đúng | `Monsters` | [scenario-qa.txt](../proof/phase-3/scenario-qa.txt) | Đạt |
| Scenario v1.2: giỏ/kho là mảng cá thể; id duy nhất; `fresh` ∈ [0,100]; sức chứa; kho đếm cũ bị từ chối | `KhoCaThe` (chèn `freshness` vào tuning) | [scenario-qa.txt](../proof/phase-3/scenario-qa.txt) | Đạt ở mức hàm kiểm scenario; **chưa** chạy qua sim v1.2 |
| Giữ chỗ theo `id`: id phải có trong kho, không ươn (`fresh < 30`), không trùng giữa các đơn, không giữ theo lượng | `test_giu_cho_theo_id`, `test_ngung_o_dung_30` | [scenario-qa.txt](../proof/phase-3/scenario-qa.txt) | Đạt ở mức hàm kiểm scenario |
| Scenario v1.1 vẫn dùng bộ đếm cũ (không vỡ regression) | `test_v11_van_dung_bo_dem_cu` + toàn bộ test P1/P2 cũ | [full-suite.txt](../proof/phase-3/full-suite.txt) | Đạt: 129 test, OK (skipped=10) |
| `spoiled` ở tick 1 khi `fresh` 30 → < 30, data `{item_id, kind, location:"hold"}` (ví dụ Ticket-03); hàng tươi không phát `spoiled` | `test_smoke_p3.py::Spoilage` (2 test) | [smoke-p3-on-minh-branch.txt](../proof/phase-3/smoke-p3-on-minh-branch.txt) | **Đạt trên gather v1.2 của Minh** (thư mục tạm, chưa vào `main`). Trên `main` hiện tại: tự bỏ qua ([smoke-p3-skip.txt](../proof/phase-3/smoke-p3-skip.txt)) |
| File kho sai schema → mã 2; scenario kho đếm cũ → mã 2 (`--inventory` và `--scenario`) | `KhoSai::test_file_kho_sai_exit_2`, `test_scenario_kho_dem_cu_exit_2` | như trên | **Đạt trên gather v1.2 của Minh** (với `scenario.py` mới của QA) |
| File kho cá thể hợp lệ vào quán (`--inventory`, `--ticks 0`) | `KhoSai::test_file_kho_ca_the_hop_le_exit_0` | như trên | **Chưa đạt**: `QuanSim` còn `dict(inventory)` nên crash (`ValueError`) khi nhận mảng cá thể — chờ Hải làm `quan` v1.2 |
| Bàn giao file `gather → quan` cùng id/kind/độ tươi, quán tick 0 không hao thêm | `Spoilage::test_ban_giao_cung_tick_khong_hao_them` | như trên | **Chưa đạt**: cùng nguyên nhân (quan chưa v1.2); phần gather ghi kho đã đúng |
| `base_price = floor(giá × avg_fresh / 100)`, boa `floor(base_price × 0.2)` | — | — | **Chưa làm**: plan chưa nêu đủ (làm tròn `avg_fresh`? hao trong lúc nấu?), tránh đoán; để `skip` có ghi lý do |
| Nhả & thử giữ lại đúng 1 lần khi cá thể giữ bị ươn; thiếu thì `unfulfillable` | — | — | **Chưa làm** (chờ sim/quan v1.2) |
| UI hiển thị độ tươi, cảnh báo hàng ươn | Chụp màn hình: snapshot giả v1.2 và **gather v1.2 thật của Minh** (cá thể fresh 30,005 → ươn tick 1) | CL-09 trong `docs/clarify.md` (nhánh `feat/p3-bao-ui`) | Đạt với gather; phần kho quán/Shop chưa kiểm (chờ quan v1.2) |

## Hồi quy khi bật manifest v1.2 (chạy lại sau khi `main` có PR #10 của Minh, 12:14)
`main` đã có gather v1.2 "staged" và manifest ứng viên `docs/contracts/game.contract.v1.2.json`, nhưng `game.contract.json` vẫn 1.1. Để biết cái giá của việc bật v1.2, đã chạy cả bộ test trên bản sao của `main` với manifest ứng viên làm `game.contract.json` ([full-suite-on-v12-manifest.txt](../proof/phase-3/full-suite-on-v12-manifest.txt)).

- Trên manifest hiện tại của `main` (1.1): **161 test, OK (skipped=10)** ([full-suite.txt](../proof/phase-3/full-suite.txt)).
- Trên manifest v1.2: **33 test fail** (21 fail, 12 lỗi). Đây là hệ quả dự kiến của đổi schema kho (fixture bộ đếm → cá thể) và quan chưa v1.2, **không phải lỗi mới của luật**:

| File test | Số test fail | Nguyên nhân | Ai đổi |
|---|---|---|---|
| `test_gather.py` | 11 | fixture giỏ/kho đếm (`hold` là chuỗi) | Minh (đã ghi trong tài liệu của Minh: test CLI chạy v1.2 trong thư mục tạm) |
| `test_gather_p2.py` | 7 | như trên | Minh |
| `test_integration.py` | 8 | fixture `hold` chuỗi + so kho `{kind: số}`; phía quán còn dict | Hùng (QA) — **chưa migrate**, và phần quán chờ Hải |
| `test_smoke_p1.py` | 2 | fixture kho đếm | cần đổi theo luật v1.2, ghi lý do ở commit khi bật |
| `test_smoke_p3.py` | 2 | `QuanSim` chưa nhận kho cá thể (`dict(inventory)` crash) | Hải |
| `test_quan_p2.py`, `test_live_ui.py`, `test_python_starter_units.py` | 1 + 1 + 1 | `quan`/`day` còn kho đếm; fixture hold chuỗi | Hải / Hùng |

`test_scenario_qa.py` (15 test) pass trên **cả hai** manifest (sau khi sửa: nhánh bộ đếm của `scenario.py` truyền `contract_version="1.1"` thay vì để `validate_items` tự theo manifest, và helper test ép về v1.1 khi cần).

## Điều chưa xác nhận
- Ticket-03 chỉ có ở nhánh `nguyendinhminh` (chưa vào `main`). Chưa viết test cho `base_price`, thử giữ lại khi ươn, `cook_started.data.items`: chờ quan v1.2. Chưa làm phần mở rộng (dòng lũ, đặt trước, `current`, `reservations`) — nhóm 4 người không bắt buộc.
- Scenario: nhận biết v1.2 bằng `tuning._contract_version == "1.2"` (đúng thiết kế chuyển tiếp của Minh), không bằng sự có mặt của `freshness`. Chưa kiểm "id vật lý duy nhất giữa các nơi chứa" xuyên `day` vì scenario `day` chưa được headless nạp.
- Chưa chạy lại regression Phase 1–2 trên sim v1.2 (chưa có). Khi v1.2 vào `main`: chạy `python -m unittest discover -s tests`, các test cũ dùng kho đếm sẽ đổi theo luật mới và **phải ghi lý do từng thay đổi ở đây**.
- Chưa tag `phase-3`, chưa xác nhận DoD toàn nhóm.
