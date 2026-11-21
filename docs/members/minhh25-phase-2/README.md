# Kiểm chứng module Phase 2 — Minh

Ngày ghi: 2026-11-21. Nguồn: `docs/requirements/phase-2.txt`; phân công: `docs/plan/phase-2.md`. Log lưu trong thư mục cá nhân để không sửa vùng bằng chứng độc quyền QA. Hùng có thể dùng các log này để tổng hợp kiểm chứng toàn nhóm.

Commit code/test: `84b1f1d` trên nhánh `nguyendinhminh`. Tài liệu/log được bàn giao trong commit kế tiếp. Chưa đẩy thẳng main hoặc gắn tag; phần dùng chung cần được gộp sớm qua PR để đồng đội dùng.

| Kiểm tra đã chạy | Kết quả | Bằng chứng |
|---|---|---|
| Toàn bộ `unittest discover -s tests -v`, PYTHONPATH=tests:. | **88/88 đạt**, gồm test HTTP live | [test-suite.txt](test-suite.txt) |
| `test_gather_p2.py` | **30/30 đạt** | [gather-p2-tests.txt](gather-p2-tests.txt) |
| Replay hai lần của 4 fixture P1 + chuyển kho cho tiến trình quan | **4/4 đạt**, byte JSONL/kho giống nhau | [replay-p1.txt](replay-p1.txt) |
| Hái kèo nèo/bắt cá kèo mặc định qua CLI rồi cho tiến trình quan đọc kho | **Đạt**, stock đúng yield từng loại | [integration-p2.txt](integration-p2.txt) |
| Một ca gather đủ 10.800 tick, seed 42 | **0,5051 s** trên máy chạy; kết thúc time, 12 đàn, 4 fish_spawned | [gather-full-run.txt](gather-full-run.txt) |

Số đo cuối chỉ là gather, **chưa phải** benchmark toàn Ngày 22.200 tick của DoD. Log HTTP được chạy ngoài hạn chế sandbox bind localhost. Không skip test.

## Truy vết phần Minh

| Yêu cầu Ticket | Kiểm chứng |
|---|---|
| 1.1 / 4.1: số chuẩn, 6 loại, 6 món, B1–B2, T1–T4, D1–D5 | P2ManifestAndInputs.test_manifest_values_and_all_five_plan_totals |
| 1.1: 8 đàn ở 8 vị trí khác nhau; 36 cặp/30 vị trí | P2Fish.test_initial_eight_unique_geometric_points_seeded |
| 1.1: bơi đúng loài, phản xạ quãng dư/cả hai trục, đổi hướng trước bước 120 | Các test reflection/turns/swimming trong P2Fish |
| 1.1 / 4.3 / 4.5: catch trước bơi, fixture đứng yên, lịch sinh/cap/clearance/id | Các test catch/random_false/spawn/no_spawn trong P2Fish |
| 1.2: M2 từ Ngày 3; patrol/chase/thoát; chọn hit gần/id; LIFO; bất tử | Các test layout/patrol/detection/hit/invulnerability trong P2Monsters |
| 1.2 / 4.5: recoil đủ 60 bước từ bước sau, không hit ở bước kết thúc; chặn mép; ngạt trước hit | Các test recoil/choke trong P2Monsters |
| 1.2 / 4.4: monster_hit → faint phần còn lại → gather_end kho rỗng | P2Monsters.test_lethal_hit_drops_half_then_faints_remaining_lifo |
| 2: nhận cấp active riêng, maxima và reset đầu ngày | P2UpgradesAndHeadless.test_active_upgrades_effective_maxima_and_new_day_reset |
| 4.2: cạnh nút và buy không kế thừa | P2ManifestAndInputs.test_input_buy_is_one_frame_and_edges_survive_phase_boundaries |
| 4.4: output tất định khi cá bơi/sinh + quái | P2UpgradesAndHeadless.test_headless_default_seeded_replay_includes_swimming_spawn_and_monsters |

## Bàn giao / giới hạn

- API cụ thể: [docs/contracts/phase-2.md](../../contracts/phase-2.md).
- Chưa sửa file độc quyền của Hải, Hùng, Bảo. CLI fixture mới (monsters/age_ticks/loài mới) cần parser QA; vòng day, pause/Shop, HUD cần chủ module tích hợp.
- Chưa đo toàn Ngày, chưa chạy day --days 1/5, chưa kiểm đầy đủ UI hoặc gắn tag. Kết quả test xanh chỉ áp lên bộ test hiện có.
- Đã giữ nguyên assertion luật cốt lõi P1; ba chỉnh sửa test do đổi contract có lý do trong tài liệu bàn giao, không sửa test để che luật sai.
- Tự rà code bởi Codex; chưa có bằng chứng review của con người. Nhật ký AI ở phần Phase 2 trong `docs/members/minhh25.md` để QA tổng hợp.
