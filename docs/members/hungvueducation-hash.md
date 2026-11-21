# hungvueducation-hash — phản tư cá nhân Phase 1 (≤ 200 từ)

Bản nháp do Claude Code ghi theo công việc thực tế trong phiên; Hùng cần tự xác nhận và chỉnh lại phần phản tư trước khi nộp.

- Tôi đã làm (kèm link commit): điền handle vào `TEAM.md` ([33cffac](https://github.com/HaiVuuu/K5-L3B-LAB-Day12-AI-SDLC-Hihihuhu/commit/33cffac)); dựng `tests/test_integration.py` cho chuỗi gather → kho → quan, tất định theo seed ([72d0b6d](https://github.com/HaiVuuu/K5-L3B-LAB-Day12-AI-SDLC-Hihihuhu/commit/72d0b6d)); gỡ `expectedFailure` sau khi lõi gather xong ([4f9103f](https://github.com/HaiVuuu/K5-L3B-LAB-Day12-AI-SDLC-Hihihuhu/commit/4f9103f), [5685495](https://github.com/HaiVuuu/K5-L3B-LAB-Day12-AI-SDLC-Hihihuhu/commit/5685495)). Hiện 8 test chạy, 2 test quán còn `skip` chờ lõi `sim/quan`.
- Tôi đã review (kèm link): chưa có review chéo có bằng chứng. Mới chỉ đọc `chonoi/sim/*` và `docs/contracts/` để viết test, chưa review PR của Minh hay Hải.
- AI sai ở đâu và tôi phát hiện thế nào: test hái nút dùng `regrow_ticks: 600` trong kịch bản; đó là bộ đếm còn lại nên nút bị coi là chưa mọc, kho ra rỗng. Phát hiện bằng cách chạy tay headless, so hai kịch bản có/không có trường này; lỗi ở test, không ở `gather.py`.
- Điều học được: test `expectedFailure` giúp biết khi nào lõi xong, nhưng phải tách "lõi chưa làm" khỏi "test sai" trước khi tin kết luận.
