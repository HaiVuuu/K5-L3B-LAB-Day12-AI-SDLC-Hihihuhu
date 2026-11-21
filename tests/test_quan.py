"""Unit tests for QuanSim (sim/quan)."""

import unittest

from chonoi.contract import load_contract
from chonoi.inputs import InputState
from chonoi.runner import Session


def make_session(scenario=None, seed=1, inventory=None):
    tuning = load_contract("game.contract.json")["tuning"]
    return Session("quan", tuning, scenario or {}, seed, inventory=inventory)


def idle():
    return InputState((0.0, 0.0), set(), set())


def press_interact():
    return InputState((0.0, 0.0), {"interact"}, {"interact"})


class QuanSimTests(unittest.TestCase):
    def test_customer_arrives_reserves_stock_and_leaves_releases_stock(self):
        sess = make_session({"stock": {"ca_loc": 1}, "random_customers": True})
        first = sess.sim.t["first_customer_tick"]
        for _ in range(first - 1):
            self.assertEqual(sess.step(idle()), [])
        evs = sess.step(idle())
        self.assertEqual([e["name"] for e in evs], ["customer_arrived"])
        self.assertEqual(evs[0]["data"]["dish_id"], "ca_loc_nuong_trui")
        self.assertEqual(sess.snapshot()["stock"], {})
        sess.sim.random_customers = False

        # Let patience expire -> customer_left + stock released + reputation reduced
        pat = int(round(sess.sim.t["patience_s"] * 60))
        left_evs = []
        for _ in range(pat):
            left_evs.extend(sess.step(idle()))
        names = [e["name"] for e in left_evs]
        self.assertIn("customer_left", names)
        self.assertEqual(sess.snapshot()["stock"], {"ca_loc": 1})
        self.assertAlmostEqual(sess.sim.reputation, 2.5)

    def test_no_dish_when_stock_insufficient(self):
        sess = make_session({"stock": {"bong_sung": 1}, "random_customers": True})
        first = sess.sim.t["first_customer_tick"]
        evs = []
        for _ in range(first):
            evs.extend(sess.step(idle()))
        self.assertEqual([e["name"] for e in evs], ["no_dish"])
        self.assertEqual(sess.snapshot()["customers"], [])

    def test_cook_pick_serve_and_paid_with_tip(self):
        sc = {
            "player": {"pos": [2, 8]},
            "stock": {"ca_loc": 1},
            "random_customers": False,
            "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"}],
        }
        sess = make_session(sc)
        # Stock should be reserved on init
        self.assertEqual(sess.snapshot()["stock"], {})

        # Start cooking at B1 [2, 8]
        evs = sess.step(press_interact())
        self.assertEqual([e["name"] for e in evs], ["cook_started"])
        self.assertEqual(sess.snapshot()["stoves"][0]["state"], "cooking")

        # Wait cook_s (6s = 360 ticks) -> dish_ready
        cook_ticks = int(round(sess.sim.menu["ca_loc_nuong_trui"]["cook_s"] * 60))
        ready_evs = []
        for _ in range(cook_ticks):
            ready_evs.extend(sess.step(idle()))
        self.assertEqual([e["name"] for e in ready_evs], ["dish_ready"])
        self.assertEqual(sess.snapshot()["stoves"][0]["state"], "ready")

        # Pick up dish
        pick_evs = sess.step(press_interact())
        self.assertEqual([e["name"] for e in pick_evs], ["dish_picked"])
        self.assertEqual(sess.snapshot()["hand"], "ca_loc_nuong_trui")
        self.assertEqual(sess.snapshot()["stoves"][0]["state"], "idle")

        # Move to table T1 [9, 2] and serve
        sess.sim.pos = [9.0, 2.0]
        serve_evs = sess.step(press_interact())
        self.assertEqual([e["name"] for e in serve_evs], ["served"])
        self.assertIsNone(sess.snapshot()["hand"])
        self.assertEqual(sess.snapshot()["customers"][0]["state"], "eating")

        # Wait eat_s (10s = 600 ticks) -> paid with tip (60 + 12 = 72) & reputation +0.2
        eat_ticks = int(round(sess.sim.t["eat_s"] * 60))
        paid_evs = []
        for _ in range(eat_ticks):
            paid_evs.extend(sess.step(idle()))
        self.assertEqual([e["name"] for e in paid_evs], ["paid"])
        self.assertEqual(paid_evs[0]["data"]["amount"], 72)
        self.assertEqual(paid_evs[0]["data"]["tip"], 12)
        self.assertEqual(sess.sim.money, 72)
        self.assertAlmostEqual(sess.sim.reputation, 3.2)


if __name__ == "__main__":
    unittest.main()
