"""Phase 3 tests for QuanSim & DaySession (Test Contract v1.2: freshness, item IDs, re-reserve, base_price)."""

import copy
import unittest

from chonoi.contract import load_contract
from chonoi.inputs import InputState
from chonoi.runner import Session


def v12_tuning():
    t = copy.deepcopy(load_contract("game.contract.json")["tuning"])
    t["freshness"] = {
        "initial": 100,
        "gather_decay_per_s": 0.5,
        "quan_decay_per_s": 0.25,
        "spoiled_below": 30,
    }
    return t


def idle():
    return InputState((0.0, 0.0), set(), set())


def press(btn):
    return InputState((0.0, 0.0), {btn}, {btn})


class QuanPhase3Tests(unittest.TestCase):
    def test_spoiled_threshold_re_reserves_freshest_or_marks_unfulfillable(self):
        # I1 spoils on tick 1 (fresh 30 -> 29.9958 < 30); I2 (fresh 80) is available as backup
        sc = {
            "stock": [
                {"id": "I1", "kind": "ca_loc", "fresh": 30},
                {"id": "I2", "kind": "ca_loc", "fresh": 80},
            ],
            "random_customers": False,
            "customers": [
                {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "reserved": ["I1"]},
            ],
        }
        sess = Session("quan", v12_tuning(), sc, seed=1)
        evs = sess.step(idle())
        self.assertEqual([e["name"] for e in evs], ["spoiled"])
        self.assertEqual(evs[0]["data"], {"item_id": "I1", "kind": "ca_loc", "location": "stock"})
        # C1 re-reserved I2
        self.assertEqual(sess.snapshot()["customers"][0]["reserved"], ["I2"])

        # Now test when no backup exists -> unfulfillable
        sc2 = {
            "stock": [{"id": "I1", "kind": "ca_loc", "fresh": 30}],
            "random_customers": False,
            "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "reserved": ["I1"]}],
        }
        sess2 = Session("quan", v12_tuning(), sc2, seed=1)
        sess2.step(idle())
        self.assertEqual(sess2.snapshot()["customers"][0]["reserved"], [])
        self.assertTrue(sess2.snapshot()["customers"][0].get("unfulfillable"))

    def test_cook_started_items_and_freshness_base_price_with_tip(self):
        # ca_loc_nuong_trui base price = 60; fresh 50 -> base_price = floor(60 * 0.5) = 30; tip = floor(30 * 0.2) = 6
        sc = {
            "player": {"pos": [2, 8]},
            "stock": [{"id": "I1", "kind": "ca_loc", "fresh": 50}],
            "random_customers": False,
            "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "reserved": ["I1"]}],
        }
        sess = Session("quan", v12_tuning(), sc, seed=1)
        evs = sess.step(press("interact"))
        self.assertEqual(evs[0]["name"], "cook_started")
        self.assertEqual(len(evs[0]["data"]["items"]), 1)
        self.assertEqual(evs[0]["data"]["items"][0]["id"], "I1")

        # Finish cooking (6s = 360 ticks)
        for _ in range(360):
            sess.step(idle())
        # Pick up
        sess.step(press("interact"))
        # Move to T1 [9, 2] and serve
        sess.sim.pos = [9.0, 2.0]
        sess.step(press("interact"))

        # Wait eat_s (10s = 600 ticks)
        paid_evs = []
        for _ in range(600):
            paid_evs.extend(sess.step(idle()))
        self.assertEqual([e["name"] for e in paid_evs], ["paid"])
        # Note: 1 tick of quan decay before cooking reduced fresh from 50 to 49.99583 -> floor(60 * 49.99583 / 100) = 29, tip = floor(29 * 0.2) = 5
        self.assertEqual(paid_evs[0]["data"]["amount"], 34)
        self.assertEqual(paid_evs[0]["data"]["tip"], 5)

    def test_day_v12_handoff_preserves_item_schema_and_persistent_ids(self):
        sc = {
            "gather": {"hold": ["ca_loc"], "random_fish": False, "time_left_ticks": 1},
            "quan": {"random_customers": False, "time_left_ticks": 1},
        }
        sess = Session("day", v12_tuning(), sc, seed=1, days=2)
        sess.initial_events()
        sess.step(idle())  # gather -> quan
        snap = sess.snapshot()
        self.assertEqual(snap["phase"], "quan")
        self.assertEqual(snap["stock"], [{"id": "I1", "kind": "ca_loc", "fresh": 100.0}])


if __name__ == "__main__":
    unittest.main()
