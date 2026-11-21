# Phase 3 — bằng chứng module của Minh

Ngày ghi: 2026-11-21. Nguồn: `docs/requirements/phase-3.txt`; phạm vi theo `docs/plan/phase-3.md`. Nhật ký riêng để QA tổng hợp vào bằng chứng toàn nhóm, không sửa file độc quyền của Hùng.

Commit code/test: `ae469d9` trên `nguyendinhminh`; tài liệu và log đi trong commit kế tiếp. Không đẩy main hoặc gắn tag trong phần bàn giao này.

Sau khi nhận main `de90282` có UI Phase 2 mới, đã gộp và chạy lại **128/128 test đạt**, gồm 30 test Phase 3 và HTTP/UI mới: [merge-main-tests.txt](merge-main-tests.txt). Log 122 test phía dưới là kết quả trước cập nhật UI.

## Kết quả thực chạy

| Kiểm tra | Kết quả | Log |
|---|---|---|
| `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v` | **122/122 đạt**, gồm HTTP live và regression đang chạy v1.1 | [test-suite.txt](test-suite.txt) |
| `PYTHONPATH=tests:. python3 -m unittest discover -s tests -p test_gather_p3.py -v` | **30/30 đạt**, test nhánh v1.2 bằng manifest ứng viên | [gather-p3-tests.txt](gather-p3-tests.txt) |
| `python3 tools/check_gather_replay.py` | **4/4 replay v1.1 đạt**, byte ổn định và kho quán đọc đúng | [legacy-replay.txt](legacy-replay.txt) |
| Session v1.2 hold fresh=30 một bước | spoiled đúng tick 1; fresh <30 | [boundary-and-file.txt](boundary-and-file.txt) |
| Session v1.2 hold fresh=100 cập bến một bước | File/event cùng ID/kind/fresh=99.99166666666667, adapter đọc lại nguyên giá trị | [boundary-and-file.txt](boundary-and-file.txt) |

CLI v1.2 được chạy trong thư mục tạm có package sao chép và manifest ứng viên. Đã kiểm: kho đếm → mã 2 trước tạo JSONL, hái xuất cá thể, ngất xuất mảng rỗng, tick_limit giữ nguyên file và cùng seed giống byte. Không thay manifest gốc trong khi test.

## Truy vết

- **Schema/adapter:** chọn version tường minh, đúng ba khóa cá thể, sáu kind, ID duy nhất, fresh hữu hạn, giữ hàng ươn, sort ID, ghi nguyên tử/dọn file tạm khi lỗi.
- **Freshness:** fresh=30 ươn tick 1; fresh=31 về đúng 30 ở tick 120 và ươn tick 121; không phát lặp, không phát cho hàng vốn ươn, kẹp 0; dữ liệu ngoài lưới không bị lượng tử hóa sai.
- **Thứ tự:** regrowth trước spoiled, spoiled trước bơi/ngạt/hit/bến; đồ vừa nhặt/bắt còn 100; pause không hao.
- **ID/LIFO:** ID tiếp sau hậu tố lớn nhất, không cấp khi giỏ đầy, allocator chung không tái sử dụng ID mất; mẫu Ngày sau cấp ID mới theo thứ tự. lost hit và faint là các cá thể khác nhau theo LIFO, đã hao tươi.
- **Precision:** JSONL/file khớp fresh đầy đủ; tọa độ vẫn 3 chữ số; một quantum trên ngưỡng được đọc lại và qua ngưỡng đúng tick.

## Trạng thái tích hợp thật

- Manifest gốc vẫn **v1.1**, có thêm dữ liệu freshness; ứng viên **v1.2** ở `docs/contracts/game.contract.v1.2.json`. Quyết định và điều chỉnh thứ tự kế hoạch: `docs/adr/0001-phase-3-inventory-migration.md`.
- Chưa kiểm file cá thể qua quan thật hoặc vòng day v1.2: quan/day/scenario/UI còn chờ chủ module chuyển. Thử FreshnessTracker với location stock chỉ kiểm primitive, không thay việc kiểm quan/giá/giữ chỗ.
- Các test P1/P2 chưa bị đổi fixture để che lỗi; vẫn chạy nhánh legacy trong quá trình chuyển tiếp. QA cần cập nhật fixture còn hiệu lực sang cá thể khi kích hoạt toàn bộ v1.2.
- Không bật mở rộng, không đẩy main, không gắn tag, không xác nhận DoD/deadline hay người thật đã review. Nhật ký AI và phản tư nháp ở `docs/members/minhh25.md`.
