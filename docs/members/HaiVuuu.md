# HaiVuuu — phản tư cá nhân

- Tôi đã làm (kèm link commit):
  - Chia việc 4 thành viên tránh xung đột (`a3ea401`, `7446e0b`, `0f72810` trong `TEAM.md`, `docs/plan/phase-1..3.md`).
  - Triển khai `chonoi/sim/quan.py` (Phase 1–3), `chonoi/sim/day.py` (`DaySession`, `ShopSim`), cập nhật `runner.py`/`headless.py`/`inputs.py` cho `day` và `pause` (`88ebbd5`, `c048344`).
  - Viết unit test `tests/test_quan.py`, `tests/test_quan_p2.py`, `tests/test_quan_p3.py` và hướng dẫn tái lập (`docs/proof/phase-1/quan.md`, `docs/proof/phase-2/quan.md`).
- Tôi đã review:
  - Gộp và kiểm thử chéo code từ `main` (`gather.py`, `monsters.py`, `web/index.html`, `test_gather_p2.py`, `test_live_ui.py` từ PR #2, #6, #7), xác nhận 77/77 unit test xanh.
- AI sai ở đâu và tôi phát hiện thế nào:
  - AI tạo test thiếu tham số `edges` của `InputState`, dùng nhầm import tương đối trong `day.py`, và test khách rời bàn ban đầu trùng tick sinh khách mới. Chạy `unittest` phát hiện ngay và sửa lại chính xác.
- Điều tôi học được:
  - Khóa hợp đồng (`game.contract.json`) sớm và tách file test/proof riêng theo từng người giúp tích hợp nhiều nhánh mượt mà, không xung đột.

