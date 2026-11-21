"""Phần Minh: TICKET-02 §1.1/1.2/4, không giả lập day/pause của Hải hay parser của QA."""

import copy
import json
import math
import unittest

from chonoi.contract import load_contract, validate_tuning
from chonoi.errors import BadInput
from chonoi.ids import IdAllocator
from chonoi.inputs import BUTTONS_V11, InputPlayer, InputState, LiveInputs, load_frames
from chonoi.inventory import KINDS_P2, read_inventory, validate_items, write_inventory
from chonoi.rng import Streams
from chonoi.sim.gather import GatherSim
from helpers import Workdir, frames, read_jsonl, run_headless, snapshots, write_json


def school(ident="F1", kind="ca_linh", pos=(20, 5), heading=0, age=0):
    return {"id": ident, "kind": kind, "pos": list(pos), "heading_deg": heading, "age_ticks": age}


def crocodile(ident="M1", pos=(20, 12), **fields):
    return {"id": ident, "kind": "ca_sau", "pos": list(pos),
            "waypoints": [list(pos), [pos[0] + 4, pos[1]]], **fields}


class P2Base(unittest.TestCase):
    def setUp(self):
        self.tuning = copy.deepcopy(load_contract()["tuning"])
        self.g = self.tuning["gather"]

    def sim(self, player=None, *, seed=7, day=1, active_upgrades=None, **scenario):
        return GatherSim(self.tuning, {"player": {"pos": [20, 0], **(player or {})},
                                      "fish": [], "nodes": [], "monsters": [], **scenario},
                         Streams(seed), IdAllocator(), day=day, active_upgrades=active_upgrades)

    def step(self, sim, *buttons, move=(0, 0)):
        return sim.step(InputState(move, {}, set(buttons)))


class P2ManifestAndInputs(P2Base):
    def test_manifest_values_and_all_five_plan_totals(self):
        self.assertEqual(load_contract()["contract_version"], "1.1")
        self.assertEqual(self.g["fish_initial"], 8)
        self.assertEqual(self.g["fish_max"], 12)
        self.assertEqual(self.g["fish_weights"], {"ca_linh": 40, "ca_loc": 30, "ca_keo": 30})
        self.assertEqual(self.g["fish_yield"], {"ca_linh": 3, "ca_loc": 1, "ca_keo": 2})
        self.assertEqual(len(self.g["nodes"]), 6)
        self.assertEqual([n["pos"] for n in self.g["nodes"][-2:]], [[76, 0], [90, 0]])
        self.assertEqual(len(self.tuning["menu"]), 6)
        self.assertEqual(len(self.tuning["quan"]["stoves"]), 2)
        self.assertEqual(len(self.tuning["quan"]["tables"]), 4)
        self.assertEqual([sum(p["ingredients"].values()) for p in self.tuning["day_plan"]], [9, 10, 12, 9, 10])
        validate_tuning(self.tuning)

    def test_bad_p2_data_is_rejected(self):
        for field, value in [("fish_initial", True), ("fish_turn_ticks", 0), ("fish_speed", float("nan")),
                             ("fish_depths", {}), ("fish_spawn_x", []), ("fish_weights", {})]:
            with self.subTest(field=field):
                tuning = copy.deepcopy(self.tuning)
                tuning["gather"][field] = value
                with self.assertRaises(BadInput):
                    validate_tuning(tuning)
        self.tuning["day_plan"][0]["ingredients"]["ca_loc"] += 1
        with self.assertRaises(BadInput):
            validate_tuning(self.tuning)

    def test_six_ingredients_roundtrip_without_changing_schema(self):
        items = {kind: i + 1 for i, kind in enumerate(KINDS_P2)}
        with Workdir() as work:
            path = work.path("inventory.json")
            write_inventory(path, items)
            self.assertEqual(read_inventory(path), items)
            with open(path, encoding="utf-8") as stream:
                self.assertEqual(set(json.load(stream)), {"items"})
        for invalid in ({"ca_keo": True}, {"keo_neo": -1}, {"ca_la": 1}):
            with self.assertRaises(BadInput):
                validate_items(invalid)

    def test_input_buy_is_one_frame_and_edges_survive_phase_boundaries(self):
        with Workdir() as work:
            path = write_json(work.path("inputs.json"), frames(
                {"tick": 0, "pause": True, "shop_done": True, "buy": "oxygen"},
                {"tick": 2, "pause": False}, {"tick": 3, "pause": True, "buy": "hp"}))
            player = InputPlayer(load_frames(path))
            first = player.advance(0)
            self.assertEqual(first.buy, "oxygen")
            self.assertTrue(first.pressed("pause"))
            following = player.advance(1)
            self.assertIsNone(following.buy)
            self.assertFalse(following.pressed("pause"))
            self.assertFalse(following.pressed("shop_done"))
            player.advance(2)
            self.assertTrue(player.advance(3).pressed("pause"))
            self.assertIsNone(player.advance(4).buy)

    def test_load_frames_supports_cli_allow_buy_keyword_and_explicit_disable(self):
        with Workdir() as work:
            path = write_json(work.path("inputs.json"), frames({"tick": 0, "buy": "oxygen"}))
            loaded = load_frames(path, buttons=BUTTONS_V11, allow_buy=True)
            self.assertEqual(InputPlayer(loaded).advance(0).buy, "oxygen")
            self.assertEqual(load_frames(path)[0]["buy"], "oxygen")
            with self.assertRaises(BadInput):
                load_frames(path, buttons=BUTTONS_V11, allow_buy=False)

    def test_input_rejects_wrong_types_and_accepts_disabled_extension_buttons(self):
        with Workdir() as work:
            for values in ({"buy": ""}, {"buy": 1}, {"pause": 1}, {"shop_done": "true"}, {"photo": []}):
                path = write_json(work.path("bad.json"), frames({"tick": 0, **values}))
                with self.assertRaises(BadInput):
                    load_frames(path)
            path = write_json(work.path("ok.json"), frames({"tick": 0, "attack": True, "photo": True}))
            player = InputPlayer(load_frames(path))
            self.assertEqual(self.sim().step(player.advance(0)), [])
        live = LiveInputs()
        live.set(buy="hp", pause=True)
        self.assertEqual(live.advance().buy, "hp")
        self.assertIsNone(live.advance().buy)


class P2Fish(P2Base):
    def test_initial_eight_unique_geometric_points_seeded(self):
        sims = [GatherSim(self.tuning, {}, Streams(42), IdAllocator()) for _ in range(2)]
        self.assertEqual(sims[0].snapshot(), sims[1].snapshot())
        schools = sims[0].fish
        self.assertEqual(len(schools), 8)
        self.assertEqual(len({tuple(f["pos"]) for f in schools}), 8)
        self.assertEqual([f["id"] for f in schools], [f"F{i}" for i in range(1, 9)])
        pairs = [(kind, x, d) for kind in self.g["fish_spawn_depths"]
                 for x in self.g["fish_spawn_x"] for d in self.g["fish_spawn_depths"][kind]]
        self.assertEqual(len(pairs), 36)
        self.assertEqual(len({(x, d) for _, x, d in pairs}), 30)
        for f in schools:
            self.assertIn((f["kind"], *f["pos"]), pairs)
            self.assertEqual(f["age_ticks"], 0)

    def test_reflection_preserves_remainder_at_wall_depth_and_corner(self):
        distance = self.g["fish_speed"] / self.tuning["tick_hz"]
        for pos, heading, expected_pos, expected_heading in [
            ((95.99, 5), 0, [96 - (distance - 0.01), 5], 180),
            ((20, 11.99), 90, [20, 12 - (distance - 0.01)], 270),
            ((95.99, 11.99), 45, [96 - (distance / math.sqrt(2) - 0.01),
                                     12 - (distance / math.sqrt(2) - 0.01)], 225),
            ((96 - distance, 5), 0, [96, 5], 180),
        ]:
            with self.subTest(heading=heading, pos=pos):
                sim = self.sim(fish=[school(pos=pos, heading=heading)])
                self.step(sim)
                for actual, expected in zip(sim.fish[0]["pos"], expected_pos):
                    self.assertAlmostEqual(actual, expected)
                self.assertAlmostEqual(sim.fish[0]["heading_deg"], expected_heading)

    def test_turns_on_120th_swim_before_moving(self):
        sim = self.sim(fish=[school(age=118)])
        self.step(sim)
        self.assertEqual(sim.fish[0]["age_ticks"], 119)
        before = list(sim.fish[0]["pos"])
        expected_heading = Streams(7).get("fish_turn:F1").uniform(0, 360)
        self.step(sim)
        self.assertEqual(sim.fish[0]["age_ticks"], 120)
        self.assertAlmostEqual(sim.fish[0]["heading_deg"], expected_heading)
        distance = self.g["fish_speed"] / self.tuning["tick_hz"]
        self.assertAlmostEqual(sim.fish[0]["pos"][0] - before[0], distance * math.cos(math.radians(expected_heading)))
        self.assertAlmostEqual(sim.fish[0]["pos"][1] - before[1], distance * math.sin(math.radians(expected_heading)))

    def test_random_false_freezes_fixture_age_heading_and_disables_spawn(self):
        sim = self.sim(fish=[school(age=119)], random_fish=False)
        before = copy.deepcopy(sim.fish)
        for _ in range(self.g["fish_spawn_ticks"] * 2):
            self.assertEqual(self.step(sim), [])
        self.assertEqual(sim.fish, before)

    def test_catch_uses_position_before_swim(self):
        sim = self.sim({"pos": [20, 5]}, fish=[school(pos=(22.01, 5), heading=180)])
        self.assertEqual(self.step(sim, "catch"), [])
        self.assertEqual(sim.catch_cd_ticks, 0)
        self.assertEqual(self.step(sim, "catch")[0][0], "fish_caught")

    def test_spawn_tick_cap_id_and_newborn_waits_until_next_step(self):
        existing = [school(f"F{i}", pos=(30 + i, 5)) for i in range(1, 13)]
        sim = self.sim({"pos": [20, 5]}, fish=existing)
        sim.phase_tick = self.g["fish_spawn_ticks"] - 1
        self.assertEqual(self.step(sim), [])
        self.assertEqual(len(sim.fish), 12)
        sim.phase_tick = self.g["fish_spawn_ticks"] - 1
        sim.fish[0]["pos"] = [20, 5]
        rows = self.step(sim, "catch")
        self.assertEqual([name for name, _ in rows], ["fish_caught", "fish_spawned"])
        baby = next(f for f in sim.fish if f["id"] == "F13")
        self.assertEqual(len(sim.fish), 12)
        self.assertEqual(baby["age_ticks"], 0)
        self.assertEqual(rows[-1][1], {"id": "F13", "kind": baby["kind"], "pos": baby["pos"]})
        self.assertTrue(all(math.dist(baby["pos"], f["pos"]) > self.g["fish_spawn_clearance"]
                            for f in sim.fish if f is not baby))
        self.step(sim)
        self.assertEqual(baby["age_ticks"], 1)

    def test_spawn_renormalizes_to_species_with_free_point_and_strict_clearance(self):
        points = {(x, d) for depths in self.g["fish_spawn_depths"].values()
                  for x in self.g["fish_spawn_x"] for d in depths}
        points.remove((90, 27))
        self.g["fish_max"] = len(points) + 2
        sim = self.sim(fish=[school(f"F{i}", pos=p) for i, p in enumerate(sorted(points), 1)])
        rows = []
        self.assertTrue(sim._spawn_fish(events=rows))
        self.assertEqual(rows[0][1]["kind"], "ca_keo")
        self.assertEqual(rows[0][1]["pos"], [90, 27])
        sim.fish[-1]["pos"] = [89, 27]  # đúng 1 m vẫn không hợp lệ.
        self.assertFalse(sim._spawn_fish(events=rows))
        self.assertEqual(len(rows), 1)

    def test_no_spawn_or_swim_after_time_or_docking(self):
        for docked in (False, True):
            sim = self.sim({"pos": [2, 0] if docked else [20, 0]}, fish=[school(age=119)], time_left_ticks=1)
            sim.phase_tick = self.g["fish_spawn_ticks"] - 1
            before = copy.deepcopy(sim.fish)
            self.assertEqual(self.step(sim, *(["interact"] if docked else []))[-1][1]["reason"],
                             "docked" if docked else "time")
            self.assertEqual(sim.fish, before)

    def test_swimming_remains_inside_each_species_bounds(self):
        sim = self.sim(fish=[school("F1"), school("F2", "ca_loc", (96, 20), 45),
                             school("F3", "ca_keo", (4, 22), 225)])
        for _ in range(1000):
            self.step(sim)
            for f in sim.fish:
                self.assertTrue(self.g["fish_x"][0] <= f["pos"][0] <= self.g["fish_x"][1])
                lo, hi = self.g["fish_depths"][f["kind"]]
                self.assertTrue(lo <= f["pos"][1] <= hi)


class P2Monsters(P2Base):
    def test_default_day_layout_and_fixture_replacement(self):
        for day, expected in ((1, ["M1"]), (2, ["M1"]), (3, ["M1", "M2"]), (5, ["M1", "M2"])):
            sim = GatherSim(self.tuning, {"random_fish": False}, Streams(1), IdAllocator(), day=day)
            self.assertEqual([m["id"] for m in sim.monsters], expected)
        self.assertEqual(self.sim(monsters=[]).snapshot()["monsters"], [])

    def test_patrol_arrival_switches_target_for_next_step(self):
        monster = crocodile(pos=(60, 24))
        monster["pos"] = [63.99, 24]
        sim = self.sim(monsters=[monster])
        self.step(sim)
        self.assertEqual(sim.monsters[0]["pos"], [64, 24])
        self.assertEqual(sim.monsters[0]["target_idx"], 0)
        self.step(sim)
        self.assertAlmostEqual(sim.monsters[0]["pos"][0], 64 - 1 / 60)

    def test_detection_exit_and_depth_boundaries(self):
        for position, state, expected in [((30, 10), "patrol", "chase"),
                                           ((30.001, 10), "patrol", "patrol"),
                                           ((36, 10), "chase", "chase"),
                                           ((36.001, 10), "chase", "patrol")]:
            sim = self.sim({"pos": [20, 10]}, monsters=[crocodile(pos=position, state=state)])
            self.step(sim)
            self.assertEqual(sim.monsters[0]["state"], expected)
        sim = self.sim({"pos": [20, 9.999]}, monsters=[crocodile(pos=(21, 10), state="chase")])
        self.assertEqual(self.step(sim), [])
        self.assertEqual(sim.monsters[0]["state"], "patrol")

    def test_hit_boundary_half_lifo_and_only_nearest_natural_id(self):
        hold = ["ca_loc", "bong_sung", "ca_linh", "keo_neo", "ca_keo"]
        sim = self.sim({"pos": [20, 12]}, hold=hold,
                       monsters=[crocodile("M10", (21.55, 12)), crocodile("M2", (21.55, 12))])
        self.assertEqual(self.step(sim), [("monster_hit", {"monster_id": "M2", "hp": 2,
                                      "lost": ["ca_keo", "keo_neo"], "pos": [20, 12]})])
        self.assertEqual(sim.hold, hold[:3])
        self.assertEqual(sim.invuln_ticks, 90)
        by_id = {m["id"]: m for m in sim.monsters}
        self.assertEqual(by_id["M2"]["state"], "recoil")
        self.assertEqual(by_id["M10"]["state"], "chase")

    def test_nearest_monster_precedes_lower_id(self):
        sim = self.sim({"pos": [20, 12]}, monsters=[crocodile("M1", (21.5, 12)), crocodile("M2", (21, 12))])
        self.assertEqual(self.step(sim)[0][1]["monster_id"], "M2")

    def test_invulnerability_prevents_hit_and_recoil_until_exact_deadline(self):
        sim = self.sim({"pos": [20, 12], "invuln_ticks": 2}, monsters=[crocodile()])
        self.assertEqual(self.step(sim), [])
        self.assertEqual(sim.monsters[0]["state"], "chase")
        self.assertEqual(self.step(sim)[0][0], "monster_hit")
        for _ in range(89):
            self.assertNotIn("monster_hit", [name for name, _ in self.step(sim)])
        self.assertEqual(self.step(sim)[0][0], "monster_hit")

    def test_recoil_full_sixty_steps_and_coincident_direction(self):
        sim = self.sim({"pos": [20, 12]}, monsters=[crocodile()])
        self.step(sim)
        monster = sim.monsters[0]
        self.assertEqual(monster["recoil_dir"], [1, 0])
        self.assertEqual(monster["state_ticks_left"], 60)
        for _ in range(59):
            self.step(sim)
        self.assertEqual(monster["state"], "recoil")
        self.assertEqual(monster["state_ticks_left"], 1)
        self.step(sim)
        self.assertAlmostEqual(monster["pos"][0], 22)
        self.assertEqual(monster["state"], "patrol")
        self.assertIsNone(monster["recoil_dir"])
        self.step(sim)
        self.assertEqual(monster["state"], "chase")

    def test_recoil_expiry_cannot_hit_in_same_step_and_clamps_bounds(self):
        sim = self.sim({"pos": [20, 12]}, monsters=[crocodile(
            state="recoil", state_ticks_left=1, recoil_dir=[1, 0])])
        self.assertEqual(self.step(sim), [])
        self.assertEqual(sim.monsters[0]["state"], "patrol")
        self.assertEqual(self.step(sim)[0][0], "monster_hit")
        sim = self.sim(monsters=[crocodile(pos=(99.99, 30), state="recoil", state_ticks_left=2,
                                            recoil_dir=[2 ** -0.5, 2 ** -0.5])])
        self.step(sim)
        self.assertEqual(sim.monsters[0]["pos"], [100, 30])

    def test_lethal_hit_drops_half_then_faints_remaining_lifo(self):
        hold = ["ca_loc", "bong_sung", "ca_linh", "keo_neo", "ca_keo"]
        sim = self.sim({"pos": [20, 12], "hp": 1}, hold=hold, monsters=[crocodile()], time_left_ticks=1)
        rows = self.step(sim, "interact", "catch")
        self.assertEqual([name for name, _ in rows], ["monster_hit", "faint", "gather_end"])
        self.assertEqual(rows[0][1]["lost"], ["ca_keo", "keo_neo"])
        self.assertEqual(rows[1][1], {"cause": "monster", "lost": ["ca_linh", "bong_sung", "ca_loc"], "hp": 0})
        self.assertEqual(rows[-1][1], {"reason": "fainted", "inventory": {"items": {}}})
        self.assertEqual(sim.hold, [])
        self.assertEqual(self.step(sim), [])

    def test_choke_pierces_invulnerability_and_does_not_drop_hold(self):
        sim = self.sim({"pos": [20, 12], "oxygen_ticks": 0, "zero_oxy_ticks": 59,
                        "invuln_ticks": 90}, hold=["ca_loc"], monsters=[crocodile()])
        self.assertEqual(self.step(sim), [("choke", {"hp": 2})])
        self.assertEqual(sim.hold, ["ca_loc"])

    def test_choke_before_hit_and_lethal_choke_skips_monster(self):
        for hp, names in ((1, ["choke", "faint", "gather_end"]),
                          (2, ["choke", "monster_hit", "faint", "gather_end"])):
            sim = self.sim({"pos": [20, 12], "oxygen_ticks": 0, "zero_oxy_ticks": 59, "hp": hp},
                           monsters=[crocodile()])
            self.assertEqual([name for name, _ in self.step(sim)], names)

    def test_hit_precedes_docking_on_last_tick(self):
        self.g["dock_pos"] = [20, 12]
        sim = self.sim({"pos": [20, 12], "hp": 1}, monsters=[crocodile()], time_left_ticks=1)
        self.assertEqual(self.step(sim, "interact")[-1][1]["reason"], "fainted")


class P2UpgradesAndHeadless(P2Base):
    def test_new_fish_and_plant_export_inventory_to_separate_quan_process(self):
        # Dùng cá/nút mặc định để kiểm được CLI trước khi QA nâng scenario parser.
        initial = GatherSim(self.tuning, {}, Streams(42), IdAllocator())
        target = next(f for f in initial.fish if f["kind"] == "ca_keo" and f["pos"][0] < 50)
        for name, pos, button, kind, amount in [
            ("fish", target["pos"], "catch", "ca_keo", self.g["fish_yield"]["ca_keo"]),
            ("plant", self.g["nodes"][4]["pos"], "interact", "keo_neo", self.g["node_yield"]),
        ]:
            with self.subTest(case=name), Workdir() as work:
                scenario = write_json(work.path("scenario.json"), {"gather": {
                    "player": {"pos": pos}, "time_left_ticks": 1}})
                inputs = write_json(work.path("inputs.json"), frames({"tick": 0, button: True}))
                inventory, out = work.path("inventory.json"), work.path("gather.jsonl")
                code, error = run_headless("--mode", "gather", "--seed", "42", "--ticks", "1",
                                           "--scenario", scenario, "--inputs", inputs,
                                           "--out", out, "--inventory-out", inventory)
                self.assertEqual(code, 0, error)
                self.assertEqual(read_inventory(inventory), {kind: amount})
                quan = work.path("quan.jsonl")
                code, error = run_headless("--mode", "quan", "--seed", "42", "--ticks", "0",
                                           "--inventory", inventory, "--out", quan)
                self.assertEqual(code, 0, error)
                self.assertEqual(snapshots(read_jsonl(quan))[0]["stock"], {kind: amount})

    def test_active_upgrades_effective_maxima_and_new_day_reset(self):
        levels = {"oxygen": 1, "hp": 1}
        first = self.sim(active_upgrades=levels)
        self.assertEqual(first.oxygen_ticks, 2700)
        self.assertEqual(first.hp, 4)
        levels.update(oxygen=2, hp=2)
        self.assertEqual(first.snapshot()["player"]["oxygen_max_ticks"], 2700)
        self.assertEqual(first.snapshot()["player"]["hp_max"], 4)
        following = self.sim(day=2, active_upgrades=levels)
        self.assertEqual(following.oxygen_ticks, 3600)
        self.assertEqual(following.hp, 5)
        self.assertEqual(following.hold, [])

    def test_no_upgrade_standalone_remains_base_and_refill_caps_at_effective_max(self):
        base = self.sim()
        self.assertEqual((base.oxygen_max, base.hp_max), (1800, 3))
        upgraded = self.sim({"oxygen_ticks": 3599}, active_upgrades={"oxygen": 2})
        self.step(upgraded)
        self.assertEqual(upgraded.oxygen_ticks, 3600)

    def test_headless_default_seeded_replay_includes_swimming_spawn_and_monsters(self):
        with Workdir() as work:
            outputs = []
            for i in range(2):
                path = work.path(f"replay{i}.jsonl")
                code, error = run_headless("--mode", "gather", "--seed", "42", "--ticks", "720",
                                           "--snapshot-every", "120", "--out", path)
                self.assertEqual(code, 0, error)
                with open(path, "rb") as stream:
                    outputs.append(stream.read())
            self.assertEqual(outputs[0], outputs[1])
            rows = read_jsonl(work.path("replay0.jsonl"))
            self.assertEqual([r["tick"] for r in rows if r.get("name") == "fish_spawned"], [360, 720])
            self.assertEqual(len(snapshots(rows)[0]["fish"]), 8)
            self.assertEqual(len(snapshots(rows)[-1]["fish"]), 10)
            self.assertEqual(len(snapshots(rows)[-1]["monsters"]), 1)


if __name__ == "__main__":
    unittest.main()
