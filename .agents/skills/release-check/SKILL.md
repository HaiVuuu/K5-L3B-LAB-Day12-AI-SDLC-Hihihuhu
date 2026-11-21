---
name: release-check
description: Kiểm tra sẵn sàng phát hành v1.0.0: soak 10 ngày, bench render, check_release và đóng gói zip.
---

# Skill: Release Check (`v1.0.0`)

Dùng ở Phase 4 trước khi gắn tag `phase-4` và công bố GitHub Release `v1.0.0`.

## Các bước kiểm tra
1. Chạy kiểm tra tổng hợp phát hành:
   ```bash
   python3 tools/check_release.py --measure --out dist/release-status.json
   ```
2. Chạy soak 10 ngày độc lập:
   ```bash
   python3 -m chonoi.soak --seed 7 --days 10 --out dist/soak.json
   ```
3. Chạy benchmark render 1280×720:
   ```bash
   python3 -m chonoi.bench --seed 42 --duration 30 --out dist/bench.json
   ```
4. Đóng gói bản phát hành:
   ```bash
   python3 tools/package_release.py --out dist/chonoi-v1.0.0.zip
   ```
5. Đảm bảo tag `phase-4` và Release `v1.0.0` trỏ tới cùng một commit trên `main`.
