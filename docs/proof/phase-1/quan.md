# Proof Phase 1 — `sim/quan` (Nguyễn Đình Vũ Hải)

## Lệnh chạy kiểm chứng (reproducible)

### Windows (PowerShell)
```powershell
$env:PYTHONPATH="tests;."
python -m unittest tests/test_quan.py tests/test_live.py tests/test_python_starter_units.py -v
python -m chonoi.headless --mode quan --seed 1 --ticks 600 --out out.jsonl
```

### Linux / macOS (bash)
```bash
PYTHONPATH=tests:. python3 -m unittest tests/test_quan.py tests/test_live.py tests/test_python_starter_units.py -v
python3 -m chonoi.headless --mode quan --seed 1 --ticks 600 --out out.jsonl
```

### Chơi thử trên trình duyệt
```bash
python -m chonoi.live --mode quan --seed 1
```

> Lưu ý: Xóa file tạm `out.jsonl` sau khi chạy xong để tránh commit nhầm vào git.

## Kết quả đã kiểm chứng
- `unittest` (`test_quan.py`, `test_live.py`, `test_python_starter_units.py`): **11/11 tests passed (`OK`)**.
- `chonoi.headless --mode quan --seed 1 --ticks 600`: **exit code 0**.
