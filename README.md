# Quán Ăn Chợ Nổi — Hihihuhu

Game lab Day 12: Út Sen lặn/hái, mở quán rồi mua nâng cấp cho Ngày sau. Python chuẩn và giao diện Canvas trong trình duyệt, nhóm 4 người.

**Bản chuẩn bị phát hành, chưa công bố v1.0.0.** Contract v1.3 giữ gameplay/kho cá thể/độ tươi v1.2. Trạng thái thật và điều kiện còn thiếu: [bàn giao phần Minh](docs/members/minhh25-phase-4/README.md).

## Chạy từ clone sạch — 3 lệnh

Yêu cầu Git, Python **3.10+** với lệnh `python3`, trình duyệt hỗ trợ Canvas (Chrome/Firefox/Safari). Không cần pip hoặc API key. Kiểm chứng hiện dùng Python 3.13 trên macOS; CI khai Python 3.12 trên Linux.

```bash
git clone https://github.com/HaiVuuu/K5-L3B-LAB-Day12-AI-SDLC-Hihihuhu.git
cd K5-L3B-LAB-Day12-AI-SDLC-Hihihuhu
python3 -m chonoi.live --mode day --days 1 --port 0
```

Mở địa chỉ localhost được in ra, bấm **Chơi**. Port 0 chọn cổng trống; Ctrl+C trong terminal dừng server. Với ZIP Release: giải nén, cd vào thư mục có game.contract.json, chạy lệnh Python trên. Đổi thành `--days 5` để chơi D1–D5; chơi riêng bằng `--mode gather` hoặc `--mode quan` (bỏ --days).

## Điều khiển và luật chính

| Hành động | Phím / nút |
|---|---|
| Bơi / đi | WASD hoặc mũi tên; xuống là tăng độ sâu |
| Bến / hái / nấu / bưng / phục vụ | E |
| Bắt nguyên đàn trong tầm, cần đủ giỏ | Space |
| Pause / tiếp tục | Esc hoặc P |
| Chơi lại | R |
| Giới thiệu / kết quả | Nút tiếp tục hoặc Enter/Space |
| Shop | Nút mua oxygen/hp, Enter hoặc Xong để đóng |

HUD hiển thị oxy/Máu/thời gian/giỏ, độ tươi, kho, món/kiên nhẫn, bếp và tiền/uy tín. Fresh **<30** là ươn; đúng 30 còn dùng được. Hàng có sẵn hao đầu bước; hàng mới nhặt giữ 100 tới bước sau. Shop/pause không hao. Ngất mất giỏ và vẫn mở quán.

Điểm = `earned + 100 × floor(reputation)` theo tuning.score; tiền đơn vị nghìn đồng. Mua nâng cấp trừ money, giữ earned/điểm và áp từ Ngày kế.

## Test và headless

```bash
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v
```

```bash
python3 -m chonoi.headless --mode gather --seed 42 --ticks 600 --out gather.jsonl
python3 -m chonoi.headless --mode day --days 1 --seed 42 --ticks 22200 --out day.jsonl
```

Năm Ngày: `--days 5 --ticks 111000`. --ticks là trần, gameplay kết thúc thì dừng sớm. Input/scenario qua --inputs/--scenario. Gather độc lập xuất --inventory-out inventory.json; quan đọc --inventory inventory.json. Kho v1.3 là `{items:[{id,kind,fresh}]}`, kho đếm bị từ chối. Chỉ ghi khi gather_end; tick_limit giữ nguyên file. Mã thoát: 0 bình thường, 2 sai cờ/dữ liệu, 1 lỗi thực thi/ghi. Cùng seed + input + bản chạy cho output tất định.

## Bench và soak theo manifest

```bash
python3 -m chonoi.bench --seed 42 --duration 30 --out bench.json
python3 -m chonoi.soak --seed 7 --days 10 --out soak.json
```

Module do Bảo/Hải triển khai; lệnh kiểm phát hành bên dưới báo nếu còn thiếu. Bench cần render 1280×720, làm nóng 3s rồi đo 30s; không dùng số headless thay FPS. Báo cáo avg_fps, p1_low_fps, frames, measured_s, load_ms; mốc tham khảo 60/30 FPS, tải ≤10s. Soak phải đi qua đủ gather→quan→shop trong 10 Ngày/một tiến trình, D1–D5 lặp và giữ tiến trình xuyên Ngày.

## Đóng gói và phát hành

```bash
python3 tools/check_release.py --measure --out dist/release-status.json
python3 tools/package_release.py --ref main --out dist/chonoi-v1.0.0.zip
```

Lệnh kiểm lưu kết quả thật và trả 1 nếu còn điều kiện chưa đạt. --measure chạy bench/soak, so gameplay hai lượt soak bỏ duration_s; không bật cờ thì phép đo ở trạng thái chưa chạy. Vẫn cần QA kiểm UI/tương phản cao và clone sạch theo checklist.

ZIP lấy đúng commit Git chỉ định, không lấy file chưa commit; receipt JSON ghi SHA commit và SHA-256. Sau kiểm chứng trên main, tag phase-4 và v1.0.0 cùng commit, đính ZIP và [release notes](docs/releases/v1.0.0.md). Công cụ không tự tag/publish. [CREDITS](CREDITS.md) ghi nguồn và rà LICENSE.

## Giới hạn và bằng chứng

Bản chuẩn bị hiện còn thiếu bench/soak, có lỗi regression từ main trước Phase 4, thiếu hồ sơ thành viên và xác nhận LICENSE; chưa xác nhận UI tương phản cao. Theo dõi [báo cáo phần Minh](docs/members/minhh25-phase-4/README.md). README mô tả hợp đồng đích; chưa phải xác nhận DoD/phát hành toàn nhóm.

[TEAM](TEAM.md) · [Kế hoạch P4](docs/plan/phase-4.md) · [AI log](docs/ai-usage-log.md) · [Retro](docs/retro.md) · [Spec P4](docs/requirements/phase-4.txt) · [Hợp đồng kho](docs/contracts/phase-3.md). Starter: [VinUni-AI20k](https://github.com/VinUni-AI20k/K5-L3B-LAB-Day12-AI-SDLC).

## Sáng tạo của nhóm

Chưa khai mở rộng ngoài lõi. Ưu tiên đúng spec; phần tự thêm không được làm đổi tick, kho hoặc điểm headless.
