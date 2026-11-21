# Ma trận truy vết Phase 4 (QA) — Phát hành `v1.0.0`

Trạng thái ghi lúc kéo `origin/main` ở commit `24c65dd` (12:22): **chưa đủ điều kiện gắn tag `phase-4` / phát hành `v1.0.0`**. Chưa có `bench_cmd`, `soak_cmd`, `chonoi/bench.py`, `chonoi/soak.py` ở bất kỳ nhánh nào; `game.contract.json` vẫn **1.1**; không có tag nào. Ticket-04 chưa có trong repo nên mọi điều dưới đây dựa vào `docs/plan/phase-4.md`. Không có mục nào dưới đây được tính là đạt nếu chưa có bằng chứng chạy thật.

## Checklist bàn giao (docs/plan/phase-4.md mục 4)

| AC | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|
| `contract_version: "1.3"`, `bench_cmd` và `soak_cmd` đúng schema | Đọc `game.contract.json`; `tests/test_smoke_p4.py` | [regression-p1-p3-main.txt](../proof/phase-4/regression-p1-p3-main.txt) (5 test smoke P4 tự bỏ qua) | **Chưa đạt**: manifest vẫn 1.1, chưa có hai lệnh. `contract.py` còn từ chối `1.3` (chỉ nhận 1.0/1.1/1.2) |
| `<bench_cmd>` xuất `bench.json` (`avg_fps`, `p1_low_fps`, `frames`, `measured_s`, `load_ms`) | `test_smoke_p4.py::Bench`; số liệu chuẩn `--seed 42 --duration 30` | — | **Chưa kiểm chứng**: chưa có `chonoi/bench.py` (phần của Bảo). Test đã viết, kiểm logic trên bản giả ở thư mục tạm (không commit) |
| `<soak_cmd> --seed 7 --days 10` xuất `soak.json` (`days`, `days_completed`, `crashes`, `results[]`, `duration_s`) | `test_smoke_p4.py::Soak` | — | **Chưa kiểm chứng**: chưa có `chonoi/soak.py` (phần của Hải). Cùng lý do |
| 3 cảnh báo UI (thủy quái gần, oxy sắp hết, khách sắp giận) + chế độ tương phản cao | Kiểm thủ công trên `chonoi.live` | — | **Chưa kiểm chứng**: phần của Bảo, chưa có commit Phase 4. (UI hiện có từ Phase 2–3: "Thủy quái!", "Hết hơi!", oxy < 25%, kiên nhẫn < 25% — chưa phải 3 cảnh báo + tương phản cao của Phase 4) |
| `tools/check_team.py` xanh (đủ 4 handle), đủ 4 `docs/members/<handle>.md` | Chạy `python tools/check_team.py` | [check-team.txt](../proof/phase-4/check-team.txt) | **Chưa đạt**: thiếu handle của Minh và Bảo trong `TEAM.md` (handle `minhh25` của Minh có ở `docs/members/minhh25.md` nhưng đã mất khỏi `TEAM.md` sau một lần merge). Có 3/4 file member (thiếu Bảo). Lưu ý: `TEAM.md` ghi Hải là `HaiVuu` nhưng repo/file member dùng `HaiVuuu` — cần Hải xác nhận handle thật |
| Regression P1–P3 xanh trên `main` | `python -m unittest discover -s tests` | [regression-p1-p3-main.txt](../proof/phase-4/regression-p1-p3-main.txt) | **Chưa đạt**: 171 test, **9 fail**, skipped=15 (xem mục dưới) |
| Clone sạch chạy ≤ 3 lệnh | `git clone` → `cd` → `python -m unittest discover -s tests` trên `origin/main` | [clean-clone-main.txt](../proof/phase-4/clean-clone-main.txt) | **Chạy được trong 3 lệnh nhưng không xanh**: clone `24c65dd`, 165 test, 11 fail. Chưa có hướng dẫn môi trường ở `README.md` (phần của Minh) |
| `docs/verification/phase-4.md` khớp commit gắn tag | — | — | **Không áp dụng được**: chưa có tag. Tài liệu này ghi theo `24c65dd` + nhánh `vutienhung` |
| Demo (< 5 phút): chơi 1 Ngày `gather → quan → shop`, chạy test xanh, đóng góp từng người | — | — | **Chưa sẵn sàng**: test chưa xanh trên `main` |

## Hồi quy P1–P3: `main` đang đỏ vì gather và quan lệch phiên bản
Manifest `main` là **1.1** (gather ghi kho dạng đếm `{kind: số}`), nhưng `QuanSim` của Hải sau PR #11/#12 chỉ còn nói **v1.2** (stock là mảng cá thể). Hai đầu bàn giao không khớp nên một số test tích hợp fail. Đây là lệch cấu hình chuyển tiếp, không phải lỗi luật riêng của ai.

| File test (manifest 1.1, `main` + `vutienhung`) | Fail | Chi tiết |
|---|---|---|
| `test_gather.py`, `test_gather_p2.py` | 1 + 2 | Chuyển giao kho gather → quan (test của Minh) |
| `test_quan.py` | 2 | Fixture quán dạng đếm; quan nay là v1.2 (test của Hải) |
| `test_smoke_p1.py` | 1 | `test_inv_01_gather_writes_inventory_quan_reads_it` (test giảng viên cấp) |
| `test_live_ui.py` | 1 | Kịch bản day qua Shop |
| `test_integration.py` (QA) | 2 | `chuoi_giu_nguyen_kho_qua_hai_buoi`, `hai_nut_mat_nuoc_vao_kho`: đầu quán v1.2 đọc kho đếm v1.1 |

Khi bật manifest ứng viên v1.2 trên cùng mã nguồn ([regression-p1-p3-v12-manifest.txt](../proof/phase-4/regression-p1-p3-v12-manifest.txt)): **không còn test QA nào fail** (`test_integration`, `test_scenario_qa`, `test_smoke_p3` đều đạt hoặc skip có lý do; smoke P3 đạt 6/8, 2 skip chờ `base_price`/giữ lại khi ươn). Còn 25 test fail ở file của người khác (fixture kho đếm trong `test_gather*.py`, `test_quan*.py`, `test_smoke_p1.py`, `test_live_ui.py`, `test_python_starter_units.py`) — các test cũ này phải đổi theo luật v1.2 và ghi lý do khi bật.

**Đề xuất để `main` xanh:** Minh nâng manifest lên bản chạy luật v1.2 (đúng kế hoạch Phase 4: `1.3` giữ nguyên gameplay/kho/JSONL v1.2) **và** cho `chonoi/contract.py` nhận `1.3`; mỗi chủ file cập nhật fixture kho đếm. `scenario.py` và test của QA đã sẵn sàng cho `1.3` (nhận biết "từ 1.2 trở lên").

## Việc QA đã làm cho Phase 4
- `tests/test_smoke_p4.py` (5 test): tự kích hoạt khi manifest có `bench_cmd` và `soak_cmd`; kiểm schema bench/soak, 10 ngày không crash, tất định theo seed. Kiểm logic bằng bench/soak **giả** ở thư mục tạm (không commit): 4 đạt, 1 skip.
- `scenario.py`, `test_integration.py`, `test_smoke_p3.py`: nhận biết v1.2 bằng "phiên bản từ 1.2 trở lên" để không tự tắt khi lên 1.3; thêm ca contract 1.3 trong `test_scenario_qa.py`.
- Sửa smoke bàn giao P3 theo dung sai ±0.01 của Ticket-03 (JSONL làm tròn 3 chữ số).

## Chưa làm / chưa xác nhận
- Chưa có `bench.json`/`soak.json` thật trong `docs/proof/phase-4/` (chờ Bảo và Hải).
- Chưa kiểm clone sạch trên Windows và Linux khác nhau; chỉ chạy trên máy này (Python 3.12.10).
- Chưa chạy chế độ tương phản cao, cảnh báo UI Phase 4.
- Chưa gắn tag, chưa có Release `v1.0.0`; không xác nhận DoD toàn nhóm.
