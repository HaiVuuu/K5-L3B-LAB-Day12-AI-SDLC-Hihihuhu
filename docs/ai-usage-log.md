# Nhật ký dùng AI (theo phase và theo người)

| Phase | Người | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|---|
| 1 | Nguyễn Đình Minh (minhh25) | Codex; model/token/chi phí không được công cụ báo, không ước đoán | Đọc toàn bộ Markdown repo và PRD-0 do người dùng gửi; viết luật gather, 23 test, 2 command kiểm, hợp đồng tích hợp và bằng chứng | Không đo được | Bản nháp trước khi có PRD dùng qty; đối chiếu mục E sửa thành amount/yield và bổ sung faint.lost LIFO. Test HTTP ban đầu bị sandbox chặn cổng, chạy lại đủ quyền đạt. Không ghi nhận con người đã review. |
| 1 | Vũ Tiến Hùng (hungvueducation-hash) | Claude Code (Sonnet 5.5); token/chi phí không được công cụ báo, không ước đoán | Đọc `sim/*`, hợp đồng kho, smoke P1; viết `tests/test_integration.py`; chạy regression P1 và đo tốc độ headless; tìm nguyên nhân test hái nút | Không đo được | Test hái nút đặt `regrow_ticks: 600` nên nút chưa mọc, kho rỗng; chạy tay headless xác định lỗi ở test, đã sửa. Chưa có review chéo bởi người khác. |
