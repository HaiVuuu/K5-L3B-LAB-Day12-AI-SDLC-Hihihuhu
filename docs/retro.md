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
- Rà lại hành động Phase 2: đã làm chưa? vì sao?
- Điều tốt / điều tệ:
- Số liệu: số commit theo người, cách đọc code của nhau, token theo người:
- Một lần AI sai và cách nhóm phát hiện:
- Nếu làm lại, đổi gì:

## Phase 3 — ghi chú từ phần QA (bản nháp do Claude Code ghi, Hùng cần xác nhận)
- Làm được: kiểm scenario cho 6 nguyên liệu, `monsters`, và kho cá thể v1.2 (13 test); dựng smoke v1.2 tự kích hoạt khi contract có `freshness`.
- Vướng: contract 1.2 và sim độ tươi chưa vào `main` nên smoke v1.2 chưa chạy được thật; không đoán các chi tiết plan chưa nêu (`base_price`, giữ lại khi ươn).
- Hành động đề xuất: khi v1.2 vào `main`, chạy smoke P3 + regression P1–P2, ghi lý do từng test cũ phải đổi.
