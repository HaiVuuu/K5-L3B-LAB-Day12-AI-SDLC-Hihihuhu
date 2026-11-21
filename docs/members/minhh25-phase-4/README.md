# Phase 4 — bàn giao Release/Integrator (Minh)

Ngày: 2026-11-21. Theo `docs/plan/phase-4.md`, `docs/requirements/phase-4.txt`. Đây là bản chuẩn bị, **chưa Release**. Người dùng cho phép tự push nếu không có issue; hiện có issue thật nên giữ commit local tới khi thống nhất cách bàn giao.

## Đã làm trong phạm vi Minh

- Manifest v1.3 có bench_cmd/soak_cmd và run_cmd mở vòng day. Không đổi gameplay tuning.
- contract.py chấp nhận v1.3, yêu cầu lệnh đo; metadata nội bộ chuẩn hóa về v1.2 để gather/scenario vẫn dùng kho cá thể. inventory.py nhận v1.3 theo đúng schema v1.2, không vô tình quay về kho đếm.
- README chạy clone sạch ≤3 lệnh, môi trường/điều khiển, test/headless/bench/soak, đóng gói và giới hạn thật. Credits rà asset/font/AI/starter/license; release notes nháp ở docs/releases/v1.0.0.md.
- tools/package_release.py đóng đúng commit thành ZIP + receipt SHA-256; không lấy file chưa commit. tools/check_release.py thu log thật và báo chưa đạt, không giả lập bench/soak hay tự publish/tag.
- Test riêng v1.3 giữ nguyên tuning/snapshot/event/schema v1.2 ở cả gather/quan/day: **5/5 đạt**. Gather P3 **30/30 đạt**.
- Khôi phục handle minhh25 đã xác minh, sửa handle Hải theo repo/docs thành HaiVuuu. Phản tư Minh đã rút xuống 140 từ, lịch sử giữ ở history-before-release.md.

## Issue phát hiện, không che bằng test xanh

| Vấn đề | Bằng chứng / chủ phần |
|---|---|
| Baseline main trước việc P4 đã lỗi: 165 test, 11 failure + lỗi bind localhost trong sandbox, 10 skip | baseline-tests.txt. Quan bật cá thể chỉ vì có freshness mặc dù manifest 1.1, gây mất kho đếm. Cần chủ quan/day + QA kiểm tích hợp |
| Khi bật v1.3: regression 170 test, **20 failure, 16 error, 10 skip** | release-check-logs/regression.txt; nhiều fixture/assertion P1–P2 vẫn kho đếm. Đây không phải báo cáo toàn bộ test đạt |
| Chưa có chonoi/bench.py và chonoi/soak.py | release-status.json. Theo kế hoạch Bảo/Hải sở hữu các module này; chưa có số FPS/10 Ngày để công bố |
| TEAM thiếu handle Bảo; thiếu docs/members/<handle>.md của Bảo | release-check-logs/team.txt; đã hỏi người dùng, không tự bịa handle/đóng góp |
| Không có LICENSE/COPYING; starter metadata license:null | CREDITS.md; chờ nguồn giấy phép/nhóm xác nhận |
| Chưa có xác nhận UI cảnh báo/tương phản cao và ma trận QA P4 | Theo phạm vi Bảo/Hùng trong kế hoạch |

`release-status.json` và log này được tạo trên worktree chuẩn bị (base commit trong report); chưa phải artifact từ tag. Kết quả phải chạy lại trên main bàn giao sau khi gộp/sửa đủ. Không sửa file bench/soak/UI hoặc báo cáo QA độc quyền của đồng đội trong lần bàn giao này.

## Cách tiếp tục

1. Hải/Bảo bàn giao module đo/soak; QA chuyển fixture/regression còn hiệu lực sang schema v1.2 và chạy smoke v1.3.
2. Bổ sung handle/reflection còn thiếu và xác nhận LICENSE. Hoàn thiện CHANGELOG/retro/verification theo chủ phần.
3. Chạy `python3 tools/check_release.py --measure --out dist/release-status.json`; kiểm clone sạch và UI.
4. Gộp main, chốt đúng SHA, đặt phase-4/v1.0.0 cùng SHA, đóng ZIP bằng SHA đó rồi đính Release. Không phát hành bản chuẩn bị này như bản đã đạt DoD.
