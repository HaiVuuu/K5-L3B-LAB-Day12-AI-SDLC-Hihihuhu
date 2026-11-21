# Changelog
## Unreleased
- Phase 1 (Minh): hoàn thiện gather — oxy/ngạt/ngất LIFO, hái/mọc lại, bắt nguyên đàn/hồi chiêu, sự kiện đúng Test Contract v1.0 và ưu tiên kết thúc ở bước cuối.
- Thêm 23 test gather, command kiểm luật/replay hai tiến trình và tài liệu tích hợp/bằng chứng; chưa phát hành tag toàn nhóm.

## Phase 3 — Test Contract v1.2 (Breaking Changes)
- Kho đếm theo loại (`{"items": {"ca_loc": 1}}`) chuyển sang kho cá thể (`{"items": [{"id": "I1", "kind": "ca_linh", "fresh": 100}]}`) khi bật `freshness` / `contract_version: "1.2"`.
- `QuanSim`: `stock` dùng mảng cá thể, `customers[].reserved` giữ theo `id` cá thể, hao tươi `-0.25/s` (`spoiled` dưới `30`), tự nhả và thử giữ lại 1 lần khi hàng giữ vừa ươn, `cook_started.data.items` trả danh sách cá thể đã dùng, chốt `base_price = floor(giá × avg_fresh / 100)` và boa `floor(base_price × 0.2)`.
- `DaySession`: giữ bộ đếm id họ `"I"` liên tục xuyên pha và Ngày.
