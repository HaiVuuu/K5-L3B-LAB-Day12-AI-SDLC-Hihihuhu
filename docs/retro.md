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
- Rà lại hành động Phase 2: Đã thực hiện phần lớn — Integrator khóa contract trước và tách file test/proof theo từng người giúp Phase 3–4 giảm xung đột; các test cũ P1–P2 chưa cập nhật schema kho cá thể v1.2/v1.3 là điểm còn sót lại cần ghi chú rõ trong ma trận truy vết.
- Điều tốt / điều tệ:
  - Tốt: 4 thành viên phối hợp đầy đủ trên cùng repo, có đủ `soak`, `bench`, cảnh báo tương phản cao, kiểm tra đóng gói `tools/check_release.py` và phản tư cá nhân đủ 4/4 người.
  - Tệ: Lịch chạy dồn nên `docs/verification/phase-2.md` bị bỏ qua và việc gắn tag đúng mốc từng phase chưa được đẩy đồng bộ lên GitHub.
- Số liệu: Số commit trên `main` (`git shortlog -sn HEAD`): `hungvueducation-hash` (20+1), `Nguyen Dinh Minh` (17), `HaiVuuu` / `Nguyen Dinh Vu Hai` (10+8), `Jay Baro` / `Doan Xuan Duy Bao` (12+1); đọc code chéo qua PR và kiểm tra offline trước khi merge; token không đo được do dùng nhiều công cụ AI khác nhau.
- Một lần AI sai và cách nhóm phát hiện: AI tạo test trong `test_quan.py` thiếu tham số `edges` của `InputState`, dùng nhầm import tương đối trong `day.py`, và viết fixture `"hold": ["ca_loc"]` ở `test_quan_p3.py` cho schema v1.2/v1.3 — phát hiện ngay khi chạy `unittest`.
- Nếu làm lại, đổi gì: Đẩy tag `phase-n` và điền `docs/verification/phase-n.md` ngay tại thời điểm kết thúc mỗi phase; cập nhật ngay fixture test cũ mỗi khi có breaking change schema.

## Phase 3 — ghi chú từ phần QA (bản nháp do Claude Code ghi, Hùng cần xác nhận)
- Làm được: kiểm scenario cho 6 nguyên liệu, `monsters`, và kho cá thể v1.2 (13 test); dựng smoke v1.2 tự kích hoạt khi contract có `freshness`.
- Vướng: contract 1.2 và sim độ tươi chưa vào `main` nên smoke v1.2 chưa chạy được thật; không đoán các chi tiết plan chưa nêu (`base_price`, giữ lại khi ươn).
- Hành động đề xuất: khi v1.2 vào `main`, chạy smoke P3 + regression P1–P2, ghi lý do từng test cũ phải đổi.
