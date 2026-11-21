# Ma trận truy vết Phase 1

| AC | Cách kiểm chứng | Bằng chứng (link `docs/proof/phase-1/...`) | Kết quả (đạt / chưa đạt — ghi trung thực) |
|---|---|---|---|
| PRD-0 F Gather: bơi, biên, tốc độ, hướng | Smoke `Movement` + test chuyển mặt nước | [test-suite.txt](../proof/phase-1/minh/test-suite.txt) | Đạt trong test tự động |
| PRD-0 E/F: oxy, ngạt đúng t+59, nổi lên tránh ngạt, faint mất giỏ LIFO | `GatherRules`: test oxy, ngạt, surface, faint; kiểm payload và thứ tự event | [gather-tests.txt](../proof/phase-1/minh/gather-tests.txt) | Đạt |
| PRD-0 E/F: hái/mọc lại, đúng mép, hòa theo id, giữ nguyên khi đầy | `GatherRules`: node, regrowth, full_hold | [gather-tests.txt](../proof/phase-1/minh/gather-tests.txt) | Đạt |
| PRD-0 E/F: bắt nguyên đàn, không thử đàn khác, cooldown/cạnh lên | `GatherRules`: fish, partial_capacity, miss, cooldown, buttons | [gather-tests.txt](../proof/phase-1/minh/gather-tests.txt) | Đạt |
| PRD-0 F/G: bến ưu tiên, hành động ở bước cuối, ngất kho rỗng, tick_limit giữ file | Unit + `GatherHeadless` | [gather-tests.txt](../proof/phase-1/minh/gather-tests.txt) | Đạt |
| PRD-0 E/G: tất định và smoke kho hai tiến trình | 4 fixture, chạy hai lần so byte và nạp kho vào quan tick 0 | [replay.txt](../proof/phase-1/minh/replay.txt) | Đạt |
| PRD-0 mục 7: danh sách thành viên | `tools/check_team.py` | [team-check.txt](../proof/phase-1/minh/team-check.txt) | Chưa đạt: 3 handle thiếu |
| PRD-0 mục 7: luật quán, HUD đầy đủ, chơi thử/review trên main, tag đúng hạn | Cần Hải/Bảo/Hùng tiếp tục; chưa có bằng chứng này | [ghi chú bàn giao](../proof/phase-1/minh/README.md) | Chưa xác nhận; chưa đủ DoD toàn nhóm |

## Đánh giá ngắn
- Đây là phần kiểm chứng Minh bổ sung, không thay xác nhận phát hành của QA lead. Nguồn PRD được cung cấp không có mã AC riêng; truy vết bằng mục yêu cầu thật, không tự đặt mã của giảng viên.
- Gather đạt 23 test riêng và hồi quy trong bộ 55 test. Test xanh không chứng minh luật quán, review của nhóm hay tag đúng hạn.
- Trước phase sau: tích hợp/review trên main, điền handle còn thiếu, nhận Ticket tương ứng rồi lập kế hoạch; giữ replay và regression gather.
