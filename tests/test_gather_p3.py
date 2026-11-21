"""Minh Phase 3: kho cá thể, độ tươi chính xác, LIFO/ID và migration v1.1→v1.2.

CLI v1.2 chạy trong bản sao tạm với manifest ứng viên; không bật schema mới trên main cũ.
"""

import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import unittest
from contextlib import contextmanager
from unittest.mock import patch

from chonoi.contract import load_contract
from chonoi.errors import BadInput
from chonoi.ids import IdAllocator
from chonoi.inputs import InputState
from chonoi.inventory import (FRESH_SCALE, FreshnessTracker, fresh_units, fresh_value,
                              read_inventory, validate_instances, validate_items, write_inventory)
from chonoi.jsonl import dumps
from chonoi.rng import Streams
from chonoi.runner import Session
from chonoi.sim.gather import GatherSim
from helpers import ROOT, Workdir, read_jsonl, write_json


CANDIDATE = Path(ROOT) / "docs/contracts/game.contract.v1.2.json"


def item(ident="I1", kind="ca_loc", fresh=100):
    return {"id": ident, "kind": kind, "fresh": fresh}


def idle(*buttons):
    return InputState((0, 0), {}, set(buttons))


@contextmanager
def candidate_workspace():
    with Workdir() as work:
        root = Path(work.path("project"))
        root.mkdir()
        shutil.copytree(Path(ROOT) / "chonoi", root / "chonoi", ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copyfile(CANDIDATE, root / "game.contract.json")
        yield root


def candidate_headless(root, *arguments):
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    env.pop("PYTHONPATH", None)
    return subprocess.run([sys.executable, "-m", "chonoi.headless", *arguments],
                          cwd=root, env=env, text=True, capture_output=True)


class P3Base(unittest.TestCase):
    def setUp(self):
        self.tuning = load_contract(str(CANDIDATE))["tuning"]

    def sim(self, *, ids=None, day=1, player=None, **scenario):
        return GatherSim(self.tuning, {"player": {"pos": [20, 0], **(player or {})},
                                      "nodes": [], "fish": [], "random_fish": False,
                                      "monsters": [], **scenario}, Streams(7), ids or IdAllocator(), day=day)


class P3Inventory(P3Base):
    def test_candidate_and_staged_config_differ_only_by_version(self):
        staged = load_contract()
        candidate = load_contract(str(CANDIDATE))
        self.assertIn(staged["contract_version"], ("1.1", "1.2"))
        self.assertEqual(candidate["contract_version"], "1.2")
        self.assertEqual(candidate["tuning"]["freshness"], {
            "initial": 100, "gather_decay_per_s": 0.5, "quan_decay_per_s": 0.25, "spoiled_below": 30})
        staged["contract_version"] = "1.2"
        staged["tuning"]["_contract_version"] = "1.2"
        self.assertEqual(staged, candidate)

    def test_strict_instances_reject_bad_shape_id_kind_or_freshness(self):
        invalid = [None, {}, {"ca_loc": 1}, ["ca_loc"], [item(), item()],
                   [item(ident="")], [item(ident=1)], [item(kind="alien")],
                   [item(fresh=True)], [item(fresh="100")], [item(fresh=-0.1)], [item(fresh=100.1)],
                   [item(fresh=float("nan"))], [item(fresh=float("inf"))],
                   [{"id": "I1", "kind": "ca_loc"}], [dict(item(), extra=1)]]
        for items in invalid:
            with self.subTest(items=items), self.assertRaises(BadInput):
                validate_items(items, contract_version="1.2")

    def test_all_six_kinds_and_spoiled_stock_are_preserved(self):
        kinds = ["ca_loc", "ca_linh", "ca_keo", "keo_neo", "bong_sung", "bong_dien_dien"]
        items = [item(f"I{i}", kind, 0 if i == 1 else 29.9) for i, kind in enumerate(kinds, 1)]
        self.assertEqual(validate_instances(items), items)

    def test_version_dispatch_rejects_count_schema_for_v12(self):
        with Workdir() as work:
            counted = write_json(work.path("old.json"), {"items": {"ca_loc": 1}})
            self.assertEqual(read_inventory(counted, contract_version="1.1"), {"ca_loc": 1})
            with self.assertRaises(BadInput):
                read_inventory(counted, contract_version="1.2")
            with self.assertRaises(BadInput):
                write_inventory(work.path("bad.json"), {"ca_loc": 1}, contract_version="1.2")

    def test_file_sort_uses_natural_id_and_empty_list(self):
        with Workdir() as work:
            path = work.path("inventory.json")
            write_inventory(path, [item("I10"), item("I2", fresh=0)], contract_version="1.2")
            with open(path, encoding="utf-8") as stream:
                saved = json.load(stream)
            self.assertEqual([i["id"] for i in saved["items"]], ["I2", "I10"])
            self.assertEqual(read_inventory(path, contract_version="1.2"), saved["items"])
            write_inventory(path, [], contract_version="1.2")
            with open(path, encoding="utf-8") as stream:
                self.assertEqual(json.load(stream), {"items": []})

    def test_reader_rejects_extra_root_key_duplicate_id_and_nonfinite(self):
        with Workdir() as work:
            for value in ({"items": [], "x": 1}, {"items": [item(), item()]},
                          {"items": [item(fresh=float("nan"))]}):
                path = write_json(work.path("bad.json"), value)
                with self.assertRaises(BadInput):
                    read_inventory(path, contract_version="1.2")

    def test_atomic_failure_preserves_existing_file_and_removes_temporary(self):
        with Workdir() as work:
            path = Path(work.path("inventory.json"))
            path.write_bytes(b"previous contents\n")
            with patch("chonoi.inventory.os.replace", side_effect=OSError("replace failed")):
                with self.assertRaises(OSError):
                    write_inventory(str(path), [item()], contract_version="1.2")
            self.assertEqual(path.read_bytes(), b"previous contents\n")
            self.assertEqual(list(path.parent.glob(".inv-*.tmp")), [])

    def test_default_v12_reader_cli_returns_2_before_output_for_old_inventory(self):
        with candidate_workspace() as root:
            inventory = root / "old.json"
            inventory.write_text('{"items":{"ca_loc":1}}')
            out = root / "out.jsonl"
            result = candidate_headless(root, "--mode", "quan", "--seed", "1", "--ticks", "0",
                                         "--inventory", str(inventory), "--out", str(out))
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertFalse(out.exists())


class P3Freshness(P3Base):
    def test_fresh_30_crosses_on_first_tick_and_emits_once(self):
        sim = self.sim(hold=[item(fresh=30)])
        self.assertEqual(sim.step(idle()), [("spoiled", {"item_id": "I1", "kind": "ca_loc", "location": "hold"})])
        self.assertLess(sim.hold[0]["fresh"], 30)
        self.assertAlmostEqual(sim.hold[0]["fresh"], 30 - 0.5 / 60)
        self.assertEqual(sim.step(idle()), [])

    def test_session_emits_spoiled_at_tick_one_with_exact_envelope(self):
        session = Session("gather", self.tuning, {"hold": [item(kind="ca_linh", fresh=30)],
                                                  "random_fish": False}, 1)
        self.assertEqual(session.step(idle()), [{"type": "event", "tick": 1, "phase": "gather",
            "name": "spoiled", "data": {"item_id": "I1", "kind": "ca_linh", "location": "hold"}}])

    def test_freshness_uses_exact_units_at_tick_120_and_121(self):
        sim = self.sim(hold=[item(fresh=31)])
        for _ in range(120):
            self.assertEqual(sim.step(idle()), [])
        self.assertEqual(sim.hold[0]["fresh"], 30)
        self.assertEqual(sim._freshness.units["I1"], 30 * FRESH_SCALE)
        self.assertEqual(sim.step(idle())[0][0], "spoiled")

    def test_freshness_zero_clamps_and_already_spoiled_does_not_emit(self):
        sim = self.sim(hold=[item("I1", fresh=0), item("I2", fresh=0.001), item("I3", fresh=29)])
        self.assertEqual(sim.step(idle()), [])
        self.assertEqual(sim.hold[0]["fresh"], 0)
        self.assertEqual(sim.hold[1]["fresh"], 0)

    def test_spoiled_sorted_by_id_not_lifo_or_insertion_order(self):
        sim = self.sim(hold=[item("I10", fresh=30), item("I2", fresh=30), item("I1", fresh=30)])
        rows = sim.step(idle())
        self.assertEqual([data["item_id"] for _, data in rows], ["I1", "I2", "I10"])
        self.assertEqual([i["id"] for i in sim.hold], ["I10", "I2", "I1"])

    def test_new_harvest_is_100_until_next_step_and_ids_continue_after_fixture(self):
        original = [item("I10")]
        sim = self.sim(hold=original, nodes=[{"id": "N1", "kind": "bong_sung", "pos": [20, 0]}])
        self.assertEqual(sim.step(idle("interact"))[0][0], "gather")
        self.assertEqual(sim.hold[-1], item("I11", "bong_sung"))
        self.assertLess(sim.hold[0]["fresh"], 100)
        self.assertEqual(original[0]["fresh"], 100, "fixture đầu vào không bị sửa")
        sim.step(idle())
        self.assertLess(sim.hold[-1]["fresh"], 100)

    def test_catch_allocates_one_item_per_yield_in_order(self):
        sim = self.sim(player={"pos": [20, 5]}, fish=[{"id": "F1", "kind": "ca_linh", "pos": [20, 5]}])
        self.assertEqual(sim.step(idle("catch"))[0][0], "fish_caught")
        self.assertEqual(sim.hold, [item(f"I{i}", "ca_linh") for i in range(1, 4)])

    def test_full_hold_does_not_allocate_item_ids(self):
        capacity = self.tuning["gather"]["hold_capacity"]
        sim = self.sim(hold=[item(f"I{i}") for i in range(1, capacity + 1)],
                       nodes=[{"id": "N1", "kind": "bong_sung", "pos": [20, 0]}])
        self.assertEqual(sim.step(idle("interact"))[0][0], "hold_full")
        self.assertEqual(sim.ids.new("I"), f"I{capacity + 1}")

    def test_same_allocator_prevents_reuse_after_loss_and_remaps_next_day_template(self):
        allocator = IdAllocator()
        template = [item("I10", "ca_loc", 97.5), item("I2", "bong_sung", 30)]
        first = self.sim(ids=allocator, hold=template)
        first.hold.clear()  # Vật đã dùng/bỏ không trả lại ID.
        next_day = self.sim(ids=allocator, day=2, hold=template)
        self.assertEqual(next_day.hold, [item("I11", "ca_loc", 97.5), item("I12", "bong_sung", 30)])
        self.assertEqual(template, [item("I10", "ca_loc", 97.5), item("I2", "bong_sung", 30)])
        self.assertEqual(next_day.ids.new("I"), "I13")

    def test_snapshot_hold_is_detached_and_inventory_is_sorted(self):
        sim = self.sim(hold=[item("I10"), item("I2")])
        before = sim.snapshot()
        sim.step(idle())
        self.assertEqual(before["hold"][0]["fresh"], 100)
        self.assertEqual([i["id"] for i in sim.inventory_items()], ["I2", "I10"])
        exported = sim.inventory_items()
        exported[0]["fresh"] = 0
        self.assertGreater(sim.hold[1]["fresh"], 0)

    def test_monster_hit_then_faint_losses_are_individuals_lifo_after_decay(self):
        sim = self.sim(player={"pos": [20, 12], "hp": 1},
                       hold=[item(f"I{i}", fresh=30) for i in range(1, 6)],
                       monsters=[{"id": "M1", "kind": "ca_sau", "pos": [20, 12],
                                  "waypoints": [[20, 12], [24, 12]]}])
        rows = sim.step(idle())
        self.assertEqual([name for name, _ in rows], ["spoiled"] * 5 + ["monster_hit", "faint", "gather_end"])
        hit, faint = rows[-3][1], rows[-2][1]
        self.assertEqual([i["id"] for i in hit["lost"]], ["I5", "I4"])
        self.assertEqual([i["id"] for i in faint["lost"]], ["I3", "I2", "I1"])
        self.assertTrue(all(i["fresh"] < 30 for i in hit["lost"] + faint["lost"]))
        self.assertEqual(rows[-1][1], {"reason": "fainted", "inventory": {"items": []}})

    def test_choke_faint_after_spoil_keeps_lifo_and_empty_inventory(self):
        sim = self.sim(player={"pos": [20, 5], "oxygen_ticks": 0, "zero_oxy_ticks": 59, "hp": 1},
                       hold=[item("I10", fresh=30), item("I2", fresh=30)])
        rows = sim.step(idle())
        self.assertEqual([name for name, _ in rows], ["spoiled", "spoiled", "choke", "faint", "gather_end"])
        self.assertEqual([i["id"] for i in rows[-2][1]["lost"]], ["I2", "I10"])
        self.assertEqual(rows[-1][1]["inventory"], {"items": []})

    def test_regrowth_precedes_spoiling_and_spoiling_precedes_docking(self):
        sim = self.sim(player={"pos": [2, 0]}, hold=[item(fresh=30)], time_left_ticks=1,
                       nodes=[{"id": "N1", "kind": "bong_sung", "pos": [20, 0], "regrow_ticks": 1}])
        rows = sim.step(idle("interact"))
        self.assertEqual([name for name, _ in rows], ["node_regrown", "spoiled", "gather_end"])
        self.assertEqual(rows[-1][1]["reason"], "docked")
        self.assertLess(rows[-1][1]["inventory"]["items"][0]["fresh"], 30)

    def test_pause_stops_freshness_and_resume_decays_once(self):
        session = Session("gather", self.tuning, {"hold": [item(fresh=30)], "random_fish": False}, 1)
        session.step(idle("pause"))
        session.step(idle())
        self.assertEqual(session.sim.hold[0]["fresh"], 30)
        rows = session.step(idle("pause"))
        self.assertEqual([r["name"] for r in rows], ["resumed", "spoiled"])
        self.assertEqual(session.sim_tick, 1)


class P3PrecisionAndCLI(P3Base):
    def test_jsonl_preserves_freshness_precision_while_rounding_positions(self):
        fresh = fresh_value(fresh_units(100) - 2, 30)
        result = json.loads(dumps({"pos": [1.234567, -0.00001], "inventory": {"items": [item(fresh=fresh)]}}))
        self.assertEqual(result["pos"], [1.235, 0])
        self.assertEqual(result["inventory"]["items"][0]["fresh"], fresh)

    def test_inventory_file_equals_gather_end_after_existing_item_decays(self):
        sim = self.sim(player={"pos": [2, 0]}, hold=[item("I10"), item("I2", fresh=97.5)])
        end = sim.step(idle("interact"))[-1][1]["inventory"]
        with Workdir() as work:
            path = work.path("items.json")
            write_inventory(path, sim.inventory_items(), contract_version="1.2")
            with open(path, encoding="utf-8") as stream:
                saved = json.load(stream)
            self.assertEqual(saved, json.loads(dumps(end)))
            self.assertEqual(read_inventory(path, contract_version="1.2"), end["items"])

    def test_roundtrip_one_quantum_above_30_does_not_spoil_early(self):
        stock = [item(fresh=fresh_value(30 * FRESH_SCALE + 1, 30))]
        with Workdir() as work:
            path = work.path("items.json")
            write_inventory(path, stock, contract_version="1.2")
            restored = read_inventory(path, contract_version="1.2")
        tracker = FreshnessTracker(self.tuning)
        self.assertEqual(tracker.decay(restored, location="stock", rate=0.25), [])
        self.assertGreaterEqual(restored[0]["fresh"], 30)
        self.assertEqual(tracker.decay(restored, location="stock", rate=0.25), [
            ("spoiled", {"item_id": "I1", "kind": "ca_loc", "location": "stock"})])

    def test_non_grid_fixture_keeps_side_of_threshold_and_is_not_quantized(self):
        below = math.nextafter(30, -math.inf)
        self.assertLess(fresh_value(fresh_units(below), 30), 30)
        sim = self.sim(hold=[item(fresh=30.000001)])
        self.assertEqual(sim.step(idle())[0][0], "spoiled")
        self.assertAlmostEqual(sim.hold[0]["fresh"], 30.000001 - 0.5 / 60, places=12)

    def test_same_tick_handoff_does_not_decay_again_until_next_step(self):
        sim = self.sim(player={"pos": [2, 0]}, hold=[item(fresh=30)])
        result = sim.step(idle("interact"))[-1][1]["inventory"]["items"]
        stock = validate_instances(result)
        self.assertEqual(stock, result)
        tracker = FreshnessTracker(self.tuning)
        # Vào pha không gọi decay. Bước quán sau chỉ hao 1 đơn vị và không spoiled lần hai.
        self.assertEqual(tracker.decay(stock, location="stock", rate=0.25), [])
        self.assertAlmostEqual(stock[0]["fresh"], result[0]["fresh"] - 0.25 / 60)

    def test_candidate_headless_harvest_exports_individual_inventory_deterministically(self):
        with candidate_workspace() as root:
            scenario = root / "scenario.json"
            scenario.write_text(json.dumps({"gather": {"player": {"pos": [44, 0]}, "time_left_ticks": 1}}))
            inputs = root / "inputs.json"
            inputs.write_text('{"frames":[{"tick":0,"interact":true}]}')
            runs = []
            for i in range(2):
                out, inventory = root / f"out{i}.jsonl", root / f"inv{i}.json"
                result = candidate_headless(root, "--mode", "gather", "--seed", "42", "--ticks", "1",
                                             "--scenario", str(scenario), "--inputs", str(inputs),
                                             "--out", str(out), "--inventory-out", str(inventory))
                self.assertEqual(result.returncode, 0, result.stderr)
                runs.append((out.read_bytes(), inventory.read_bytes()))
                end = next(row for row in read_jsonl(str(out)) if row.get("name") == "gather_end")
                self.assertEqual(end["data"]["inventory"], json.loads(inventory.read_bytes()))
                self.assertEqual(end["data"]["inventory"]["items"], [item(kind="bong_sung")])
            self.assertEqual(runs[0], runs[1])

    def test_candidate_tick_limit_preserves_existing_inventory_bytes(self):
        with candidate_workspace() as root:
            inventory = root / "inventory.json"
            inventory.write_bytes(b"do not overwrite\n")
            result = candidate_headless(root, "--mode", "gather", "--seed", "1", "--ticks", "1",
                                         "--inventory-out", str(inventory), "--out", str(root / "out.jsonl"))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(inventory.read_bytes(), b"do not overwrite\n")

    def test_candidate_faint_writes_empty_array_and_stops_once(self):
        with candidate_workspace() as root:
            inventory, out = root / "inventory.json", root / "out.jsonl"
            inventory.write_text('{"items":[{"id":"I99","kind":"ca_loc","fresh":100}]}')
            scenario = root / "scenario.json"
            scenario.write_text(json.dumps({"gather": {"player": {
                "pos": [20, 5], "hp": 1, "oxygen_ticks": 0, "zero_oxy_ticks": 59}, "random_fish": False}}))
            result = candidate_headless(root, "--mode", "gather", "--seed", "1", "--ticks", "600",
                                         "--scenario", str(scenario), "--inventory-out", str(inventory), "--out", str(out))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(inventory.read_bytes()), {"items": []})
            rows = read_jsonl(str(out))
            self.assertEqual(sum(r.get("name") == "gather_end" for r in rows), 1)
            self.assertEqual(rows[-1]["ticks"], 1)
            self.assertEqual(rows[-1]["reason"], "fainted")


if __name__ == "__main__":
    unittest.main()
