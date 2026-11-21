# Proof Phase 2 — `sim/quan` & `day` (Nguyễn Đình Vũ Hải)

## Lưu ý môi trường Windows vs Linux/macOS
Không phải lỗi riêng máy bạn — **mọi thành viên dùng Windows PowerShell** đều cần lưu ý 2 điểm khi chạy lệnh trong `README.md`/`AGENTS.md`:
1. PowerShell không hỗ trợ `PYTHONPATH=tests:.` viết liền trên một dòng và dùng dấu `;` thay vì `:`, nên phải đặt `$env:PYTHONPATH="tests;."`.
2. Trên Windows, `python3` có thể trỏ vào Windows Store alias (`WinError 1920`); dùng `python` khi chạy tay (giữ `python3` trong `game.contract.json` cho Linux CI).

## Lệnh chạy kiểm chứng (reproducible)

### Windows (PowerShell)
```powershell
$env:PYTHONPATH="tests;."
python -m unittest tests/test_quan.py tests/test_quan_p2.py tests/test_live.py tests/test_python_starter_units.py -v
```

### Linux / macOS (bash)
```bash
PYTHONPATH=tests:. python3 -m unittest tests/test_quan.py tests/test_quan_p2.py tests/test_live.py tests/test_python_starter_units.py -v
```

## Kết quả đã kiểm chứng
- `unittest` (`test_quan.py`, `test_quan_p2.py`, `test_live.py`, `test_python_starter_units.py`): **14/14 tests passed (`OK`)**.
