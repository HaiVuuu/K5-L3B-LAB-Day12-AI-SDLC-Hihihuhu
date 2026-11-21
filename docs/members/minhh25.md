# minhh25 — phần việc Phase 1

Bản nháp do Codex ghi theo công việc thực tế trong phiên; Minh cần tự xác nhận phần phản tư và review trước nộp.

- Đã thực hiện: lát 1–2 và 23 test (`2760cdc`); hai command kiểm gather/replay + AGENTS (`c3fa73b`); tài liệu tích hợp và log trong commit bàn giao tiếp theo. Nhánh `codex/minh-gather-phase1`; chi tiết đối chiếu `git log` và `docs/proof/phase-1/minh/README.md`.
- Review: Codex tự rà diff theo PRD E–G; chưa có bằng chứng Minh hay thành viên khác đã đọc chéo. Cần Hải review trước gộp.
- AI sai: bản nháp thiếu PRD dùng `qty` cho sự kiện. Khi nhận Test Contract, đối chiếu mục E cho thấy phải là `amount`/`yield` và `faint` phải có đồ mất LIFO. Đã sửa, thêm assertion kiểm payload chính xác.
- Gợi ý điều học được để Minh tự xác nhận: smoke xanh chưa chứng minh đủ luật; cần kiểm tick oxy vừa về 0, deadline hồi chiêu, nổi lên đúng lúc ngạt và ưu tiên cập bến ở tick cuối.
- Kiểm chứng thật: 55 test đạt; replay 4 fixture cùng seed giống byte và kho được tiến trình quán đọc đúng. Chưa xác nhận toàn bộ DoD nhóm hoặc các phase sau.
