# Ma trận truy vết Phase 4 — Phát hành `v1.0.0`

| AC | Cách kiểm chứng | Bằng chứng | Kết quả (đạt / chưa đạt) |
|---|---|---|---|
| AC-P4-01: Contract v1.3 (`bench_cmd`, `soak_cmd`, giữ v1.2) | `tests/test_release_p4.py`, `tools/check_release.py` | [minhh25-phase-4/README.md](../members/minhh25-phase-4/README.md) | Đạt |
| AC-P4-02: Benchmark render 1280×720 (`--seed 42 --duration 30`) | `python -m chonoi.bench --seed 42 --duration 30 --out bench.json`, `tests/test_bench_p4.py` | [CapybaraSlayer96-phase-4/bench.json](../members/CapybaraSlayer96-phase-4/bench.json) | Đạt |
| AC-P4-03: 3 cảnh báo rõ ràng & chế độ tương phản cao | Chơi thử trực tiếp cả 3 cảnh báo ở chế độ thường & tương phản cao | [CapybaraSlayer96-phase-4/README.md](../members/CapybaraSlayer96-phase-4/README.md) | Đạt |
| AC-P4-04: Soak headless 10 ngày (`--seed 7 --days 10`, lặp `D1–D5`) | `python -m chonoi.soak --seed 7 --days 10 --out soak.json`, `tests/test_soak_p4.py` | [soak-1.json](../members/minhh25-phase-4/soak-1.json), [soak-2.json](../members/minhh25-phase-4/soak-2.json) | Đạt (`days_completed=10`, `crashes=0`) |
| AC-P4-05: Clone sạch chạy ≤ 3 lệnh, đóng gói & `README.md`/`LICENSE`/`CREDITS.md` | `tools/package_release.py`, `docs/releases/v1.0.0.md` | [clean-clone-and-package.json](../members/minhh25-phase-4/clean-clone-and-package.json) | Đạt |
| AC-P4-06: Đội ngũ (`TEAM.md`), phản tư cá nhân (`docs/members/*.md`), retro & skills | `python tools/check_team.py`, `.agents/skills/*`, `docs/retro.md` | [team.txt](../members/minhh25-phase-4/release-check-logs/team.txt) | Đạt (`4/4` thành viên) |
| AC-P4-07: Gắn tag `phase-1`..`phase-4` & Release `v1.0.0` | `git tag -l` và GitHub Release `v1.0.0` | (Cần Integrator đẩy tag & publish Release từ `main`) | Chờ đẩy tag & Release |

## Đánh giá ngắn
- Các module lõi (`gather`, `quan`, `day`, `soak`, `bench`, `web/index.html`) và tài liệu thành viên/release đã đầy đủ trên `main`.
- Lưu ý test cũ P1–P2 dùng schema kho đếm v1.0/v1.1 nên bị từ chối khi `game.contract.json` đã nâng lên schema cá thể v1.3 (đúng theo luật đổi kho từ Phase 3); các bộ test v1.2/v1.3 (`test_gather_p3.py`, `test_quan_p3.py`, `test_soak_p4.py`, `test_bench_p4.py`, `test_release_p4.py`) là bộ kiểm chứng chính cho bản phát hành.
