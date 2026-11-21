# Bằng chứng Phase 1 — Minh (minhh25)

Phạm vi: lát 1–2 gather và phần chuẩn bị tích hợp. Nguồn yêu cầu là [PRD-0/Test Contract v1.0 người dùng cung cấp](../../../requirements/phase-1.txt), đối chiếu đặc biệt mục E–G. Ngày ghi: 2026-11-21. Nhánh: `codex/minh-gather-phase1`.

## Kết quả thực thi

| Lệnh từ gốc repo | Kết quả | Log |
|---|---|---|
| `python3 tools/check_gather.py` | 23 test đạt | [gather-tests.txt](gather-tests.txt) |
| `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v` | 55 test đạt, gồm HTTP live | [test-suite.txt](test-suite.txt) |
| `python3 tools/check_gather_replay.py` | 4/4 fixture đạt; JSONL/kho giống byte ở 2 lần chạy cùng seed 42; quan đọc đúng kho | [replay.txt](replay.txt) |
| `python3 tools/check_team.py` | Chưa đạt: thiếu handle của Hải, Bảo, Hùng | [team-check.txt](team-check.txt) |

Lần chạy test gốc ban đầu trong sandbox: 31/32 đạt, `test_live` bị `PermissionError` khi bind localhost. Không sửa/skip test; chạy lại ngoài giới hạn sandbox đạt toàn bộ. Không dùng kết quả này để xác nhận luật quán hoàn tất: smoke chỉ kiểm khung, `chonoi/sim/quan.py` còn TODO.

Fixture replay ở `tests/fixtures/gather-replay.json`: hái tại mép bán kính ở bước cuối, bắt cá ở bước cuối, ngất bỏ giỏ và mẫu cập bến của PRD. Script chạy mỗi fixture qua hai tiến trình gather, so trực tiếp byte trước tính SHA-256, kiểm `gather_end.inventory`, rồi cho một tiến trình quan đọc file tại tick 0. Hash và sự kiện thật nằm trong log.

## Bàn giao và việc còn lại

- Mã/test: `chonoi/sim/gather.py`, `tests/test_gather.py`; không đổi preset, schema kho hoặc khung runner/live/scenario.
- Tài liệu tích hợp: `docs/contracts/README.md` ghi lại đúng PRD; chưa có bằng chứng thành viên khác đã duyệt.
- Xem commit bằng `git log --oneline --author='Nguyen Dinh Minh' codex/minh-gather-phase1`; các commit chứa kết quả kiểm tra trong mô tả. Không coi ghi chép do Codex tạo là review của con người.
- Commit luật + test + handle: `2760cdc`; commit hai command + fixture + AGENTS: `c3fa73b`. Tài liệu và log được ghi trong commit bàn giao tiếp theo.
- Cần Hải đọc chéo gather; QA/UI tích hợp trên main, bổ sung ba handle còn thiếu, kiểm chứng luật quán và chơi thử đầy đủ trước tag `phase-1`.
- Chưa tạo/push tag, chưa push nhánh, chưa xác nhận mốc giờ nộp/collaborator. Chưa có Ticket-02/03/04 trong nguồn được cung cấp.
