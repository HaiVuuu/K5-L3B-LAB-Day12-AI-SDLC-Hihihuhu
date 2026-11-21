# Title

feat(gather): cá bơi, Cá Sấu và hợp đồng v1.1 cho Phase 2

# Description

## Phạm vi
Phase 2 · Minh (sim/gather + Integrator), theo TICKET-02 mục 1.1, 1.2 và 4.

- Chuẩn hóa manifest v1.1: sáu nguyên liệu/sáu món, hai bếp/bốn bàn, kế hoạch D1–D5 và dữ liệu nâng cấp Shop.
- Cá bơi/phản xạ, đổi hướng theo seed mỗi 120 bước, sinh mỗi 360 tick với trần 12 và khoảng cách sinh >1 m.
- Cá Sấu patrol/chase/recoil, M2 từ Ngày 3, một hit/bước, mất nửa giỏ LIFO, bất tử 90 tick và ngất đúng thứ tự.
- Gather nhận day/active_upgrades; input có nút mới và buy không kế thừa qua frame; kho hỗ trợ hai loại mới.

## Kiểm chứng
- Toàn bộ test: **88/88 đạt**, gồm HTTP live.
- Test mới phần Minh: **30/30 đạt**.
- Bốn replay P1 giống byte; cá kèo/kèo nèo bàn giao đúng qua hai tiến trình gather → quan.
- Gather đủ 10.800 tick: **0,5051 s** trên máy chạy. Chưa phải benchmark cả Ngày.
- Bằng chứng: `docs/members/minhh25-phase-2/`; API: `docs/contracts/phase-2.md`.

## Điều chỉnh test cũ theo yêu cầu mới
Đọc fish_initial từ dữ liệu thay số 6; test từ chối attack v1.0 dùng BUTTONS_V10; fixture P1 dùng random_fish:false/monsters:[] để giữ phạm vi kiểm luật cũ. Lý do chi tiết có trong hợp đồng bàn giao và commit code.

## AI và phần cần tích hợp
Codex triển khai, kiểm thử và tự rà theo Ticket; chưa ghi nhận review của người thật. Nhật ký riêng ở docs/members/minhh25.md để QA tổng hợp.

Hải cần nối day/Shop/pause và truyền active_upgrades; Hùng nâng scenario parser/smoke; Bảo nối UI/HUD (endpoint live hiện chỉ chuyển nút cũ). Không sửa các file độc quyền của đồng đội, không khai DoD Phase 2 đã hoàn tất hay gắn tag.

## Checklist review
- [ ] Đúng thứ tự tick, payload và số chuẩn của Ticket-02.
- [ ] Rà thay đổi contract.py/input/inventory và lý do cập nhật regression.
- [ ] CI xanh; các chủ module đọc tài liệu API và tích hợp.
- [ ] Sau tích hợp chạy day --days 1/5, pause/Shop/UI và kiểm chứng trên main trước tag.
