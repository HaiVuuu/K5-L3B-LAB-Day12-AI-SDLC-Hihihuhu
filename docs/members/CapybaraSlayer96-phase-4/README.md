# Bảo (CapybaraSlayer96) — bằng chứng Phase 4

Phần được giao theo `docs/plan/phase-4.md`: `chonoi/bench.py`, ba cảnh báo và chế độ tương phản cao trong `chonoi/web/index.html`, `docs/clarify.md`. QA (Hùng) chép artifact cần thiết sang `docs/proof/phase-4/`.

## Bench

```bash
python3 -m chonoi.bench --seed 42 --duration 30 --out bench.json
```

Kết quả máy dev, Windows 11, Edge 157 headless, Python 3.14: [bench.json](bench.json)

```json
{"avg_fps": 58.16, "p1_low_fps": 12.18, "frames": 1746, "measured_s": 30.022, "load_ms": 2778}
```

- Đạt mốc load ≤ 10 s. Chưa đạt 60 FPS avg (58.16, sát vsync 60 Hz của headless) và chưa đạt 30 FPS ở 1% low. Có vài khung bị giật; chưa điều tra nguyên nhân.
- Số này đo trên máy dev, không phải commit gắn tag. QA cần đo lại trên commit bàn giao.
- Cần có Chrome, Chromium hoặc Edge. Không tìm thấy trình duyệt thì lệnh trả mã 1 và không ghi file. Đặt `CHONOI_BROWSER=<đường dẫn>` để chỉ định trình duyệt.

## Cảnh báo và tương phản cao

Bật tương phản cao bằng phím **H** (lưu trong localStorage) hoặc thêm `?hc=1` vào URL.

| Cảnh báo | Điều kiện | Ảnh (tương phản cao) |
|---|---|---|
| Thủy quái gần / đang đuổi | Monster `chase`, hoặc khoảng cách ≤ `detect_radius` của loài (đọc từ contract) | [monster-hc.png](monster-hc.png), bình thường: [monster-normal.png](monster-normal.png) |
| Oxy sắp hết / Hết hơi | Đang dưới nước và oxy < 25% (CL-07), hoặc oxy = 0 | [oxy-hc.png](oxy-hc.png), bình thường: [oxy-normal.png](oxy-normal.png) |
| Khách sắp giận | Khách `waiting` có kiên nhẫn < 25% | [quan-hc.png](quan-hc.png), bình thường: [quan-normal.png](quan-normal.png) |

Ảnh chụp theo đồ họa chợ nổi (commit `d3ef384`).

Mỗi cảnh báo có chữ và biểu tượng tam giác "!" vẽ bằng canvas (không phụ thuộc font emoji). Ở chế độ tương phản cao, cảnh báo là khung vàng, chữ đen, viền trắng/đen dày. Viền đuổi đổi sang nét đứt trắng, nên vẫn nhận ra được mà không cần phân biệt màu.

Ảnh chụp tự động bằng Edge headless, chạy `chonoi.live --no-menu --scenario` với các file sau: [oxy](scenario-oxy.json), [thủy quái](scenario-monster.json), [quán](scenario-quan-warnings.json). Đây là bằng chứng render. **Chưa phải phần chơi thử thủ công** mà spec yêu cầu; Bảo cần tự chơi cả ba cảnh báo ở chế độ tương phản cao.

## Test

- `tests/test_bench_p4.py`: 4 test (công thức FPS và mã thoát 0/1/2), không cần trình duyệt.
- Toàn bộ suite có 35 fail/error, đều đã có sẵn trên `main` trước thay đổi này (đã so danh sách khi stash, trùng khớp). Chúng thuộc phần regression đang chờ migration, không phải module của Bảo.
