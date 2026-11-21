# TEAM

**Tên nhóm:** Hihihuhu  **Số người:** 4  (khớp `team_size` trong `game.contract.json`)

| Thành viên | GitHub handle | Module chính | Vai quy trình | Người dự phòng cho |
|---|---|---|---|---|
| Nguyễn Đình Minh | | `sim/gather` | Integrator | `sim/quan` |
| Nguyễn Đình Vũ Hải | | `sim/quan` | Scrum / Release | `sim/gather` |
| Đoàn Xuân Duy Bảo | | `client/ui` | PO | `qa` |
| Vũ Tiến Hùng | | `qa` | QA lead | `client/ui` |

**Vai quy trình:** PO (đầu mối hỏi giảng viên, giữ `docs/clarify.md`) · Integrator (giữ `docs/contracts/`, gắn tag) · QA lead · Scrum/Release. Có thể kiêm.

## Thỏa thuận làm việc nhóm (điền trong 15 phút kickoff, ≤ 10 dòng)

- Kênh liên lạc: Nhóm chat chung của 4 người
- Khi bất đồng về thiết kế: Thảo luận 2 phút, chưa chốt được thì Integrator quyết và ghi lý do
- Khi ai đó trễ hoặc vướng quá 10 phút: Báo ngay trên kênh chung để người dự phòng hỗ trợ hoặc nhận lát việc
- Giờ standup giữa phase: Cuối mỗi phase (trước khi gắn tag 10 phút), cập nhật `docs/standup.md`
- Cách đọc code của nhau (tùy chọn): Đọc chéo theo cặp dự phòng (`sim/gather` ↔ `sim/quan`, `client/ui` ↔ `qa`) trước khi gộp vào `main`
- Cách làm việc với Git: Làm trên nhánh ngắn (`feat/<module>-...`), tách file test riêng (`test_gather.py`, `test_quan.py`, `test_integration.py`), rebase `main` và chạy test xanh trước khi gộp; Integrator gắn tag `phase-1`..`phase-4`
