# Title

chore(release): chuẩn bị contract v1.3 và gói phát hành v1.0.0

# Description

## Phạm vi
Phase 4 · Minh — Release/Integrator.

- Contract v1.3 khai bench_cmd/soak_cmd; giữ gameplay/schema v1.2 bằng metadata tương thích các module.
- README chạy clone sạch trong 3 lệnh, điều khiển và lệnh test/headless/bench/soak.
- LICENSE MIT theo yêu cầu Minh, credits/attribution, TEAM đủ handle và phản tư Minh dưới 200 từ.
- Release notes nháp, công cụ kiểm điều kiện release và đóng ZIP đúng commit + receipt SHA-256.
- Gộp phần soak/sửa tương thích của Hải từ main, giữ file đồng đội.

## Kiểm chứng
- 5/5 test v1.3 và 30/30 test gather P3 đạt; team checker đạt.
- Soak seed 7: hai lượt đủ 10 Ngày, 0 crash, gameplay giống nhau sau bỏ duration_s.
- Clone local sạch mở menu/cập bến → quan; ZIP không có .git chạy headless được. SHA được ghi trong receipt/log.
- **Full regression chưa đạt: 172 test, 19 failure, 16 error, 10 skip**; nhiều fixture kho đếm chưa migrate. Không ghi CI đã xanh.
- Log/báo cáo: docs/members/minhh25-phase-4/.

## Chưa phải bản phát hành cuối
Chờ bench.py/cảnh báo/tương phản cao của Bảo, migration regression và verification P4/retro/changelog của nhóm; phản tư Bảo còn nháp. Chưa có số đo render, chưa tag phase-4/v1.0.0 hoặc công bố Release.

Đây là PR phần chuẩn bị để các module tích hợp, không dùng làm bằng chứng DoD toàn nhóm. Chỉ gắn hai tag cùng SHA main và đính ZIP sau khi các điều kiện đạt.

## AI
Codex hỗ trợ triển khai và kiểm chứng; nhật ký ở docs/ai-usage-log.md. Các lỗi và skip được giữ nguyên trong log, không sửa test cho xanh khi luật chưa đúng.
