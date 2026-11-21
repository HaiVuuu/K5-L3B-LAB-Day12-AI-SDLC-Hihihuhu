# Retro nhóm

## Phase 1 — ghi chú từ phần Minh (chưa phải tổng kết cả nhóm)
- Đã có bằng chứng cho gather: 23 test mới, bộ hồi quy 55 test đạt, 4 replay kho hai tiến trình giống byte.
- Vướng: PRD ban đầu chỉ có link cần đăng nhập; sau khi người dùng gửi văn bản mới đối chiếu được payload amount/yield và faint.lost. Ba handle còn thiếu, quán còn TODO nên chưa xác nhận DoD/tag.
- Hành động đề xuất: giữ PRD đã nhận trong `docs/requirements/`, Hải đọc chéo gather và QA kiểm luật quán thực tế trước khi tag. Chưa có bằng chứng hành động review này đã diễn ra.

## Phase 2 (nhanh) — ghi chú từ phần QA (Hùng; bản nháp do Claude Code ghi, Hùng cần xác nhận)
- Điều tốt: hai buổi nối được qua file kho; `main` luôn qua bộ test sau mỗi lần gộp.
- Điều tệ: Phase 2 hợp đồng v1.1 vào `main` trễ nên QA không chạy được smoke `--mode day` đúng lịch; `scenario.py` bị bỏ sót (còn cứng 4 loại nguyên liệu, từ chối `monsters`) cho tới Phase 3; test `expectedFailure` của QA từng sai vì chính test (đặt `regrow_ticks` làm nút chưa mọc), không phải sim.
- 1 hành động cho Phase 3: Integrator đẩy contract trước khi chia nhánh; QA viết test theo spec rồi chạy trên sim thật trước khi tin kết quả.

## Phase 4 (cuối)
- Rà lại hành động Phase 2 (phần QA; bản nháp do Claude Code ghi, Hùng cần xác nhận): hành động là "Integrator đẩy contract trước khi chia nhánh; QA viết test theo spec rồi chạy trên sim thật trước khi tin kết quả". Nửa sau **đã làm**: smoke P3 chạy thử trên gather v1.2 và quan v1.2 thật, tìm ra 3 vấn đề thật. Nửa đầu **chưa làm được**: contract v1.2/1.3 vẫn chưa vào `main` ở thời điểm Phase 4, nên `main` từng đỏ (12:22) vì gather (v1.1) và quan (v1.2) lệch phiên bản; Hải sửa bằng tương thích v1.1/v1.2 ở PR #13 (12:46) và `main` xanh trở lại.
- Điều tốt: test viết theo spec và kiểm trên bản thật bắt được lỗi sớm; mỗi người sở hữu file riêng nên ít xung đột merge; PR có mô tả "đã kiểm / chưa kiểm".
- Điều tệ: bàn giao contract chậm làm đội chuyển phiên bản không đồng bộ; `TEAM.md` bị mất handle của Minh sau một lần merge mà không ai phát hiện tới Phase 4; Ticket phase sau không nằm trong repo chung nên QA phải suy từ plan; bench chưa có; soak chạy được nhưng bot chưa bán hàng nên chưa thực thi luật quán.
- Số liệu: số commit theo người đọc từ `git shortlog -sn origin/main` (chưa tổng hợp trong bản nháp này); cách đọc code của nhau: chưa có bằng chứng review chéo bởi người thật; token theo người: công cụ không báo, không ước đoán.
- Một lần AI sai và cách nhóm phát hiện: test hái nút đặt `regrow_ticks: 600` nên nút chưa mọc (lỗi ở test, phát hiện bằng chạy tay headless); smoke P3 ban đầu so `fresh` chính xác trong khi JSONL làm tròn 3 chữ số (phát hiện khi chạy trên bản thật, Ticket-03 cho dung sai ±0.01); nhận biết v1.2 bằng "có `freshness`" sai vì manifest chuyển tiếp có freshness mà vẫn 1.1.
- Nếu làm lại, đổi gì: chốt và đẩy contract + ADR chuyển phiên bản lên `main` trước khi chia nhánh; có một lệnh `check_team` trong CI; đưa Ticket từng phase vào `docs/requirements/` ngay khi phát.

## Phase 3 — ghi chú từ phần QA (bản nháp do Claude Code ghi, Hùng cần xác nhận)
- Làm được: kiểm scenario cho 6 nguyên liệu, `monsters`, và kho cá thể v1.2 (13 test); dựng smoke v1.2 tự kích hoạt khi contract có `freshness`.
- Vướng: contract 1.2 và sim độ tươi chưa vào `main` nên smoke v1.2 chưa chạy được thật; không đoán các chi tiết plan chưa nêu (`base_price`, giữ lại khi ươn).
- Hành động đề xuất: khi v1.2 vào `main`, chạy smoke P3 + regression P1–P2, ghi lý do từng test cũ phải đổi.
