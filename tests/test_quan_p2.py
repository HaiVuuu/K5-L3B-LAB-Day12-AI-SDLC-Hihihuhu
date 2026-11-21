"""Phase 2 tests for QuanSim (2B/4T/6 dishes, oldest order, shift close), DaySession, ShopSim, and Pause."""

import copy
import unittest

from chonoi.contract import load_contract
from chonoi.inputs import InputState
from chonoi.runner import Session


def v11_tuning():
    t = copy.deepcopy(load_contract("game.contract.json")["tuning"])
    t["quan"]["stoves"] = [{"id": "B1", "pos": [2, 8]}, {"id": "B2", "pos": [5, 8]}]
    t["quan"]["tables"] = [
        {"id": "T1", "pos": [9, 2]},
        {"id": "T2", "pos": [13, 2]},
        {"id": "T3", "pos": [9, 6]},
        {"id": "T4", "pos": [13, 6]},
    ]
    t["menu"].update({
        "canh_chua_ca_loc": {"recipe": {"ca_loc": 1, "bong_dien_dien": 1}, "cook_s": 8, "price": 90},
        "ca_keo_nuong": {"recipe": {"ca_keo": 2}, "cook_s": 6, "price": 70},
        "lau_mam": {"recipe": {"ca_linh": 2, "ca_keo": 1, "keo_neo": 1, "bong_dien_dien": 1}, "cook_s": 12, "price": 200},
    })
    t["day_plan"] = [
        {"day": 1, "dishes": {"ca_loc_nuong_trui": 3, "goi_bong_sung": 3}, "ingredients": {"ca_loc": 3, "bong_sung": 6}},
        {"day": 2, "dishes": {"ca_loc_nuong_trui": 2, "lau_ca_linh_dien_dien": 2}, "ingredients": {"ca_loc": 2, "ca_linh": 6, "bong_dien_dien": 2}},
    ]
    t["shop"] = {
        "max_ticks": 600,
        "upgrades": {
            "oxygen": [{"level": 1, "price": 200, "oxygen_max_s": 45}, {"level": 2, "price": 400, "oxygen_max_s": 60}],
            "hp": [{"level": 1, "price": 250, "hp_max": 4}, {"level": 2, "price": 500, "hp_max": 5}],
        },
    }
    return t


def idle():
    return InputState((0.0, 0.0), set(), set())


def press(btn, buy=None):
    return InputState((0.0, 0.0), {btn}, {btn}, buy=buy)


class QuanPhase2Tests(unittest.TestCase):
    def test_oldest_order_priority_by_order_tick_then_table_id(self):
        sc = {
            "player": {"pos": [2, 8]},
            "stock": {"ca_loc": 1, "bong_sung": 2},
            "random_customers": False,
            "customers": [
                {"id": "C1", "table_id": "T2", "dish_id": "goi_bong_sung", "order_tick": 10},
                {"id": "C2", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "order_tick": 10},
            ],
        }
        sess = Session("quan", v11_tuning(), sc, seed=1)
        evs = sess.step(press("interact"))
        self.assertEqual(evs[0]["name"], "cook_started")
        self.assertEqual(evs[0]["data"]["dish_id"], "ca_loc_nuong_trui")

    def test_shift_close_pays_eating_and_clears_waiting_without_penalty(self):
        sc = {
            "stock": {"ca_loc": 1, "bong_sung": 2},
            "random_customers": False,
            "time_left_ticks": 1,
            "customers": [
                {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "state": "eating", "eat_ticks_left": 100},
                {"id": "C2", "table_id": "T2", "dish_id": "goi_bong_sung", "state": "waiting"},
            ],
        }
        sess = Session("quan", v11_tuning(), sc, seed=1)
        evs = sess.step(idle())
        names = [e["name"] for e in evs]
        self.assertEqual(names, ["paid", "quan_end"])
        self.assertEqual(sess.sim.money, 72)
        self.assertAlmostEqual(sess.sim.reputation, 3.2)
        self.assertEqual(sess.snapshot()["customers"], [])

    def test_day_loop_shop_upgrade_applies_next_day_and_pause(self):
        sc = {
            "day": {"money": 200, "earned": 200},
            "gather": {"hold": ["ca_loc"], "random_fish": False, "time_left_ticks": 1},
            "quan": {"random_customers": False, "time_left_ticks": 1},
        }
        sess = Session("day", v11_tuning(), sc, seed=1, days=2)
        init_names = [e["name"] for e in sess.initial_events()]
        self.assertEqual(init_names, ["day_start", "day_plan", "phase_start"])

        # Tick 1: pause
        p_evs = sess.step(press("pause"))
        self.assertEqual([e["name"] for e in p_evs], ["paused"])
        self.assertEqual(sess.snapshot()["state"], "paused")
        self.assertEqual(sess.sim_tick, 0)

        # Tick 2: still paused -> no sim progress
        self.assertEqual(sess.step(idle()), [])
        self.assertEqual(sess.sim_tick, 0)

        # Tick 3: resume + gather finishes -> phase_start(quan)
        r_evs = sess.step(press("pause"))
        self.assertEqual([e["name"] for e in r_evs], ["resumed", "gather_end", "phase_start"])
        self.assertEqual(sess.snapshot()["phase"], "quan")

        # Tick 4: quan finishes -> phase_start(shop)
        q_evs = sess.step(idle())
        self.assertEqual([e["name"] for e in q_evs], ["quan_end", "phase_start"])
        self.assertEqual(sess.snapshot()["phase"], "shop")

        # Tick 5: buy oxygen level 1 (200) and close shop -> day 2 starts with active_upgrades.oxygen == 1
        s_evs = sess.step(InputState((0.0, 0.0), {"shop_done"}, {"shop_done"}, buy="oxygen"))
        self.assertEqual([e["name"] for e in s_evs], ["bought", "shop_end", "day_start", "day_plan", "phase_start"])
        snap = sess.snapshot()
        self.assertEqual(snap["day"], 2)
        self.assertEqual(snap["upgrades"], {"oxygen": 1})
        self.assertEqual(snap["active_upgrades"], {"oxygen": 1})
        self.assertEqual(snap["player"]["oxygen_max_ticks"], 45 * 60)


if __name__ == "__main__":
    unittest.main()
