"""Luật gather theo PRD-0, Test Contract v1.0 E–G; không thay smoke test gốc."""

import copy
import json
import unittest

from chonoi.contract import load_contract
from chonoi.inputs import InputPlayer, InputState
from chonoi.runner import Session
from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


def node(ident="N1", x=20, kind="bong_sung", regrow=0):
    return {"id": ident, "kind": kind, "pos": [x, 0], "regrow_ticks": regrow}


def fish(ident="F1", x=20, kind="ca_linh"):
    return {"id": ident, "kind": kind, "pos": [x, 5]}


class GatherRules(unittest.TestCase):
    def setUp(self):
        self.tuning = copy.deepcopy(load_contract()["tuning"])
        self.g = self.tuning["gather"]
        self.hz = self.tuning["tick_hz"]

    def session(self, player=None, **scenario):
        return Session("gather", self.tuning,
                       {"player": {"pos": [20, 0], **(player or {})},
                        "nodes": [], "fish": [], **scenario}, 42)

    def step(self, session, move=(0, 0), *buttons):
        rows = session.step(InputState(move, {}, set(buttons)))
        return [(r["name"], r["data"]) for r in rows]

    def test_oxygen_clamps_and_empty_is_emitted_once(self):
        s = self.session({"pos": [20, 5], "oxygen_ticks": 1})
        self.assertEqual(self.step(s), [("oxygen_empty", {"oxygen_ticks": 0})])
        self.assertEqual(s.sim.zero_oxy_ticks, 1)
        self.assertEqual(self.step(s), [])
        self.assertEqual(s.sim.oxygen_ticks, 0)
        self.assertEqual(s.sim.zero_oxy_ticks, 2)

    def test_first_choke_is_empty_tick_plus_interval_minus_one(self):
        s = self.session({"pos": [20, 5], "oxygen_ticks": 1})
        interval = self.g["choke_interval_ticks"]
        for _ in range(interval - 1):
            self.step(s)
        self.assertEqual(s.sim.hp, self.g["hp_max"])
        self.assertEqual(self.step(s), [("choke", {"hp": self.g["hp_max"] - 1})])
        self.assertEqual(s.tick, interval)
        self.assertEqual(s.sim.zero_oxy_ticks, 0)
        for _ in range(interval - 1):
            self.step(s)
        self.assertEqual(self.step(s), [("choke", {"hp": self.g["hp_max"] - 2})])

    def test_surface_depth_is_inclusive_refills_and_resets_choke(self):
        s = self.session({"pos": [20, self.g["surface_depth"]], "oxygen_ticks": 0})
        self.assertEqual(self.step(s), [])
        self.assertEqual(s.sim.oxygen_ticks, self.g["oxygen_refill_per_tick"])
        self.assertEqual(s.sim.zero_oxy_ticks, 0)
        s.sim.oxygen_ticks = s.sim.oxygen_max - 1
        self.step(s)
        self.assertEqual(s.sim.oxygen_ticks, s.sim.oxygen_max)

    def test_surfacing_on_choke_deadline_prevents_damage(self):
        self.g["ramp_max_ticks"] = 0
        s = self.session({"pos": [20, self.g["surface_depth"] + 0.01],
                          "oxygen_ticks": 0, "zero_oxy_ticks": self.g["choke_interval_ticks"] - 1})
        rows = self.step(s, (0, -1))
        self.assertEqual([name for name, _ in rows], ["surface"])
        self.assertEqual(rows[0][1]["pos"], s.sim.pos)
        self.assertEqual(s.sim.hp, self.g["hp_max"])
        self.assertEqual(s.sim.zero_oxy_ticks, 0)
        self.assertEqual(s.sim.oxygen_ticks, self.g["oxygen_refill_per_tick"])

    def test_dive_uses_end_position_and_does_not_repeat(self):
        self.g["ramp_max_ticks"] = 0
        s = self.session({"pos": [20, self.g["surface_depth"]]})
        rows = self.step(s, (0, 1))
        self.assertEqual(rows, [("dive", {"pos": list(s.sim.pos)})])
        saved_pos = list(rows[0][1]["pos"])
        self.assertEqual(s.sim.oxygen_ticks, s.sim.oxygen_max - 1)
        self.assertEqual(self.step(s, (0, 1)), [])
        self.assertEqual(rows[0][1]["pos"], saved_pos, "event không giữ tham chiếu vị trí mutable")

    def test_faint_lifo_precedes_catch_and_time(self):
        hold = ["ca_loc", "bong_sung", "bong_dien_dien"]
        s = self.session({"pos": [20, 5], "hp": 1, "oxygen_ticks": 0,
                          "zero_oxy_ticks": self.g["choke_interval_ticks"] - 1},
                         hold=hold, fish=[fish()], time_left_ticks=1)
        self.assertEqual(self.step(s, (0, 0), "catch", "interact"), [
            ("choke", {"hp": 0}),
            ("faint", {"cause": "choke", "lost": list(reversed(hold)), "hp": 0}),
            ("gather_end", {"reason": "fainted", "inventory": {"items": {}}}),
        ])
        self.assertEqual(s.sim.hold, [])
        self.assertEqual(len(s.sim.fish), 1)
        self.assertEqual(self.step(s, (0, 0), "catch"), [])

    def test_nearest_ready_node_at_radius_and_natural_id_tie(self):
        r = self.g["interact_radius"]
        s = self.session(nodes=[node("N10", 20 + r), node("N1", 20, regrow=2), node("N2", 20 - r)])
        self.assertEqual(self.step(s, (0, 0), "interact"), [
            ("gather", {"node_id": "N2", "kind": "bong_sung", "amount": self.g["node_yield"]})])
        self.assertEqual(s.sim.hold, ["bong_sung"] * self.g["node_yield"])
        self.assertEqual(next(n for n in s.sim.nodes if n["id"] == "N2")["regrow_ticks"],
                         round(self.g["regrow_s"] * self.hz))

    def test_node_outside_radius_or_underwater_is_not_gathered(self):
        for pos, target in [([20, 0], node(x=20 + self.g["interact_radius"] + 0.001)),
                            ([20, self.g["surface_depth"] + 0.01], node())]:
            with self.subTest(pos=pos):
                s = self.session({"pos": pos}, nodes=[target])
                self.assertEqual(self.step(s, (0, 0), "interact"), [])
                self.assertEqual(s.sim.hold, [])

    def test_full_hold_keeps_node_ready(self):
        hold = ["ca_loc"] * self.g["hold_capacity"]
        s = self.session(hold=hold, nodes=[node()])
        self.assertEqual(self.step(s, (0, 0), "interact"), [
            ("hold_full", {"action": "gather", "node_id": "N1", "required": self.g["node_yield"], "free": 0})])
        self.assertEqual(s.sim.hold, hold)
        self.assertEqual(s.sim.nodes[0]["regrow_ticks"], 0)

    def test_regrowth_sorted_then_harvested_in_same_tick(self):
        s = self.session(nodes=[node("N10", regrow=1), node("N2", regrow=1)])
        rows = self.step(s, (0, 0), "interact")
        self.assertEqual(rows, [("node_regrown", {"node_id": "N2"}),
                                ("node_regrown", {"node_id": "N10"}),
                                ("gather", {"node_id": "N2", "kind": "bong_sung", "amount": self.g["node_yield"]})])

    def test_node_regrows_exactly_after_configured_delay(self):
        self.g["regrow_s"] = 0.1
        s = self.session(nodes=[node()])
        self.step(s, (0, 0), "interact")
        delay = round(self.g["regrow_s"] * self.hz)
        for _ in range(delay - 1):
            self.assertEqual(self.step(s), [])
        self.assertEqual(self.step(s)[0], ("node_regrown", {"node_id": "N1"}))

    def test_dock_before_harvest_at_exact_radius_on_last_tick(self):
        x, d = self.g["dock_pos"]
        pos = [x + self.g["dock_radius"], d]
        s = self.session({"pos": pos}, nodes=[node(x=pos[0])], hold=["ca_loc"], time_left_ticks=1)
        self.assertEqual(self.step(s, (0, 0), "interact", "catch"), [
            ("gather_end", {"reason": "docked", "inventory": {"items": {"ca_loc": 1}}})])
        self.assertEqual(s.sim.nodes[0]["regrow_ticks"], 0)

    def test_dock_distance_uses_both_axes_even_underwater(self):
        x, d = self.g["dock_pos"]
        s = self.session({"pos": [x, d + self.g["dock_radius"]]})
        self.assertEqual(self.step(s, (0, 0), "interact")[0][1]["reason"], "docked")
        s = self.session({"pos": [x, d + self.g["dock_radius"] + 0.001]})
        self.assertEqual(self.step(s, (0, 0), "interact"), [])

    def test_fish_whole_yield_at_radius_tie_and_hold_order(self):
        r = self.g["catch_radius"]
        s = self.session({"pos": [20, 5]}, fish=[fish("F10", 20 + r), fish("F2", 20 - r)],
                         hold=["bong_sung"])
        self.assertEqual(self.step(s, (0, 0), "catch"), [
            ("fish_caught", {"fish_id": "F2", "kind": "ca_linh", "yield": self.g["fish_yield"]["ca_linh"]})])
        self.assertEqual(s.sim.hold, ["bong_sung"] + ["ca_linh"] * self.g["fish_yield"]["ca_linh"])
        self.assertEqual([f["id"] for f in s.sim.fish], ["F10"])
        self.assertEqual(s.sim.catch_cd_ticks, round(self.g["catch_cooldown_s"] * self.hz))

    def test_partial_capacity_keeps_nearest_fish_and_does_not_try_smaller(self):
        s = self.session({"pos": [20, 5]},
                         hold=["ca_loc"] * (self.g["hold_capacity"] - 1),
                         fish=[fish(), fish("F2", 21, "ca_loc")])
        self.assertEqual(self.step(s, (0, 0), "catch"), [
            ("hold_full", {"action": "catch", "fish_id": "F1",
                           "required": self.g["fish_yield"]["ca_linh"], "free": 1})])
        self.assertEqual(len(s.sim.fish), 2)
        self.assertEqual(len(s.sim.hold), self.g["hold_capacity"] - 1)
        self.assertEqual(s.sim.catch_cd_ticks, 0)

    def test_surface_or_miss_does_not_start_cooldown(self):
        for pos, target in [([20, 0], fish()),
                            ([20, 5], fish(x=20 + self.g["catch_radius"] + 0.001))]:
            with self.subTest(pos=pos):
                s = self.session({"pos": pos}, fish=[target])
                self.assertEqual(self.step(s, (0, 0), "catch"), [])
                self.assertEqual(s.sim.catch_cd_ticks, 0)
                self.assertEqual(len(s.sim.fish), 1)

    def test_cooldown_reusable_at_exact_deadline(self):
        s = self.session({"pos": [20, 5]}, fish=[fish("F1", kind="ca_loc"), fish("F2", kind="ca_loc")])
        self.step(s, (0, 0), "catch")
        delay = round(self.g["catch_cooldown_s"] * self.hz)
        for _ in range(delay - 1):
            self.assertEqual(self.step(s, (0, 0), "catch"), [])
        self.assertEqual(self.step(s, (0, 0), "catch")[0][0], "fish_caught")
        self.assertEqual(s.tick, 1 + delay)

    def test_buttons_only_act_on_rising_edge(self):
        for button, pos, objects, name in [
            ("interact", [20, 0], {"nodes": [node(), node("N2")]}, "gather"),
            ("catch", [20, 5], {"fish": [fish(), fish("F2")]}, "fish_caught"),
        ]:
            with self.subTest(button=button):
                self.g["catch_cooldown_s"] = 0
                s = self.session({"pos": pos}, **objects)
                player = InputPlayer([{"tick": 0, button: True}, {"tick": 2, button: False},
                                      {"tick": 3, button: True}])
                rows = [r for tick in range(4) for r in s.step(player.advance(tick))]
                self.assertEqual([r["tick"] for r in rows if r["name"] == name], [1, 4])

    def test_last_tick_harvest_and_catch_enter_inventory(self):
        for pos, objects, button, kind, qty in [
            ([20, 0], {"nodes": [node()]}, "interact", "bong_sung", self.g["node_yield"]),
            ([20, 5], {"fish": [fish()]}, "catch", "ca_linh", self.g["fish_yield"]["ca_linh"]),
        ]:
            with self.subTest(button=button):
                s = self.session({"pos": pos}, time_left_ticks=1, **objects)
                rows = self.step(s, (0, 0), button)
                self.assertEqual(rows[-1], ("gather_end", {"reason": "time", "inventory": {"items": {kind: qty}}}))

    def test_tuning_controls_oxygen_choke_yield_capacity_and_cooldown(self):
        self.g.update(oxygen_refill_per_tick=9, choke_interval_ticks=3,
                      hold_capacity=4, catch_cooldown_s=0.1, node_yield=2)
        self.g["fish_yield"]["ca_linh"] = 2
        s = self.session(nodes=[node()])
        self.step(s, (0, 0), "interact")
        self.assertEqual(s.sim.hold, ["bong_sung"] * 2)
        s = self.session({"pos": [20, 5], "oxygen_ticks": 1}, fish=[fish()])
        self.step(s, (0, 0), "catch")
        self.assertEqual(s.sim.hold, ["ca_linh"] * 2)
        self.assertEqual(s.sim.catch_cd_ticks, round(0.1 * self.hz))
        self.step(s)
        self.assertEqual(self.step(s), [("choke", {"hp": self.g["hp_max"] - 1})])


class GatherHeadless(unittest.TestCase):
    def test_faint_overwrites_inventory_with_empty_and_stops_once(self):
        g = load_contract()["tuning"]["gather"]
        with Workdir() as w:
            scenario = write_json(w.path("sc.json"), {"gather": {
                "player": {"pos": [20, 5], "hp": 1, "oxygen_ticks": 0,
                           "zero_oxy_ticks": g["choke_interval_ticks"] - 1},
                "hold": ["ca_loc", "bong_sung"], "random_fish": False}})
            inv = write_json(w.path("inv.json"), {"items": {"ca_loc": 10}})
            out = w.path("out.jsonl")
            code, err = run_headless("--mode", "gather", "--seed", "42", "--ticks", "600",
                                     "--scenario", scenario, "--out", out, "--inventory-out", inv)
            self.assertEqual(code, 0, err)
            rows = read_jsonl(out)
            self.assertEqual(len(events(rows, "gather_end")), 1)
            self.assertEqual(rows[-1]["ticks"], 1)
            self.assertEqual(rows[-1]["reason"], "fainted")
            self.assertEqual(snapshots(rows)[-1]["hold"], [])
            with open(inv, encoding="utf-8") as f:
                self.assertEqual(json.load(f), events(rows, "gather_end")[0]["data"]["inventory"])

    def test_tick_limit_keeps_existing_inventory_bytes(self):
        with Workdir() as w:
            inv = write_json(w.path("inv.json"), {"items": {"ca_loc": 9}})
            with open(inv, "rb") as f:
                before = f.read()
            code, err = run_headless("--mode", "gather", "--seed", "42", "--ticks", "1",
                                     "--out", w.path("out.jsonl"), "--inventory-out", inv)
            self.assertEqual(code, 0, err)
            with open(inv, "rb") as f:
                self.assertEqual(f.read(), before)

    def test_real_harvest_transfers_to_quan_and_replays_byte_identically(self):
        with Workdir() as w:
            scenario = write_json(w.path("sc.json"), {"gather": {"player": {"pos": [20, 0]},
                "nodes": [node()], "fish": [], "time_left_ticks": 1}})
            inputs = write_json(w.path("in.json"), frames({"tick": 0, "interact": True}))
            outputs, inventories = [], []
            for i in range(2):
                out, inv = w.path(f"g{i}.jsonl"), w.path(f"inv{i}.json")
                code, err = run_headless("--mode", "gather", "--seed", "42", "--ticks", "1",
                                         "--scenario", scenario, "--inputs", inputs, "--out", out,
                                         "--inventory-out", inv)
                self.assertEqual(code, 0, err)
                with open(out, "rb") as f:
                    outputs.append(f.read())
                with open(inv, "rb") as f:
                    inventories.append(f.read())
            self.assertEqual(outputs[0], outputs[1])
            self.assertEqual(inventories[0], inventories[1])
            quan = w.path("q.jsonl")
            code, err = run_headless("--mode", "quan", "--seed", "42", "--ticks", "0",
                                     "--inventory", w.path("inv0.json"), "--out", quan)
            self.assertEqual(code, 0, err)
            self.assertEqual(snapshots(read_jsonl(quan))[0]["stock"], json.loads(inventories[0])["items"])


if __name__ == "__main__":
    unittest.main()
