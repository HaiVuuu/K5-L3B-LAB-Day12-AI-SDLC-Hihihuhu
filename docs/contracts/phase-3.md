# Phase 3 — API kho cá thể và độ tươi

Nguồn: [Ticket](../requirements/phase-3.txt). Quyết định/thứ tự chuyển tiếp: [ADR-0001](../adr/0001-phase-3-inventory-migration.md). Bản mặc định tạm giữ v1.1; [manifest ứng viên](game.contract.v1.2.json) bật v1.2 cho test và tích hợp. Không xác nhận cả nhóm đã duyệt hoặc DoD đã hoàn tất.

## Dữ liệu và version

```json
{"items":[{"id":"I1","kind":"ca_linh","fresh":100},{"id":"I2","kind":"ca_loc","fresh":97.5}]}
```

- Root đúng một khóa items. V1.2 nhận mảng cá thể có đúng id/kind/fresh; ID chuỗi duy nhất khác rỗng, sáu kind hiện hành, fresh hữu hạn trong [0,100], không nhận boolean.
- Không nhận kho đếm dưới v1.2; không tự cấp ID hoặc thay độ tươi cho file sai schema. Kho rỗng là `{items:[]}`, hàng ươn vẫn được giữ và bàn giao.
- `inventory.validate_items`, `read_inventory`, `write_inventory`, `hold_to_items` thêm keyword `contract_version`. Mặc định theo manifest hiện hành; v1.0/v1.1 giữ nhánh kho đếm. Dùng `contract_version="1.2"` khi test ứng viên từ repo vẫn đang chuyển tiếp.
- `validate_instances(items)` kiểm mảng và trả bản sao theo thứ tự đầu vào. `read_inventory`/`write_inventory`/`hold_to_items` v1.2 sắp theo ids.sort_by_id; snapshot hold giữ thứ tự vào giỏ, mới nhất cuối.
- Ghi qua file tạm cùng thư mục, thay nguyên tử và dọn tạm khi lỗi. Giữ đủ precision fresh; file và gather_end.data.inventory khớp khi giải mã JSON. Caller chỉ ghi khi gather_end, tick_limit không ghi.
- `tuning.freshness`: initial=100, gather_decay_per_s=0.5, quan_decay_per_s=0.25, spoiled_below=30. `load_contract` gắn `_contract_version` vào tuning ở thời gian chạy; field metadata này không nằm trong manifest hoặc snapshot.

## Gather và ID xuyên Ngày

```python
sim = GatherSim(tuning, gather_template, streams, shared_ids,
                day=day_number, active_upgrades=active_upgrades)
```

- Gather dùng version trong tuning._contract_version, có keyword override `contract_version="1.2"` cho test nội bộ. Không suy version từ hình dạng hold.
- Ở v1.2, hold là list cá thể. Ngày 1 reserve mọi ID fixture trong allocator trước nhặt mới. Mỗi nguyên liệu nhận một I mới theo thứ tự vào giỏ; đủ chỗ mới cấp ID.
- Hải cần giữ **cùng IdAllocator** xuyên pha và Ngày. Khi day>1, truyền lại mẫu hold gốc; GatherSim tự cấp ID mới theo thứ tự mảng, giữ kind/fresh ban đầu. Không cấp lại ID cho mẫu trước khi gọi GatherSim, sẽ gây hai lượt cấp không cần thiết. ID đã dùng/mất không được trả về allocator.
- Bàn giao `inventory_items()` là list được sao/sắp ID, không hao tươi khi gọi. DaySession mở quán cùng tick với inventory này và chỉ chạy quán từ bước sau.
- Timer/hồi nút → hao hàng có sẵn đầu bước → bơi/oxy/ngạt → quái/hit → bến/hái → bắt cá → hết giờ → cá bơi/sinh. Hàng vừa nhận giữ fresh=initial cho tới bước gameplay sau. Pause phải chặn step như Phase 2.
- `spoiled`: `{item_id,kind,location:"hold"}` đúng một lần khi đi từ fresh>=30 xuống <30, theo ID. 30 còn dùng được; chỉ <30 là ươn. Không loại hàng ươn khỏi giỏ.
- monster_hit/faint.lost là list cá thể theo LIFO, dùng giá trị đã hao ở đầu bước. Nếu hit chết: monster_hit bỏ nửa giỏ rồi faint bỏ phần còn lại, không lặp cá thể. Ngất xuất `{items:[]}`.
- monsters.py không cần đổi: phần quái chỉ quản chuyển động/hit candidate, GatherSim giữ quyền mất hàng như Phase 2.

## Độ chính xác dùng chung cho Hải

`inventory.FreshnessTracker(tuning)` giữ bộ đếm chính xác riêng cho hold/stock:

```python
tracker = FreshnessTracker(tuning)
events = tracker.decay(stock_items, location="stock",
                      rate=tuning["freshness"]["quan_decay_per_s"])
```

- Chỉ gọi đầu bước gameplay, không gọi lúc dựng pha, pause hoặc Shop. Trả event tuple `(name,data)` theo ID, cập nhật fresh trên từng dict tại chỗ. Chưa xử lý reserved/nấu/giá; phần đó thuộc quan.
- `FRESH_SCALE=240` là đơn vị biểu diễn. Chuẩn rate gather tương ứng 2 đơn vị/tick và stock 1 đơn vị/tick. `tracker.units[item_id]` là giá trị chính xác hiện tại (integer với fixture chuẩn, Fraction khi fixture khác lưới).
- Helper `fresh_units(value)` và `fresh_value(units, spoiled_below)` dùng để đổi giữa số public và đơn vị nội bộ. Tính so ngưỡng/floor bằng đơn vị chính xác, không lấy số đã làm tròn từ UI/JSONL. Có thể tính avg_fresh từ tổng units chia số cá thể và FRESH_SCALE trước floor giá.
- Trường fresh xuất đủ precision với phía ngưỡng giữ đúng khi đọc lại; jsonl._clean chỉ tiếp tục làm tròn tọa độ/số float khác tới 3 chữ số. Không phát spoiled cho cá thể vốn đã ươn từ pha trước.

## Việc cần đồng đội nối trước khi bật v1.2

| Chủ phần | Phụ thuộc |
|---|---|
| Hải | stock/reserved cá thể, giữ lại khi ươn, consume đúng ID, giá/boa, Shop list không hao; shared allocator và mẫu gather mỗi Ngày; CHANGELOG |
| Hùng | scenario.hold/stock/reserved theo cá thể, duy nhất ID vật lý giữa nơi chứa, validation version từ tuning._contract_version; test smoke v1.2 và cập nhật fixture/regression đếm |
| Bảo | Hold/stock/lost là list cá thể, fresh dưới 30 cảnh báo; đọc snapshot mới, không tự hao tươi |

`tests/test_gather_p3.py` kiểm nhánh v1.2 của Minh bằng manifest ứng viên; test CLI sao chép package vào thư mục tạm và bật v1.2 ở đó. Chưa coi thử adapter stock là kiểm chứng quan thật. Chưa bật current/reservations hoặc mở rộng khác.
