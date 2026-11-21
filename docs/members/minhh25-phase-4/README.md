# Phase 4 — bàn giao Release/Integrator (Minh)

Theo docs/plan/phase-4.md và docs/requirements/phase-4.txt, ngày 2026-11-21. Đây là **bản chuẩn bị**, chưa phải tag/Release đã đạt DoD. Sau khi báo các issue, người dùng cho biết làm được tới đâu thì làm, cung cấp handle Bảo và yêu cầu MIT; phần chuẩn bị được bàn giao trên nhánh Minh, không tự merge/tag main.

## Đã thực hiện

- Manifest v1.3 khai bench_cmd/soak_cmd, run_cmd mở day. Gameplay tuning giữ nguyên v1.2. Bộ đọc chấp nhận v1.3 và chuẩn hóa metadata về v1.2; thêm v12_enabled theo API quan/day của Hải. Inventory v1.3 là cá thể, không quay về kho đếm.
- README clone sạch trong 3 lệnh, môi trường/điều khiển, test/headless/bench/soak và giới hạn. Release notes nháp: docs/releases/v1.0.0.md.
- LICENSE MIT theo yêu cầu Minh, mẫu OSI chính thức; CREDITS giữ attribution starter và kết quả rà. TEAM đủ 4 handle; phản tư Minh 140 từ, các file khác đều ≤200 từ. Bảo còn bản nháp chờ tự xác nhận.
- Công cụ kiểm release thu log thật và báo chưa đạt; packager lấy đúng SHA Git, ZIP kèm receipt SHA-256, không lấy file chưa commit, không tự publish/tag.
- Đã gộp main 7522453 có soak và sửa tương thích của Hải, giữ quyền sở hữu file đồng đội. Nhật ký AI cập nhật dòng Minh.

## Kiểm chứng thật

| Kiểm tra | Kết quả | Bằng chứng |
|---|---|---|
| Test hỗ trợ contract v1.3 / giữ nguyên v1.2 | **5/5 đạt** | release-tests.txt |
| Gather Phase 3 ứng viên | **30/30 đạt** | gather-p3-tests.txt |
| Team checker | **4 handle đạt** | release-check-logs/team.txt |
| Soak thật, seed 7, 10 Ngày, hai tiến trình chạy riêng để so lặp | **10/10 hoàn tất, 0 crash** mỗi lượt; gameplay khớp, bỏ duration_s (0,533s / 0,530s) | soak-1.json / soak-2.json và log |
| Clone sạch local đúng commit ứng viên, 3 lệnh mở live | Menu hoạt động, cập bến → quan, kho là list | clean-clone-and-package.json |
| ZIP tự tạo, không có .git, chạy headless gather | Đạt | clean-clone-and-package.json; package-receipt.json |
| Full regression v1.3 sau gộp soak | **Chưa đạt: 172 test, 19 failure, 16 error, 10 skip** | release-check-logs/regression.txt |

Báo cáo máy: release-status.json. Baseline main trước việc Phase 4 đã lỗi 11 assertion (thêm lỗi sandbox bind localhost); log baseline-tests.txt giữ để phân biệt lỗi có sẵn. Lần kiểm cuối đã chạy ngoài giới hạn sandbox, không còn coi bind localhost là lỗi gameplay. Log text chỉ chuẩn hóa khoảng trắng cuối dòng để qua diff check, không thay kết quả.

Clone hiện là clone sạch từ repo local ở SHA ghi trong JSON, chưa phải clone remote có commit Phase 4. Artifact ứng viên không phải artifact từ tag. Cần đóng/chạy lại đúng SHA main sau tích hợp; không dùng bằng chứng này để khẳng định full DoD.

## Còn vướng trước phát hành

- Chưa có chonoi/bench.py (Bảo), chưa có số FPS/render/1% low/load để công bố. Không giả lập số đo.
- Nhiều fixture/assertion P1–P2 còn kho đếm; cần QA migrate regression còn hiệu lực và Hải rà bàn giao/độ tươi/ID xuyên Ngày. Chưa coi các test skip là đạt.
- Các điểm cụ thể cần chủ module/QA đọc chéo: DaySession._build_gather hiện tạo IdAllocator mới thay vì truyền self.item_ids và số Ngày; snapshot kho quan/Shop còn round fresh về 3 chữ số; smoke P3 chỉ bật khi manifest đúng chuỗi 1.2 nên cần bao gồm 1.3. Soak bot không mang hàng, vì thế 0 crash chưa chứng minh các nhánh ID/precision này.
- Bảo cần tự xác nhận phản tư; UI ba cảnh báo và tương phản cao chưa kiểm thủ công. QA cần verification P4/artifact đúng commit; retro/changelog do chủ phần chốt.
- Chưa gắn phase-4/v1.0.0 hoặc tạo GitHub Release. Mẫu notes ghi rõ giới hạn. Đợi kiểm đủ trên main rồi đặt hai tag cùng SHA và đính ZIP từ SHA đó.

Giấy phép và handle đã được xử lý theo thông tin người dùng mới cung cấp; không còn dùng chúng làm blocker của báo cáo hiện tại. Tài liệu lịch sử được giữ ở history-before-release.md, không ghi nhận review/hành động cá nhân chưa diễn ra.

ZIP/clone cuối của phần chuẩn bị đã kiểm ở SHA `6c2969a`, gồm LICENSE MIT và module soak. Receipt trong package-receipt.json ghi SHA-256 của đúng ZIP ở dist/chonoi-v1.0.0-candidate.zip. Đây là ứng viên source, không gắn tag và không tuyên bố đủ điều kiện phát hành.
