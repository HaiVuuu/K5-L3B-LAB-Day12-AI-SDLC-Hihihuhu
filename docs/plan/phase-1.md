# Kế hoạch Phase 1 (≤ 1 trang)

- Mục tiêu: Hoàn thiện lõi `gather` và `quan` theo PRD-0 + Test Contract v1.0, hiển thị được trên `client/ui`, qua toàn bộ smoke test và integration test, gắn tag `phase-1` đúng hạn.
- Việc / người / phụ thuộc:
  - Nguyễn Đình Minh (`sim/gather` · Integrator): Lát 1–2 trong `chonoi/sim/gather.py` (oxy, ngạt, ngất, giỏ LIFO, hái nút, bắt cá) + `tests/test_gather.py`; chốt `docs/contracts/` và gắn tag.
  - Nguyễn Đình Vũ Hải (`sim/quan` · Scrum/Release): Lát 3–4 trong `chonoi/sim/quan.py` (khách, giữ chỗ, kiên nhẫn, nấu, phục vụ, tiền/boa, uy tín) + `tests/test_quan.py`; cập nhật `docs/standup.md`.
  - Đoàn Xuân Duy Bảo (`client/ui` · PO): Cập nhật `chonoi/web/index.html` đọc snapshot `gather`/`quan` từ `GET /state`, giữ `POST /input` + `POST /restart`; ghi `docs/clarify.md` (phụ thuộc field snapshot từ `sim/*`).
  - Vũ Tiến Hùng (`qa` · QA lead): Viết `tests/test_integration.py` (chuỗi `gather` → `inventory` → `quan`, tất định theo seed), chạy kiểm chứng và ghi `docs/verification/phase-1.md` + `docs/proof/phase-1/` (phụ thuộc `sim/gather` và `sim/quan` hoàn tất lát lõi).
- Rủi ro:
  - Xung đột khi gộp vào `main`: Giảm thiểu bằng phân quyền sở hữu file rạch ròi, không sửa chéo file test, không sửa `game.contract.json` khi chưa báo Integrator.
  - Thiếu GitHub handle trong `TEAM.md`: Cần điền đầy đủ trước khi nộp/chạy `tools/check_team.py` (mỗi thành viên ≥ 3 commit bằng tài khoản GitHub của mình).

## Cập nhật phần Minh — 2026-11-21

- [x] Lát 1–2 gather theo PRD-0 E–G; 23 test luật và kiểm headless/kho.
- [x] Ghi hợp đồng tích hợp hiện hành, hai command nhóm, nhật ký AI và bằng chứng tại `docs/proof/phase-1/minh/`.
- [x] Xác minh GitHub `minhh25` khớp tên/email Git đang cấu hình; điền dòng Minh trong TEAM.md.
- [ ] Hải đọc chéo gather; QA/UI xác nhận tích hợp đầy đủ trên main.
- [ ] Hoàn thiện DoD toàn nhóm và gắn/push tag `phase-1` trên main. Không tag bản còn TODO luật quán chỉ vì smoke xanh.
