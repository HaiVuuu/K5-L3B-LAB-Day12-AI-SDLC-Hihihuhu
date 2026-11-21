# Bàn giao hợp đồng v1.1 — phần Minh

Nguồn: [TICKET-02 người dùng cung cấp](../requirements/phase-2.txt), mục 1–2 và 4. Bản này bổ sung [hợp đồng Phase 1](README.md). Thay đổi đã được phân công cho Integrator trong `docs/plan/phase-2.md`; không đổi vỏ file kho.

## Cấu hình và input dùng chung

- `game.contract.json`: `contract_version:"1.1"`. Dữ liệu dưới `tuning`: `gather`, `quan`, `menu`, `day_plan`, `shop`, `score`, `tick_hz`.
- `gather.fish_initial` là số **8** (không còn mảng). Thêm các map/timer `fish_*`, hai nút N5/N6, ca_keo yield 2; cá sinh qua `Streams`, id qua `IdAllocator`.
- `gather.monsters.species.ca_sau`: `depths:[10,30]`, hai tốc độ, hai bán kính phát hiện/rời chase, bán kính hit, `recoil_ticks:60`, `recoil_dist:2.0`. recoil_dist là tổng quãng lùi 2 m trong 60 bước (2/60 m mỗi bước trước chặn mép). `spawns` có M1 từ D1 và M2 từ D3; `invuln_ticks:90`, `loss_ratio:0.5`.
- Hai bếp, bốn bàn và sáu món được khai trong dữ liệu. `tuning.day_plan` là mảng D1–D5 có `day,dishes,ingredients`; ingredients tính từ công thức. `tuning.shop` có `max_ticks:600` và `upgrades.oxygen[]/hp[]` theo cấp.
- `inventory.KINDS_P2` có sáu nguyên liệu; `validate_items`/`read_inventory` mặc định dùng tập này. `KINDS_P1` giữ nguyên bốn loại cho code/test v1.0 chủ động yêu cầu.
- `inputs.BUTTONS_V11` là mặc định: interact/catch/pause/shop_done/attack/photo. attack/photo đúng kiểu được đọc, sim lõi bỏ qua khi không bật mở rộng. `BUTTONS_V10` vẫn dùng được khi truyền tường minh.
- `InputState.buy` là chuỗi ở đúng frame, mặc định None và không kế thừa; `pressed()` vẫn chỉ nhận cạnh lên. `LiveInputs.set(buy="oxygen")` giữ một lệnh tới lần advance kế. Engine day/pause của Hải chịu trách nhiệm bỏ hành động khi pause/sai pha; parser không tự chạy Shop.

`chonoi/contract.py` cũng được cập nhật vì validator starter chỉ nhận mảng sáu cá và hai loại nút, sẽ từ chối manifest v1.1. Giữ nhánh đọc cấu hình v1.0; kiểm cấu trúc cấu hình v1.1, dữ liệu cá/quái/nâng cấp và tổng nguyên liệu kế hoạch. Không sửa runner/headless/scenario/live hoặc sim/quan của người khác.

## API gather để Hải tích hợp day

```python
sim = GatherSim(tuning, gather_fixture, streams, ids,
                day=day_number, active_upgrades=active_upgrades)
```

- Bốn tham số cũ vẫn dùng được. Mặc định `day=1`, cấp cơ sở; standalone chỉ có M1.
- `day` lọc quái mặc định theo from_day. `scenario.monsters` khi có sẽ thay hẳn danh sách; [] tắt quái.
- Cấp `active_upgrades` được sao khi khởi tạo, không đọc map cấp đã mua trong Shop. oxygen 0/1/2 → 1800/2700/3600 tick; hp 0/1/2 → 3/4/5. Snapshot dùng maxima đang hiệu lực. Fixture player có thể ghi đè giá trị hiện tại sau khi dựng maxima.
- Cần truyền cấp active và số Ngày mỗi lần dựng gather mới; giữ Streams/IdAllocator trong lượt để RNG và id sinh liên tục. Không gọi `GatherSim.step` trong bước đang pause; resume mới chạy step. Gather tự tăng phase_tick khi được gọi.
- `inventory_items()` trả map hàng còn trong giỏ; `gather_end.data.inventory` bọc `{items:...}` như v1.0. Ngất trả rỗng; DaySim vẫn phải mở quán sau đó.
- Vỏ day/day_plan/upgrades/active_upgrades và việc chuyển pha thuộc DaySim/runner; gather chỉ cung cấp snapshot/event của pha.

## Snapshot / sự kiện thêm

- `fish[]`: `id,kind,pos,heading_deg,age_ticks`. Khi random_fish:false: không sinh mặc định, không bơi/sinh lịch, cá fixture giữ nguyên cả age. Khi true và có fish fixture: thay đàn đầu, tiếp tục bơi/sinh.
- `monsters[]`: `id,kind,pos,waypoints,target_idx,state,state_ticks_left,recoil_dir`; sắp theo id. `player.invuln_ticks` giảm trước cập nhật quái.
- `fish_spawned`: `{id,kind,pos}`; newborn age 0, chỉ bơi từ bước sau. Đầu ca không phát fish_spawned.
- `monster_hit`: `{monster_id,hp,lost,pos}`; pos của người chơi, lost theo LIFO, tối đa một hit/bước. Ngạt xuyên bất tử và không làm rơi hàng nếu còn sống.
- `faint`: `{cause:"monster"|"choke",lost,hp:0}`; lost là phần còn lại sau monster_hit. Sau đó gather_end(fainted) ngay.
- Quái bơi/hit sau oxy, trước bến/hái/bắt. Bắt xét vị trí cá cũ; nếu ca còn giờ mới bơi cá rồi sinh ở phase_tick 360·k.

## Phụ thuộc cần đồng đội tích hợp

| Chủ module | Việc cần nối |
|---|---|
| Hải | Dựng GatherSim với day/active_upgrades; giữ input latch xuyên pha; pause chặn step; nhận inventory_items khi ngất; đọc tuning.day_plan/shop; CLI day/days và Shop theo ticket |
| Hùng | scenario.py: dùng KINDS_P2, thêm ca_keo/keo_neo, monsters và fish.age_ticks; kiểm fixture theo maxima nâng cấp trong day; nâng các smoke cấm mode day của P1 khi CLI day đã có |
| Bảo + Hải | Đọc monsters/player maxima/cấp active; input pause/buy; hiển thị cá/quái, HUD/cảnh báo. LiveInputs đã có nút mới, nhưng live.py.set_input hiện chỉ chuyển interact/catch; cần nối endpoint khi tích hợp UI/day |

Hiện parser của QA chưa nhận monsters/age_ticks/ca_keo/keo_neo fixture; test module dùng trực tiếp sim để không sửa file độc quyền của Hùng. CLI mặc định v1.1 và bàn giao kho thật với hai nguyên liệu mới đã được kiểm. Chưa xác nhận day/Shop/pause/UI hoặc toàn bộ DoD Phase 2.

## Điều chỉnh regression có lý do

1. Snapshot mặc định đọc số lượng từ fish_initial (v1.1 là 8), thay assertion cố định 6 của v1.0 (Ticket §4.1).
2. Test nút attack bị từ chối của v1.0 truyền BUTTONS_V10 tường minh; smoke v1.1 vẫn từ chối nút lạ, nhận attack/photo đúng kiểu để bỏ qua khi mở rộng chưa bật (Ticket §4.2).
3. Fixture test_gather.py đặt random_fish:false và monsters:[] để tiếp tục kiểm riêng luật/cooldown Phase 1 với cá đứng yên. Test cá bơi và quái ở test_gather_p2.py.
4. Sau khi gộp main có vòng day của Hải: smoke mode day kiểm theo contract_version (v1.0 từ chối, v1.1 chạy được), thay việc luôn coi day là mode tương lai. Parser giữ keyword allow_buy của CLI Hải; mặc định suy từ bộ nút, truyền False vẫn từ chối buy.

Chạy `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v`. Kết quả phần Minh và nguồn nhật ký AI riêng ở `docs/members/minhh25.md`; QA tổng hợp vào bằng chứng chính của Phase 2 sau tích hợp.
