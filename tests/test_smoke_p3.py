"""Smoke Phase 3 (QA, hộp đen): kho cá thể {id, kind, fresh} và độ tươi — Test Contract v1.2 (docs/plan/phase-3.md).

Chỉ chạy khi `game.contract.json` có khối `freshness` (v1.2); trước đó tự bỏ qua với lý do rõ ràng.
Chỉ khẳng định những điều plan nêu thẳng (ngưỡng `fresh < 30` là ươn, `spoiled` phát ở tick 1 khi đi từ >=30
xuống <30, schema file kho, mã thoát 2). Các điều còn mơ hồ (base_price, giữ lại khi ươn) KHÔNG đoán ở đây —
xem docs/verification/phase-3.md.

Chạy: python -m unittest discover -s tests -p test_smoke_p3.py -v
"""

import json
import os
import unittest

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


def contract():
    with open("game.contract.json", encoding="utf-8") as f:
        return json.load(f)


HAS_V12 = "freshness" in contract()["tuning"]
SKIP = unittest.skipUnless(HAS_V12, "game.contract.json chưa có `freshness` (chưa lên v1.2) — chờ Integrator")


def it(i, kind="ca_loc", fresh=100):
    return {"id": i, "kind": kind, "fresh": fresh}


@SKIP
class Spoilage(unittest.TestCase):
    def test_nguong_30_phat_spoiled_o_tick_1(self):
        """Giỏ có hàng fresh = 30 đúng ngưỡng: hao đầu bước -> < 30 -> `spoiled` (location hold) ở tick 1."""
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {"hold": [it("I1", fresh=30), it("I2", "bong_sung", 100)],
                                                           "random_fish": False, "player": {"pos": [50, 10]}}})
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "3", "--scenario", sc,
                                     "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            sp = events(read_jsonl(w.path("o.jsonl")), "spoiled")
            self.assertEqual(len(sp), 1, sp)
            self.assertEqual(sp[0]["tick"], 1)
            self.assertEqual(sp[0]["data"]["location"], "hold")
            self.assertIn("I1", json.dumps(sp[0]["data"]))
            self.assertNotIn("I2", json.dumps(sp[0]["data"]))

    def test_hang_tuoi_khong_phat_spoiled(self):
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {"hold": [it("I1", fresh=100)], "random_fish": False,
                                                           "player": {"pos": [50, 10]}}})
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "60", "--scenario", sc,
                                     "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            self.assertEqual(events(read_jsonl(w.path("o.jsonl")), "spoiled"), [])

    def test_ban_giao_cung_tick_khong_hao_them(self):
        """Cập bến tick 0: kho ghi ra và quán đọc lại cùng id/kind; quán tick 0 chưa hao thêm so với kho."""
        with Workdir() as w:
            hold = [it("I1", "ca_loc", 80), it("I2", "bong_sung", 64.5)]
            sc = write_json(w.path("sc.json"), {"gather": {"hold": hold}})
            inp = write_json(w.path("in.json"), frames({"tick": 0, "interact": True}))
            inv = w.path("inv.json")
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "1", "--scenario", sc, "--inputs", inp,
                                     "--inventory-out", inv, "--out", w.path("g.jsonl"))
            self.assertEqual(code, 0, err)
            with open(inv, encoding="utf-8") as f:
                saved = json.load(f)
            self.assertEqual(list(saved), ["items"])
            self.assertIsInstance(saved["items"], list)
            self.assertEqual({(x["id"], x["kind"]) for x in saved["items"]}, {("I1", "ca_loc"), ("I2", "bong_sung")})
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "0", "--inventory", inv,
                                     "--out", w.path("q.jsonl"))
            self.assertEqual(code, 0, err)
            stock = snapshots(read_jsonl(w.path("q.jsonl")))[0]["stock"]
            self.assertEqual(sorted((x["id"], x["kind"], x["fresh"]) for x in stock),
                             sorted((x["id"], x["kind"], x["fresh"]) for x in saved["items"]))


@SKIP
class KhoSai(unittest.TestCase):
    def _quan_exit(self, w, obj):
        inv = write_json(w.path("inv.json"), obj)
        return run_headless("--mode", "quan", "--seed", "1", "--ticks", "0", "--inventory", inv, "--out", w.path("q.jsonl"))[0]

    def test_file_kho_sai_exit_2(self):
        with Workdir() as w:
            for bad in ({"items": {"ca_loc": 1}},                               # kho đếm cũ
                        {"items": [it("I1"), it("I1")]},                        # trùng id
                        {"items": [it("I1", fresh=101)]}, {"items": [it("I1", fresh=-1)]},
                        {"items": [{"id": "I1", "kind": "ca_loc"}]},            # thiếu fresh
                        {"items": [it("I1", kind="ca_la_lung")]}):
                self.assertEqual(self._quan_exit(w, bad), 2, bad)
                self.assertFalse(os.path.exists(w.path("q.jsonl")), "lỗi đầu vào phải thoát trước khi ghi đầu ra")

    def test_file_kho_ca_the_hop_le_exit_0(self):
        with Workdir() as w:
            self.assertEqual(self._quan_exit(w, {"items": [it("I1"), it("I2", "ca_keo", 0)]}), 0)
            self.assertEqual(self._quan_exit(w, {"items": []}), 0)

    def test_scenario_kho_dem_cu_exit_2(self):
        with Workdir() as w:
            for mode, block in (("gather", {"hold": ["ca_loc"]}), ("quan", {"stock": {"ca_loc": 1}})):
                sc = write_json(w.path("sc.json"), {mode: block})
                self.assertEqual(run_headless("--mode", mode, "--seed", "1", "--ticks", "0", "--scenario", sc,
                                              "--out", w.path("o.jsonl"))[0], 2, block)


class ChoSimV12(unittest.TestCase):
    """Chưa viết được chính xác khi plan chưa nêu đủ chi tiết; ghi lại để không quên."""

    @unittest.skip("Chờ sim/quan v1.2 + công thức làm tròn: base_price = floor(giá × avg_fresh / 100), boa floor(base_price × 0.2)")
    def test_base_price_theo_do_tuoi(self):
        pass

    @unittest.skip("Chờ sim/quan v1.2: nhả & thử giữ lại đúng 1 lần khi cá thể giữ bị ươn; thiếu thì unfulfillable")
    def test_giu_lai_khi_hang_giu_bi_uon(self):
        pass


if __name__ == "__main__":
    unittest.main()
