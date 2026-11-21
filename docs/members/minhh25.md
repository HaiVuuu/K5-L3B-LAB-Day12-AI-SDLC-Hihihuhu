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

## Phase 3 — phần Minh

- Đã triển khai trong commit `ae469d9`: adapter kho cá thể theo version, hold/ID I và remap mẫu ở Ngày sau, hao tươi chính xác 240 đơn vị/điểm, spoiled theo ID, lost cá thể LIFO và xuất file/JSONL đủ precision.
- Giữ active v1.1 để main còn chạy trong lúc quan/day/scenario chuyển schema; chuẩn bị manifest v1.2 và test trong bản sao tạm. Điều chỉnh thứ tự bật version được giải thích ở ADR-0001 theo quyền chuyển tiếp của Ticket.
- Không sửa module/file độc quyền của Hải/Hùng/Bảo. Hợp đồng API ở `docs/contracts/phase-3.md`; bằng chứng riêng ở `docs/members/minhh25-phase-3/` để QA tổng hợp.
- AI: Codex thực hiện theo yêu cầu triển khai phần Minh sau khi PR Phase 2 đã merge. Không có số đo token/model/chi phí. Một điểm dễ sai được xử lý: làm tròn fresh về 3 chữ số sẽ khiến JSONL/file lệch và có thể đổi tick qua ngưỡng; đã tách precision fresh và thêm test đọc lại.
- Chưa ghi nhận người thật review hoặc DoD toàn nhóm. Minh cần xác nhận phản tư; Hải/Hùng cần nối hai đầu, QA chạy bản v1.2 tích hợp trước khi bật manifest và tag.
- Kết quả thực chạy: 122/122 test toàn repo, 30/30 test nhánh v1.2 phần Minh và 4/4 replay legacy đạt. Log/bằng chứng tick ngưỡng và file/event ở `docs/members/minhh25-phase-3/`.
- Sau khi gộp main de90282 (UI Phase 2): chạy lại 128/128 test đạt, log `merge-main-tests.txt` trong thư mục bằng chứng Phase 3 cá nhân.
