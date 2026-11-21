# minhh25 — phần việc Phase 1

Bản nháp do Codex ghi theo công việc thực tế trong phiên; Minh cần tự xác nhận phần phản tư và review trước nộp.

- Đã thực hiện: lát 1–2 và 23 test (`2760cdc`); hai command kiểm gather/replay + AGENTS (`c3fa73b`); tài liệu tích hợp và log trong commit bàn giao tiếp theo. Nhánh `codex/minh-gather-phase1`; chi tiết đối chiếu `git log` và `docs/proof/phase-1/minh/README.md`.
- Review: Codex tự rà diff theo PRD E–G; chưa có bằng chứng Minh hay thành viên khác đã đọc chéo. Cần Hải review trước gộp.
- AI sai: bản nháp thiếu PRD dùng `qty` cho sự kiện. Khi nhận Test Contract, đối chiếu mục E cho thấy phải là `amount`/`yield` và `faint` phải có đồ mất LIFO. Đã sửa, thêm assertion kiểm payload chính xác.
- Gợi ý điều học được để Minh tự xác nhận: smoke xanh chưa chứng minh đủ luật; cần kiểm tick oxy vừa về 0, deadline hồi chiêu, nổi lên đúng lúc ngạt và ưu tiên cập bến ở tick cuối.
- Kiểm chứng thật: 55 test đạt; replay 4 fixture cùng seed giống byte và kho được tiến trình quán đọc đúng. Chưa xác nhận toàn bộ DoD nhóm hoặc các phase sau.

## Phase 2 — phần Minh

- Đã làm trong commit `84b1f1d`: dữ liệu contract v1.1 (6 nguyên liệu/6 món, 2 bếp/4 bàn, D1–D5, Shop), input buy/cạnh nút mới, cá bơi/phản xạ/đổi hướng/sinh, Cá Sấu patrol/chase/recoil, hit/ngất LIFO, API day/active_upgrades và 30 test mới.
- Validator `chonoi/contract.py` phải đổi để đọc manifest v1.1; lý do và ba điều chỉnh regression theo Ticket đã ghi trong `docs/contracts/phase-2.md`.
- Nhật ký AI: Codex thực hiện theo yêu cầu “làm phần Minh trong docs/plan/phase-2.md”; model/token/chi phí không được công cụ báo. Vòng test đầu phát hiện fixture P1 ca_loc ở d=5 không còn đứng yên khi mặc định bật cá bơi; đã đặt random_fish:false đúng contract, không nới assertion cooldown.
- Review: Codex tự rà theo Ticket 1.1/1.2/4; chưa ghi nhận người thật đã review. Phản tư cá nhân này cần Minh xác nhận.
- Bằng chứng module riêng: `docs/members/minhh25-phase-2/` (để Hùng tổng hợp; không sửa vùng docs/proof/phase-2 độc quyền QA). Chưa xác nhận DoD toàn nhóm, day/Shop/pause/UI, tag hay deadline.
- Kết quả thực chạy: 88/88 test toàn repo, 30/30 test Phase 2 của Minh; 4 replay P1 và smoke hai nguyên liệu mới đạt. Gather đủ 10.800 tick chạy 0,5051 s (không phải benchmark cả Ngày). Nhật ký chi tiết trong thư mục bằng chứng cá nhân.
