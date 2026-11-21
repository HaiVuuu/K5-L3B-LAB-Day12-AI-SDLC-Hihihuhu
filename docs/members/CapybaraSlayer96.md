# CapybaraSlayer96 — phản tư cá nhân (≤ 200 từ, bản nháp chờ Bảo xác nhận)

- Tôi đã làm (Phase 4, nhánh `doanxuanduybao`):
  - `0b19e4f`: ba cảnh báo có chữ và biểu tượng (thủy quái gần, oxy sắp hết, khách sắp giận) và chế độ tương phản cao (phím H, `?hc=1`).
  - `63cdef9`: `chonoi/bench.py` đo FPS trong trình duyệt headless ở 1280×720, kèm 4 test.
  - `6128669`: CL-10, nhật ký AI, ảnh và [bench.json](CapybaraSlayer96-phase-4/README.md).
  - UI Phase 1–3 do Hùng làm thay; tôi không nhận phần đó.
- Tôi đã review/hỗ trợ: Bảo tự điền.
- AI sai ở đâu và tôi phát hiện thế nào: Claude Code đặt oxy thấp và thủy quái chung một kịch bản chụp ảnh. Ảnh ra lúc Út Sen đã ngất, cảnh báo vẫn đè lên màn kết thúc. Tôi xem ảnh thì phát hiện; AI sửa để ẩn cảnh báo khi buổi kết thúc và tách kịch bản.
- Điều tôi học được: Bảo tự điền.

Bench máy dev: avg 58 FPS, 1% low 12 FPS, chưa đạt mốc 60/30. Chưa chơi thử thủ công ba cảnh báo.
