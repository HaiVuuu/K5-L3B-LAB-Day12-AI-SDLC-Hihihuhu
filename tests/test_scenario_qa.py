"""QA — kiểm scenario (Contract D) theo contract v1.1 (6 nguyên liệu, monsters) và v1.2 (kho cá thể, độ tươi).

Kiểm trực tiếp `load_scenario` (nhanh) + vài ca chạy headless thật. Ca v1.2 chèn `freshness` vào tuning vì
`game.contract.json` hiện tại có thể chưa lên 1.2 — khi lên 1.2 thật, các ca này vẫn đúng. Nhận biết v1.2 bằng
`_contract_version`, không bằng sự có mặt của `freshness` (manifest chuyển tiếp có freshness nhưng vẫn là 1.1).
"""

import copy
import json
import os
import tempfile
import unittest

from chonoi.contract import load_contract
from chonoi.errors import BadInput
from chonoi.scenario import ingredient_kinds, load_scenario

from helpers import Workdir, events, frames, read_jsonl, run_headless, write_json


def tuning(v12=False):
    t = copy.deepcopy(load_contract()["tuning"])
    if not v12:  # ép về v1.1 để ca "bộ đếm cũ" đúng cả khi manifest đang chạy là 1.2 (có freshness + _contract_version 1.2)
        t.pop("freshness", None)
        t["_contract_version"] = "1.1"
    if v12:
        t["freshness"] = {"initial": 100, "gather_decay_per_s": 0.5, "quan_decay_per_s": 0.25, "spoiled_below": 30}
        t["_contract_version"] = "1.2"  # load_contract gắn khi manifest là 1.2
    return t


def load(mode, block, t):
    fd, path = tempfile.mkstemp(suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump({mode: block}, f)
        return load_scenario(path, mode, t)
    finally:
        os.unlink(path)


def it(i, kind="ca_loc", fresh=100):
    return {"id": i, "kind": kind, "fresh": fresh}


class Kinds(unittest.TestCase):
    def test_sau_nguyen_lieu_tu_contract(self):
        kinds = ingredient_kinds(tuning())
        for k in ("ca_loc", "ca_linh", "ca_keo", "bong_sung", "bong_dien_dien", "keo_neo"):
            self.assertIn(k, kinds)

    def test_nut_keo_neo_va_ca_keo_duoc_chap_nhan(self):
        t = tuning()
        load("gather", {"nodes": [{"id": "N5", "kind": "keo_neo", "pos": [76, 0]}],
                        "fish": [{"id": "F1", "kind": "ca_keo", "pos": [30, 24]}], "hold": ["ca_keo", "keo_neo"]}, t)
        load("quan", {"stock": {"ca_keo": 2, "keo_neo": 1}}, t)

    def test_loai_la_van_bi_tu_choi(self):
        t = tuning()
        for mode, block in (("gather", {"hold": ["ca_la_lung"]}), ("quan", {"stock": {"ca_la_lung": 1}}),
                            ("gather", {"nodes": [{"id": "N1", "kind": "ca_loc", "pos": [5, 0]}]})):
            with self.assertRaises(BadInput, msg=block):
                load(mode, block, t)


class Monsters(unittest.TestCase):
    GOOD = {"id": "M1", "kind": "ca_sau", "pos": [60, 24], "waypoints": [[60, 24], [64, 24]]}

    def test_monsters_hop_le(self):
        load("gather", {"monsters": [self.GOOD, dict(self.GOOD, id="M2", pos=[85, 18], state="chase")]}, tuning())

    def test_monsters_khong_hop_le_bi_tu_choi(self):
        t = tuning()
        bad = [dict(self.GOOD, kind="rong"), dict(self.GOOD, pos=[60, 5]),       # loài lạ / ngoài dải độ sâu
               dict(self.GOOD, pos=[101, 24]), dict(self.GOOD, state="lan"),     # ngoài vùng nước / state lạ
               dict(self.GOOD, waypoints=[]), dict(self.GOOD, waypoints=[[200, 24]])]
        for m in bad:
            with self.assertRaises(BadInput, msg=m):
                load("gather", {"monsters": [m]}, t)
        with self.assertRaises(BadInput):  # id trùng
            load("gather", {"monsters": [self.GOOD, self.GOOD]}, t)

    def test_headless_nhan_monsters_va_cho_ca_sau_chay(self):
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {"monsters": [self.GOOD], "random_fish": False}})
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "5", "--scenario", sc,
                                     "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            snap = [r for r in read_jsonl(w.path("o.jsonl")) if r["type"] == "snapshot"][0]
            self.assertEqual([m["id"] for m in snap["monsters"]], ["M1"])

    def test_headless_monsters_sai_exit_2(self):
        with Workdir() as w:
            out = w.path("o.jsonl")
            sc = write_json(w.path("sc.json"), {"gather": {"monsters": [dict(self.GOOD, kind="rong")]}})
            self.assertEqual(run_headless("--mode", "gather", "--seed", "1", "--ticks", "0", "--scenario", sc, "--out", out)[0], 2)
            self.assertFalse(os.path.exists(out))


class KhoCaThe(unittest.TestCase):
    """v1.2: giỏ/kho/giữ chỗ là cá thể. Lỗi -> BadInput (mã 2)."""

    def test_hop_le(self):
        t = tuning(v12=True)
        load("gather", {"hold": [it("I1"), it("I2", "bong_sung", 30), it("I3", "ca_keo", 0)]}, t)
        load("quan", {"stock": [it("I1"), it("I2", "ca_linh", 55.5)],
                      "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "reserved": ["I1"]}]}, t)

    def test_bo_dem_cu_bi_tu_choi_khi_la_v12(self):
        t = tuning(v12=True)
        with self.assertRaises(BadInput):
            load("gather", {"hold": ["ca_loc"]}, t)
        with self.assertRaises(BadInput):
            load("quan", {"stock": {"ca_loc": 1}}, t)

    def test_cua_so_gia_tri_hong(self):
        t = tuning(v12=True)
        bad_holds = [[it("I1"), it("I1")],                                  # trùng id
                     [it("I1", fresh=101)], [it("I1", fresh=-1)],           # fresh ngoài [0,100]
                     [{"id": "I1", "kind": "ca_loc"}],                      # thiếu fresh
                     [{"id": "I1", "kind": "ca_loc", "fresh": 5, "x": 1}],  # trường lạ
                     [it("I1", kind="ca_la_lung")], [{"id": "", "kind": "ca_loc", "fresh": 5}],
                     [{"id": "I1", "kind": "ca_loc", "fresh": True}]]       # bool không phải số
        for h in bad_holds:
            with self.assertRaises(BadInput, msg=h):
                load("gather", {"hold": h}, t)
        cap = t["gather"]["hold_capacity"]
        with self.assertRaises(BadInput):  # vượt sức chứa
            load("gather", {"hold": [it(f"I{i}") for i in range(cap + 1)]}, t)

    def test_giu_cho_theo_id(self):
        t = tuning(v12=True)
        stock = [it("I1"), it("I2", fresh=29.9), it("I3")]
        cust = lambda cid, tb, res: {"id": cid, "table_id": tb, "dish_id": "ca_loc_nuong_trui", "reserved": res}
        bad = [[cust("C1", "T1", ["I9"])],                                   # id không có trong kho
               [cust("C1", "T1", ["I2"])],                                   # hàng ươn (fresh < 30)
               [cust("C1", "T1", ["I1"]), cust("C2", "T2", ["I1"])],         # trùng giữa các đơn
               [cust("C1", "T1", ["I1", "I1"])], [cust("C1", "T1", "I1")],   # trùng trong đơn / sai kiểu
               [cust("C1", "T1", {"ca_loc": 1})]]                            # giữ theo lượng (cũ)
        for customers in bad:
            with self.assertRaises(BadInput, msg=customers):
                load("quan", {"stock": stock, "customers": customers}, t)

    def test_ngung_o_dung_30(self):
        """fresh = 30 chưa ươn (ươn là < 30): giữ chỗ được; 29.99 thì không."""
        t = tuning(v12=True)
        c = {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "reserved": ["I1"]}
        load("quan", {"stock": [it("I1", fresh=30)], "customers": [c]}, t)
        with self.assertRaises(BadInput):
            load("quan", {"stock": [it("I1", fresh=29.99)], "customers": [c]}, t)

    def test_giu_cho_phai_du_cong_thuc(self):
        t = tuning(v12=True)
        stock = [it("I1"), it("I2", "bong_sung", 90), it("I3", "bong_sung", 90)]
        cust = lambda dish, res: {"id": "C1", "table_id": "T1", "dish_id": dish, "reserved": res}
        load("quan", {"stock": stock, "customers": [cust("goi_bong_sung", ["I2", "I3"])]}, t)   # bông súng ×2: đúng
        for dish, res in (("goi_bong_sung", ["I2"]),            # thiếu 1 bông súng
                          ("goi_bong_sung", ["I1", "I2"]),      # sai loại
                          ("ca_loc_nuong_trui", ["I1", "I2"])):  # dư
            with self.assertRaises(BadInput, msg=(dish, res)):
                load("quan", {"stock": stock, "customers": [cust(dish, res)]}, t)

    def test_co_freshness_nhung_manifest_van_v11_thi_dung_bo_dem(self):
        """Manifest chuyển tiếp: có `freshness` nhưng contract_version vẫn 1.1 -> chưa bật kho cá thể."""
        t = tuning(v12=False)
        t["freshness"] = {"initial": 100, "gather_decay_per_s": 0.5, "quan_decay_per_s": 0.25, "spoiled_below": 30}
        t["_contract_version"] = "1.1"
        load("quan", {"stock": {"ca_loc": 1}}, t)
        load("gather", {"hold": ["ca_loc"]}, t)
        with self.assertRaises(BadInput):
            load("quan", {"stock": [it("I1")]}, t)

    def test_v11_van_dung_bo_dem_cu(self):
        t = tuning(v12=False)
        load("quan", {"stock": {"ca_loc": 2}}, t)
        with self.assertRaises(BadInput):
            load("quan", {"stock": [it("I1")]}, t)


if __name__ == "__main__":
    unittest.main()
