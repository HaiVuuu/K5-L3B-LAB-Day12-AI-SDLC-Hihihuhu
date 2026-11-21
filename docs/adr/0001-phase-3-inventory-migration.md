# ADR-0001: Chuyển kho đếm sang kho cá thể theo hai bước

- Trạng thái: triển khai chuyển tiếp trên nhánh Minh; thời điểm bật v1.2 toàn nhóm chờ tích hợp/review.
- Ngày/người ghi: 2026-11-21, Nguyễn Đình Minh với Codex hỗ trợ.
- Nguồn: `docs/requirements/phase-3.txt`, phần quy trình mục 2 cho phép hỗ trợ hai phiên bản nội bộ và bật v1.2 khi hai đầu bàn giao sẵn sàng.

## Bối cảnh và tác động

Kho mới là `{"items":[{"id","kind","fresh"}]}`. Kho đếm v1.0/v1.1 không còn hợp lệ dưới v1.2. Khi bắt đầu việc này, main đã có Phase 2 nhưng quan/day/scenario/UI chưa chuyển sang kho cá thể. Đổi version ngay sẽ làm hỏng bàn giao, giữ chỗ và phần đọc kho.

| Module/file | Tác động | Chủ phần việc |
|---|---|---|
| game.contract.json / inventory.py | Chọn schema theo version, validation nghiêm, ghi nguyên tử; chuẩn độ tươi | Minh |
| gather.py / test_gather_p3.py | Hold cá thể, ID I xuyên Ngày, hao tươi đầu bước, spoiled và lost cá thể | Minh |
| contract.py / jsonl.py | Truyền version cho sim; fresh phải giữ đủ precision trong JSONL và file | Minh, thay đổi tối thiểu do khung chưa hỗ trợ v1.2 |
| quan.py / day.py / CHANGELOG.md | Kho/reserved theo ID, hao tươi, giá/boa, allocator xuyên Ngày, Shop không hao | Hải |
| scenario.py / smoke / verification | Fixture cá thể, liên kết ID/giữ chỗ; regression đã đổi schema | Hùng |
| web / clarify | Hiển thị độ tươi, hàng ươn | Bảo |

## Quyết định

1. Thêm số chuẩn `tuning.freshness` vào manifest đang chạy nhưng giữ `contract_version:"1.1"` trong bước chuyển tiếp. `load_contract` gắn metadata nội bộ `tuning._contract_version`; gather chỉ bật cá thể khi version bằng 1.2.
2. Chuẩn bị manifest đầy đủ v1.2 ở `docs/contracts/game.contract.v1.2.json`. Bộ test mới chạy sim/adapter bằng manifest này, và chạy CLI trong bản sao tạm riêng. Không thay cấu hình repo trong lúc chạy test.
3. Adapter có nhánh tường minh theo contract_version. **Khi v1.2 hoạt động, file kho đếm bị từ chối**, không tự chuyển đổi hoặc đoán schema từ hình dạng đầu vào. Mặc định API file đọc version từ manifest hiện hành; test/chủ module có thể truyền version tường minh.
4. Giữ 240 đơn vị/điểm tươi trong mô phỏng: chuẩn trừ 2/tick ở gather và 1/tick ở stock. Fixture thập phân ngoài lưới giữ số hữu tỉ, không làm tròn làm đổi phía ngưỡng. Khi xuất số JSON, giữ phía ngưỡng 30 và đủ precision đọc lại. Tọa độ vẫn xuất 3 chữ số, `fresh` không bị làm tròn 3 chữ số.
5. Gather dùng IdAllocator được truyền vào, reserve ID fixture ở Ngày 1. Từ Ngày 2, nhận lại mẫu hold gốc và cấp ID mới theo thứ tự mảng. DaySession phải giữ cùng allocator xuyên pha/Ngày, không cấp lại trước khi truyền mẫu cho gather.
6. Không đổi file độc quyền của đồng đội, không coi test module đạt là DoD toàn nhóm. Đây là điều chỉnh thứ tự bật version so với bước mở màn trong kế hoạch nhằm giữ main chạy được, không đổi luật Ticket.

## Thứ tự tích hợp và bật v1.2

1. Gộp adapter/gather cùng tài liệu này; main vẫn chạy v1.1.
2. Hải nối quan/day và allocator, Hùng nối scenario và migration test, Bảo nối HUD. Đọc API ở `docs/contracts/phase-3.md`.
3. Kiểm hai tiến trình gather → file → quan, ngưỡng 30, giữ lại khi ươn, giá/boa, day/Shop và regression còn hiệu lực trên bản ứng viên.
4. Khi hai đầu sẵn sàng, đổi manifest gốc sang v1.2 bằng nội dung ứng viên (giữ mọi dữ liệu mới của nhóm nếu có), cập nhật fixture/test đếm theo lý do breaking change, chạy kiểm chứng toàn bộ rồi tag trên main.

## Hệ quả

- Phần Minh kiểm được độc lập và có thể gộp sớm; chưa kích hoạt đầy đủ v1.2 trong bản mặc định.
- Cần một commit tích hợp bật version sau cùng. QA vẫn phải kiểm file kho đếm bị từ chối khi v1.2 hoạt động.
- Hai thay đổi khung cần đọc chéo: metadata `_contract_version` và bảo toàn precision trường fresh. Không sửa runner/headless/live để né quyền sở hữu của nhóm.
