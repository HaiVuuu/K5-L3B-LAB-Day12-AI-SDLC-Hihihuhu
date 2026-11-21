# hungvueducation-hash — phản tư cá nhân (≤ 200 từ)

Bản nháp do Claude Code ghi theo công việc thực tế; Hùng cần tự xác nhận và chỉnh lại trước khi nộp.

- Tôi đã làm (kèm link commit): handle trong `TEAM.md` ([33cffac](https://github.com/HaiVuuu/K5-L3B-LAB-Day12-AI-SDLC-Hihihuhu/commit/33cffac)); `tests/test_integration.py` gather → kho → quan ([72d0b6d](https://github.com/HaiVuuu/K5-L3B-LAB-Day12-AI-SDLC-Hihihuhu/commit/72d0b6d)), nay chạy trên cả contract 1.1 và 1.2; `scenario.py` + `test_scenario_qa.py` + `test_smoke_p3.py` cho kho cá thể ([PR #9](https://github.com/HaiVuuu/K5-L3B-LAB-Day12-AI-SDLC-Hihihuhu/pull/9)); `test_smoke_p4.py`, `docs/verification/phase-3.md` và `phase-4.md`.
- Tôi đã review (kèm link): chưa có review chéo có bằng chứng. Mới đọc `sim/*` và Ticket-03 để viết test.
- AI sai ở đâu và tôi phát hiện thế nào: nhận biết v1.2 bằng "có `freshness`" là sai, vì manifest chuyển tiếp có `freshness` mà vẫn ghi 1.1; phát hiện khi đọc Ticket-03 và ADR của Minh, rồi chạy lại trên bản thật.
- Điều học được: chạy test trên bản triển khai thật trước khi tin; ghi rõ mục nào chưa kiểm chứng.
