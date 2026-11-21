# Title

feat(gather): chuẩn bị kho cá thể và độ tươi cho Phase 3

# Description

## Phạm vi
Phase 3 · Minh — inventory/contract và sim/gather, theo change request Mùa Nước Nổi.

- Adapter kho chọn schema theo contract_version; v1.2 nhận cá thể id/kind/fresh và từ chối kho đếm.
- Hold cá thể, ID I không tái sử dụng khi caller giữ allocator; mẫu hold ở Ngày sau được cấp ID mới.
- Hao tươi đầu bước, spoiled theo ID đúng ngưỡng; lost hit/ngất theo LIFO là cá thể.
- Bảo toàn precision fresh trong JSONL/file; giữ cách làm tròn tọa độ hiện hành.
- ADR, API tích hợp, manifest v1.2 ứng viên và 30 test mới.

## Kiểm chứng
- **122/122 test đạt**, gồm regression bản chuyển tiếp và HTTP live.
- **30/30 test Phase 3 đạt**, gồm CLI v1.2 trong thư mục tạm.
- **4/4 replay v1.1 đạt**; kho cũ tiếp tục bàn giao đúng trong giai đoạn chuyển tiếp.
- Log: `docs/members/minhh25-phase-3/`; API: `docs/contracts/phase-3.md`.

## Quyết định tích hợp
Manifest mặc định giữ v1.1 để quan/day/scenario chưa chuyển không bị hỏng; thêm freshness và chuẩn bị ứng viên v1.2 ở `docs/contracts/game.contract.v1.2.json`. Cách chuyển hai bước được Ticket cho phép; lý do và thứ tự bật ghi ở ADR-0001.

Đây là PR chuẩn bị phần Minh, chưa phải bản phát hành v1.2 toàn nhóm. Khi Hải/Hùng/Bảo nối xong hai đầu, nhóm bật manifest v1.2, cập nhật fixture, kiểm giữ chỗ/giá/độ tươi/day/UI rồi tag.

## AI và review
Codex triển khai, tự rà và chạy kiểm chứng; nhật ký ở docs/members/minhh25.md. Chưa ghi nhận review của người thật.

- [ ] Rà lựa chọn schema theo version, ID và độ chính xác ở ngưỡng 30.
- [ ] Rà ADR và API FreshnessTracker/GatherSim cho quan/day/scenario.
- [ ] CI xanh; chủ module xác nhận tích hợp trước bật version/tag.
