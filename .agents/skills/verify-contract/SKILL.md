---
name: verify-contract
description: Kiểm tra hợp đồng `game.contract.json`, danh sách thành viên `TEAM.md` và bộ test trước khi merge hoặc gắn tag phase.
---

# Skill: Verify Contract & Tests

Dùng trước khi mở PR, merge vào `main`, hoặc gắn tag `phase-1`..`phase-4`.

## Các bước kiểm tra
1. Kiểm tra danh sách thành viên khớp `team_size`:
   ```bash
   python3 tools/check_team.py
   ```
2. Chạy bộ kiểm thử (Windows PowerShell dùng `$env:PYTHONPATH="tests;."`, Linux/macOS dùng `PYTHONPATH=tests:.`):
   ```bash
   PYTHONPATH=tests:. python3 -m unittest discover -s tests -v
   ```
3. Kiểm tra nhanh headless cho `gather`, `quan`, `day`:
   ```bash
   python3 -m chonoi.headless --mode gather --seed 1 --ticks 600 --out /tmp/g.jsonl
   python3 -m chonoi.headless --mode day --days 1 --seed 1 --ticks 600 --out /tmp/d.jsonl
   ```
4. Không thay đổi khóa trong `game.contract.json` hoặc schema kho khi chưa báo cả nhóm.
