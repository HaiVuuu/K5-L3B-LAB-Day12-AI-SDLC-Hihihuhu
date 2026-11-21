# AGENTS.md — hướng dẫn chung cho mọi agent AI của nhóm

> Cập nhật file này qua các phase (lịch sử git phải cho thấy điều đó). Ngắn gọn, có lệnh chạy thật.

## Lệnh
- Test: `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v`
- Headless: `python3 -m chonoi.headless --mode gather|quan --seed 1 --ticks 600 --out out.jsonl`
- Chơi thử trên trình duyệt: `python3 -m chonoi.live --mode gather|quan` (mở địa chỉ in ra; WASD, E, Space, R)

## Cấu trúc & quy ước
- (Starter Python là TÙY CHỌN; nhóm có thể dùng ngôn ngữ khác nếu giữ Test Contract.) Khung do giảng viên cấp: `chonoi/{headless,inputs,scenario,contract,rng,ids,jsonl,inventory,runner,live}.py` và `chonoi/web/`. Hạn chế sửa; nếu phải sửa thì báo cả nhóm và ghi lại lý do.
- Luật chơi của nhóm: `chonoi/sim/gather.py`, `chonoi/sim/quan.py` (tìm `TODO(nhóm)`).
- **Số liệu chỉ đọc từ `game.contract.json` / dữ liệu**, không hard-code trong luật.
- Mọi số ngẫu nhiên đi qua `Streams` (`chonoi/rng.py`); không dùng `random` toàn cục, không dùng đồng hồ hệ thống.
- Sắp danh sách thực thể bằng `ids.sort_by_id`; cấp id bằng `IdAllocator`.

## Nên tránh
- Không sửa `docs/contracts/`, `game.contract.json` (khóa contract) hoặc schema kho khi chưa báo cả nhóm (đổi hợp đồng ảnh hưởng mọi module).
- Không làm hỏng nhánh chính: trước khi đẩy, chạy test.
- Không bịa yêu cầu: chỗ mơ hồ thì ghi `docs/clarify.md` và hỏi PO.
- Không sửa test cho xanh khi luật sai; phải sửa luật hoặc ghi lý do đổi test trong commit.

## Quy tắc làm việc với agent
- Mỗi agent một việc rõ ràng (một lát). Cho agent đọc PRD/ticket đúng phase và hợp đồng kho trước.
- Agent làm xong phải chạy test và ghi kết quả vào mô tả commit hoặc `docs/proof/`; người đọc lại thay đổi trước khi đẩy.
- Sáng tạo thêm được khuyến khích nhưng phải tắt ở headless (xem README, mục "Tự do sáng tạo").

## Skills / hooks của nhóm
- `python3 tools/check_gather.py`: command nhóm, chạy 23 test luật gather trước khi bàn giao lát 1–2.
- `python3 tools/check_gather_replay.py`: command nhóm, chạy trước tích hợp/tag; so byte JSONL + kho ở hai lượt cùng seed, kiểm quán đọc kho cho 4 fixture trong `tests/fixtures/gather-replay.json`.
- Phase 1: đối chiếu sự kiện với PRD-0 E–G và `docs/contracts/README.md`; không coi smoke xanh là đã hoàn thiện luật quán. Chỉ tag trên `main` sau kiểm chứng toàn nhóm; không ghi nhận review/commit/bằng chứng chưa xảy ra.
- PRD-0 đầy đủ: `docs/requirements/phase-1.txt`; TICKET-02: `docs/requirements/phase-2.txt`. Đọc đúng phase trước khi sửa luật.
- Phase 2 phần Minh: `PYTHONPATH=tests:. python3 -m unittest discover -s tests -p test_gather_p2.py -v`. API day/active_upgrades và lý do cập nhật regression ở `docs/contracts/phase-2.md`.
- Tuân thủ quyền sở hữu `docs/plan/phase-2.md`: Minh không sửa scenario/runner/day/UI hay báo cáo QA; nhật ký/bằng chứng module đặt ở `docs/members/minhh25-phase-2/` để QA tổng hợp. Không gắn tag phase-2 khi chưa kiểm toàn nhóm trên main.
- Phase 3: đọc `docs/requirements/phase-3.txt`, `docs/plan/phase-3.md` và ADR-0001. Test Minh: `PYTHONPATH=tests:. python3 -m unittest discover -s tests -p test_gather_p3.py -v`.
- Chuyển schema theo `docs/contracts/phase-3.md`: giữ active v1.1 trong lúc quan/scenario chuyển tiếp; ứng viên v1.2 ở `docs/contracts/game.contract.v1.2.json`. Không gắn tag hoặc tuyên bố DoD v1.2 trước kiểm hai đầu bàn giao trên bản tích hợp.
- Phase 4: đọc `docs/requirements/phase-4.txt` và `docs/plan/phase-4.md`. V1.3 dùng nguyên gameplay/schema nội bộ v1.2; không đổi tuning.
- Kiểm release: `python3 tools/check_release.py --measure --out dist/release-status.json`; đóng đúng commit: `python3 tools/package_release.py --ref main --out dist/chonoi-v1.0.0.zip`. Không bịa phép đo hoặc tag bản chưa bàn giao.
