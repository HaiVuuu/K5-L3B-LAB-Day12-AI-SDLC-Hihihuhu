# Ma trận truy vết Phase 4 (QA) — Phát hành `v1.0.0`

Trạng thái ghi lúc kéo `origin/main` ở commit `7522453` (12:46, sau PR #13 của Hải): **chưa đủ điều kiện gắn tag `phase-4` / phát hành `v1.0.0`**. Đã có `chonoi/soak.py` (Hải); **chưa có** `chonoi/bench.py`, `bench_cmd`, `soak_cmd`; `game.contract.json` vẫn **1.1**; không có tag nào. Ticket-04 chưa có trong repo nên mọi điều dưới đây dựa vào `docs/plan/phase-4.md`. Không có mục nào dưới đây được tính là đạt nếu chưa có bằng chứng chạy thật.

## Checklist bàn giao (docs/plan/phase-4.md mục 4)

| AC | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|
| `contract_version: "1.3"`, `bench_cmd` và `soak_cmd` đúng schema | Đọc `game.contract.json`; `tests/test_smoke_p4.py` | [regression-p1-p3-main.txt](../proof/phase-4/regression-p1-p3-main.txt) (5 test smoke P4 tự bỏ qua) | **Chưa đạt**: manifest vẫn 1.1, chưa có hai lệnh. `contract.py` còn từ chối `1.3` (chỉ nhận 1.0/1.1/1.2) |
| `<bench_cmd>` xuất `bench.json` (`avg_fps`, `p1_low_fps`, `frames`, `measured_s`, `load_ms`) | `test_smoke_p4.py::Bench`; số liệu chuẩn `--seed 42 --duration 30` | — | **Chưa kiểm chứng**: chưa có `chonoi/bench.py` (phần của Bảo). Test đã viết, kiểm logic trên bản giả ở thư mục tạm (không commit) |
| `<soak_cmd> --seed 7 --days 10` xuất `soak.json` (`days`, `days_completed`, `crashes`, `results[]`, `duration_s`) | Chạy `python3 -m chonoi.soak --seed 7 --days 10` hai lần + `test_smoke_p4.py::Soak` (trên bản sao có `soak_cmd` thật) | [soak.json](../proof/phase-4/soak.json) | **Đạt về schema và độ bền**: 10/10 ngày, 0 crash, 10 phần tử `results`, hai lần chạy giống nhau (trừ `duration_s`, 4,9–6,7 s). **Giới hạn:** bot cập bến ngay nên mỗi ngày `earned = 0`, uy tín 3,0, điểm 300 → soak mới chứng minh không treo/crash, chưa thực thi luật bán hàng. `soak_cmd` **chưa khai trong manifest** (chạy trực tiếp bằng `python3 -m chonoi.soak`) |
| 3 cảnh báo UI (thủy quái gần, oxy sắp hết, khách sắp giận) + chế độ tương phản cao | Kiểm thủ công trên `chonoi.live` | — | **Chưa kiểm chứng**: phần của Bảo, chưa có commit Phase 4. (UI hiện có từ Phase 2–3: "Thủy quái!", "Hết hơi!", oxy < 25%, kiên nhẫn < 25% — chưa phải 3 cảnh báo + tương phản cao của Phase 4) |
| `tools/check_team.py` xanh (đủ 4 handle), đủ 4 `docs/members/<handle>.md` | Chạy `python tools/check_team.py` | [check-team.txt](../proof/phase-4/check-team.txt) | **Chưa đạt**: thiếu handle của Minh và Bảo trong `TEAM.md` (handle `minhh25` của Minh có ở `docs/members/minhh25.md` nhưng đã mất khỏi `TEAM.md` sau một lần merge). Có 3/4 file member (thiếu Bảo). Lưu ý: `TEAM.md` ghi Hải là `HaiVuu` nhưng repo/file member dùng `HaiVuuu` — cần Hải xác nhận handle thật |
| Regression P1–P3 xanh trên `main` | `python -m unittest discover -s tests` | [regression-p1-p3-main.txt](../proof/phase-4/regression-p1-p3-main.txt) | **Đạt trên manifest 1.1 hiện tại**: 173 test, OK (skipped=15). Trước PR #13 của Hải là 9 fail (xem mục dưới); Hải đã thêm tương thích v1.1/v1.2. Chưa đạt trên manifest v1.2: 23 fail ở file của người khác |
| Clone sạch chạy ≤ 3 lệnh | `git clone` → `cd` → `python -m unittest discover -s tests` trên `origin/main` | [clean-clone-main.txt](../proof/phase-4/clean-clone-main.txt) | **Đạt cho phần test**: clone `7522453`, 167 test, OK (skipped=10), Python 3.12.10, trên máy này. Chưa có hướng dẫn môi trường ở `README.md` (phần của Minh); chưa chạy được `bench_cmd`/`soak_cmd` theo manifest vì chưa khai |
| `docs/verification/phase-4.md` khớp commit gắn tag | — | — | **Không áp dụng được**: chưa có tag. Tài liệu này ghi theo `7522453` + nhánh `vutienhung` |
| Demo (< 5 phút): chơi 1 Ngày `gather → quan → shop`, chạy test xanh, đóng góp từng người | — | — | **Chưa sẵn sàng đầy đủ**: test đã xanh trên `main` (manifest 1.1) nhưng còn thiếu bench, 3 cảnh báo UI, tương phản cao, tag/Release |

## Hồi quy P1–P3
**Diễn biến:** sau PR #11/#12 (12:22), `QuanSim` của Hải chỉ nói v1.2 trong khi manifest `main` là 1.1 (gather ghi kho đếm) → `main` đỏ (9 fail trên nhánh `vutienhung`, 11 fail khi clone sạch `24c65dd`). PR #13 (12:46) thêm tương thích v1.1/v1.2 cho quan và `soak.py` → **`main` xanh trở lại** (173 test OK, clone sạch 167 test OK).

**Còn lại khi bật manifest v1.2** ([regression-p1-p3-v12-manifest.txt](../proof/phase-4/regression-p1-p3-v12-manifest.txt)): **không có test QA nào fail** (`test_integration`, `test_scenario_qa`, `test_smoke_p3`, `test_smoke_p4`). Còn **23 test fail ở file của người khác**: `test_gather.py` (10), `test_gather_p2.py` (7), `test_smoke_p1.py` (2, test giảng viên cấp), `test_live_ui.py`, `test_python_starter_units.py`, `test_quan_p2.py`, `test_quan_p3.py` (mỗi file 1). Nguyên nhân chủ yếu là fixture giỏ/kho dạng đếm; các test này phải đổi theo luật v1.2 và ghi lý do khi bật.

**Cần Minh:** nâng manifest lên bản chạy luật v1.2 (Phase 4: `1.3` giữ gameplay/kho/JSONL v1.2) **và** cho `chonoi/contract.py` nhận `1.3` (hiện chỉ nhận 1.0/1.1/1.2); mỗi chủ file cập nhật fixture kho đếm. `scenario.py` và test của QA đã sẵn sàng cho `1.3` (nhận biết "từ 1.2 trở lên").

## Việc QA đã làm cho Phase 4
- `tests/test_smoke_p4.py` (5 test): tự kích hoạt khi manifest có `bench_cmd` và `soak_cmd`; kiểm schema bench/soak, 10 ngày không crash, tất định theo seed. Kiểm logic bằng bench/soak **giả** ở thư mục tạm (không commit): 4 đạt, 1 skip.
- `scenario.py`, `test_integration.py`, `test_smoke_p3.py`: nhận biết v1.2 bằng "phiên bản từ 1.2 trở lên" để không tự tắt khi lên 1.3; thêm ca contract 1.3 trong `test_scenario_qa.py`.
- Sửa smoke bàn giao P3 theo dung sai ±0.01 của Ticket-03 (JSONL làm tròn 3 chữ số).

## Chưa làm / chưa xác nhận
- Chưa có `bench.json` (chờ `chonoi/bench.py` của Bảo). Đã có `soak.json` thật ([soak.json](../proof/phase-4/soak.json)) nhưng bot chưa bán hàng nên `earned = 0`.
- Chưa kiểm clone sạch trên Windows và Linux khác nhau; chỉ chạy trên máy này (Python 3.12.10).
- Chưa chạy chế độ tương phản cao, cảnh báo UI Phase 4.
- Chưa gắn tag, chưa có Release `v1.0.0`; không xác nhận DoD toàn nhóm.
