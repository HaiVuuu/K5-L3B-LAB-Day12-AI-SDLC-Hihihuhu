# Bảo (CapybaraSlayer96) — bằng chứng Phase 4

Phần được giao theo `docs/plan/phase-4.md`: `chonoi/bench.py`, ba cảnh báo và chế độ tương phản cao trong `chonoi/web/index.html`, `docs/clarify.md`. QA (Hùng) chép artifact cần thiết sang `docs/proof/phase-4/`.

## Bench

```bash
python3 -m chonoi.bench --seed 42 --duration 30 --out bench.json
```

Ba lượt 30 s liên tiếp trên máy dev (Windows 11, Edge 157 headless, Python 3.14), đồ họa chợ nổi + animation bơi:

| Lượt | avg_fps | p1_low_fps | frames | load_ms |
|---|---|---|---|---|
| [1](bench-run1.json) | 60.0 | 41.11 | 1801 | 2083 |
| [2](bench-run2.json) | 59.33 | 21.22 | 1780 | 1818 |
| [3](bench-run3.json) | 56.94 | 9.43 | 1709 | 3598 |

[bench.json](bench.json) là lượt 2 (trung vị theo avg_fps).

- Đạt mốc load ≤ 10 s ở cả ba lượt. avg_fps sát vsync 60 Hz nhưng chỉ lượt 1 chạm 60. 1% low dao động rất mạnh (9–41): chỉ lượt 1 đạt mốc 30. Máy dev đang chạy nhiều tiến trình khác; chưa tách được nguyên nhân giật là do game hay do máy, nên chưa kết luận là đạt.
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

Ảnh chụp tự động bằng Edge headless, chạy `chonoi.live --no-menu --scenario` với các file sau: [oxy](scenario-oxy.json), [thủy quái](scenario-monster.json), [quán](scenario-quan-warnings.json). Đây là bằng chứng render. Ngoài ảnh tự động, Bảo đã tự chơi thử cả ba cảnh báo ở chế độ tương phản cao: cả ba đều hiện đúng.

Chơi thử nên bỏ `--no-menu`: menu giữ sim đứng yên tới khi bấm Enter. Với `--no-menu`, sim chạy ngay khi bật server nên khách mất kiên nhẫn trước khi mở trình duyệt. `scenario-monster.json` cố ý đặt người chơi cách thủy quái 10 m để chụp cảnh báo; game thật đặt thủy quái M1 cách điểm xuất phát 62,8 m.

## Test

- `tests/test_bench_p4.py`: 4 test (công thức FPS và mã thoát 0/1/2), không cần trình duyệt.
- Toàn bộ suite có 35 fail/error, đều đã có sẵn trên `main` trước thay đổi này (đã so danh sách khi stash, trùng khớp). Chúng thuộc phần regression đang chờ migration, không phải module của Bảo.
