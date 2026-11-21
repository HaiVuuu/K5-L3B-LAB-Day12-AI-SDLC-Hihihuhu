# Hợp đồng tích hợp Phase 1 — Test Contract v1.0

Người ghi: Nguyễn Đình Minh (Integrator), 2026-11-21. Nguồn: [PRD-0 mục D–G](../requirements/phase-1.txt) do người dùng cung cấp trong phiên làm việc. Đây là bản ghi lại contract hiện hành, không đổi schema, preset hay API starter. Cần các chủ module đọc chéo trước khi gộp; chưa ghi nhận cả nhóm duyệt.

## Kho: gather → quan

```json
{"items":{"bong_sung":2,"ca_loc":1}}
```

- Gốc có đúng khóa `items`; giá trị là object kind → số nguyên không âm, không nhận boolean. Kind hợp lệ: `ca_loc`, `ca_linh`, `bong_dien_dien`, `bong_sung`.
- Thiếu kind tính là 0; bên ghi bỏ lượng 0 và sắp khóa. Kho rỗng: `{"items":{}}`. Ví dụ: [inventory.sample.json](inventory.sample.json).
- Chỉ xuất hàng còn trong giỏ khi có `gather_end`, đúng một lần trong lượt headless; nội dung phải khớp `gather_end.data.inventory`. Ngất xuất rỗng.
- Chạm giới hạn `--ticks` khi gameplay chưa kết thúc: không tạo/ghi đè kho. Ghi qua file tạm cùng thư mục rồi thay thế nguyên tử (`chonoi/inventory.py`).
- `--inventory-out` chỉ ở gather; `--inventory` chỉ ở quan. Quan thiếu file và scenario.stock thì kho rỗng. Không đồng thời khai file và scenario.stock. Dữ liệu sai → mã 2 trước ghi đầu ra.
- Kho quán gồm cả nguyên liệu đang được giữ chỗ; khả dụng = tồn vật lý trừ phần giữ. Trần giỏ không áp lên kho quán.

## Sim ↔ UI

`Session` dùng chung cho headless và live: `step(InputState)` trả event; `snapshot()` trả trạng thái. UI chỉ đọc snapshot và gửi input, không tự áp dụng luật/đổi kho.

| API live | Dữ liệu |
|---|---|
| `GET /state` | Snapshot + metadata live hiện có (xem `chonoi/live.py`) |
| `POST /input` | `move:[x,d]` hoặc `[x,z]`, `interact:boolean`, `catch:boolean` |
| `POST /restart` | Khởi động lại theo cấu hình live hiện có |

Nút chỉ tác động ở cạnh lên. Vector dài hơn 1 được chuẩn hóa; trường vắng giữ giá trị cũ. `d` dương là xuống; `z` dương là bắc. Headless 60 Hz; snapshot tick 0, mỗi chu kỳ và tick cuối, event trước snapshot. Thực thể sắp bằng `ids.sort_by_id`, tọa độ xuất 3 chữ số; tính khoảng cách trước làm tròn và nhận đúng mép bán kính.

Snapshot chung: `type,tick,sim_tick,mode,phase,phase_tick,state,time_left_ticks,money,earned,reputation,score`.

| Mode | Trường UI đọc |
|---|---|
| gather | `player.pos,vel,heading_deg,oxygen_ticks,oxygen_max_ticks,hp,hp_max,zero_oxy_ticks,catch_cd_ticks,at_surface`; `hold,hold_count,hold_capacity`; `nodes[].id,pos,kind,ready,regrow_ticks`; `fish[].id,pos,kind,heading_deg` |
| quan | `player,stock,hand,stoves,tables,customers`; bàn có `customer_id` (null nếu trống); payload món `{order_id,dish_id,base_price}` |

`hold` theo thứ tự nhặt, mới nhất ở cuối. Thời gian và sự kiện dùng số tick nguyên. `score = earned + tuning.score.reputation_multiplier × floor(reputation)`.

## Sự kiện

Envelope: `{type:"event",tick,phase,name,data}`. Sim phát, runner ghi JSONL, live chuyển cho UI. UI/QA có thể đọc nhưng không sửa luật theo event. Bảng quán mô tả đích theo PRD; không phải xác nhận phần quán đã triển khai.

| name | data |
|---|---|
| gather | `node_id,kind,amount` |
| node_regrown | `node_id` |
| hold_full | `action` (gather/catch), `node_id` hoặc `fish_id`, `required,free` |
| fish_caught | `fish_id,kind,yield` (một event/đàn, nhận đủ yield) |
| dive / surface | `pos` sau di chuyển, chỉ khi đổi phía mặt nước |
| oxygen_empty | `oxygen_ticks:0`, chỉ từ dương xuống 0 |
| choke | `hp` sau trừ |
| faint | `cause:"choke",lost,hp:0`; lost là mảng kind theo LIFO |
| gather_end | `reason` (time/docked/fainted), `inventory` theo schema kho |
| customer_arrived | `order_id,table_id,dish_id` |
| no_dish | `{}` |
| cook_started | `stove_id,order_id,dish_id,items,base_price`; items là mảng kind sắp theo kind |
| dish_ready / dish_picked | `stove_id,order_id,dish_id` |
| served | `order_id,table_id,dish_id,patience_ticks_left,base_price,tip` |
| paid | `order_id,table_id,base_price,tip,amount,reason` (finished_eating/closing) |
| customer_left | `order_id,table_id,reason` (patience/closing), `reputation` |
| quan_end | `reason:"time",money,earned,shift_earned,reputation` |

Thứ tự gather: timer/mọc lại theo id → bơi → dive/surface → oxy/ngạt/ngất → bến/hái → bắt cá → hết giờ. Ngất chặn hành động còn lại; bến ưu tiên hơn hái/hết giờ. Hái/bắt ở bước cuối vẫn vào kho. Cooldown L đặt ở t dùng lại từ t+L.

## Lệnh kiểm tích hợp

```bash
python3 tools/check_gather.py
python3 tools/check_gather_replay.py
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v
```

Replay gồm mẫu cập bến của PRD và ba tình huống hái/bắt/ngất, so byte hai lượt cùng seed và cho tiến trình quan đọc kho thật. Xem [bằng chứng của Minh](../proof/phase-1/minh/README.md). Đổi contract về sau phải báo nhóm và ghi lý do/ADR trước sửa.
