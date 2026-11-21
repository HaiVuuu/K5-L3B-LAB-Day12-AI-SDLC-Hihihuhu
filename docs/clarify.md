# Clarify — câu hỏi và câu trả lời (PO ghi, cả nhóm dùng chung)

| # | Ngày giờ | Câu hỏi | Trả lời / giả định | Ai quyết |
|---|---|---|---|---|
| CL-01 | 2026-11-21 | Repo chỉ có link lab board, chưa có PRD-0 đầy đủ; phần Minh thuộc phase nào? | Đã nhận PRD-0/Test Contract v1.0 từ người dùng; phần được giao hiện tại là lát 1–2, sim/gather + Integrator theo kế hoạch Phase 1. Chưa có Ticket-02/03/04 nên chưa suy diễn việc các phase sau. | Phân công TEAM.md + docs/plan/phase-1.md, PRD người dùng cung cấp |
| CL-02 | 2026-11-21 | Thiếu chỗ cho cả đàn cá, bắt hụt và payload sự kiện xử lý thế nào? | Đã rõ ở PRD E/F: nhận nguyên yield hoặc hold_full, giữ đàn/cooldown, không thử đàn khác; hụt không hồi chiêu. gather dùng amount, fish_caught dùng yield; faint.lost theo LIFO. Đã bỏ payload qty tạm khi đối chiếu. | PRD-0 E/F, không cần giả định |
| CL-03 | 2026-11-21 | Có thể gắn phase-1 chỉ vì smoke test xanh? | Chưa đủ: quan.py còn TODO luật lõi, TEAM.md còn thiếu handle của ba người; chưa có kiểm chứng chơi/review toàn nhóm trên main. Chưa gắn tag, không xác nhận deadline hay collaborator khi chưa có bằng chứng. | DoD PRD-0 mục 7 + trạng thái repo thực tế |
