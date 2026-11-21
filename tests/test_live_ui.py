"""Test lớp live cho client mới (Phase 1-2, PO/UI): menu, cổng màn hình, pause, Shop. Chỉ starter Python."""

import json
import time
import unittest

from chonoi.contract import load_contract
from chonoi.live import LiveGame

SHOP = {"max_ticks": 3000, "upgrades": {"oxygen": [{"level": 1, "price": 50, "oxygen_max_s": 40}]}}


def tuning():
    t = load_contract()["tuning"]
    t["shop"] = SHOP
    return t


def state(g):
    return json.loads(g.state_json())


def wait(cond, secs=3.0):
    end = time.time() + secs
    while time.time() < end:
        if cond():
            return True
        time.sleep(0.02)
    return cond()


class LiveGates(unittest.TestCase):
    def setUp(self):
        self.games = []

    def tearDown(self):
        for g in self.games:
            g.stop()

    def game(self, mode, scenario=None, **kw):
        g = LiveGame(mode, tuning(), scenario or {}, 1, **kw)
        self.games.append(g)
        g.start()
        return g

    def test_menu_giu_sim_dung_den_khi_start(self):
        g = self.game("gather", menu=True)
        time.sleep(0.3)
        st = state(g)
        self.assertEqual((st["gate"], st["tick"]), ("menu", 0))
        g.advance_gate()  # menu không đóng bằng /continue
        self.assertEqual(state(g)["gate"], "menu")
        g.leave_menu()
        self.assertIsNone(state(g)["gate"])
        self.assertTrue(wait(lambda: state(g)["tick"] > 3))

    def test_day_menu_roi_gioi_thieu_ngay(self):
        g = self.game("day", menu=True, days=2)
        g.leave_menu()
        self.assertEqual(state(g)["gate"], "day_intro")
        time.sleep(0.2)
        self.assertEqual(state(g)["tick"], 0)
        g.advance_gate()
        self.assertTrue(wait(lambda: state(g)["tick"] > 3))
        st = state(g)
        self.assertEqual((st["mode"], st["phase"], st["day"]), ("day", "gather", 1))
        self.assertEqual(st["catalog"]["days"], 2)

    def test_day_cap_ben_dung_o_evening_roi_result_roi_shop_mua_xong(self):
        sc = {"gather": {"hold": ["bong_sung"]}, "quan": {"time_left_ticks": 30, "random_customers": False},
              "day": {"money": 100}}
        g = self.game("day", sc, days=1)
        self.assertEqual(state(g)["gate"], "day_intro")
        g.advance_gate()
        g.set_input({"interact": True})
        self.assertTrue(wait(lambda: state(g)["gate"] == "evening_intro"))
        self.assertEqual(state(g)["stock"], {"bong_sung": 1})
        g.advance_gate()
        self.assertTrue(wait(lambda: state(g)["gate"] == "day_result"))
        self.assertEqual(state(g)["phase"], "shop")
        g.advance_gate()
        g.set_input({"buy": "oxygen"})
        self.assertTrue(wait(lambda: state(g)["upgrades"].get("oxygen") == 1))
        self.assertEqual(state(g)["money"], 50)
        g.set_input({"shop_done": True})
        self.assertTrue(wait(lambda: state(g)["finished"]))
        self.assertEqual(state(g)["reason"], "days_complete")

    def test_pause_dung_dong_ho_va_tiep_tuc(self):
        g = self.game("gather")
        g.set_input({"pause": True})
        g.set_input({"pause": False})
        self.assertTrue(wait(lambda: state(g)["state"] == "paused"))
        left = state(g)["time_left_ticks"]
        time.sleep(0.3)
        self.assertEqual(state(g)["time_left_ticks"], left)
        g.set_input({"pause": True})
        g.set_input({"pause": False})
        self.assertTrue(wait(lambda: state(g)["time_left_ticks"] < left))

    def test_input_bi_bo_qua_khi_dang_o_cong(self):
        g = self.game("gather", menu=True)
        g.set_input({"move": [1, 0]})
        g.leave_menu()
        time.sleep(0.3)
        st = state(g)
        self.assertEqual(st["player"]["pos"], [2, 0])

    def test_catalog_co_do_tuoi_de_client_tinh_ngan_on(self):
        t = tuning()
        t["freshness"] = {"initial": 100, "spoiled_below": 30}
        g = LiveGame("gather", t, {}, 1)
        self.games.append(g)
        g.start()
        self.assertEqual(state(g)["catalog"]["freshness"]["spoiled_below"], 30)

    def test_buy_khong_hop_le_bi_tu_choi(self):
        g = self.game("day")
        with self.assertRaises(ValueError):
            g.set_input({"buy": ""})


if __name__ == "__main__":
    unittest.main()
