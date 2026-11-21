"""Minh Phase 4: v1.3 adds runner commands and retains v1.2 gameplay/schema."""

import copy
import json
from pathlib import Path
import unittest

from chonoi.contract import load_contract
from chonoi.errors import BadInput
from chonoi.inputs import InputState
from chonoi.inventory import inventory_version, read_inventory, write_inventory
from chonoi.runner import Session
from chonoi.scenario import load_scenario
from helpers import ROOT, Workdir, write_json


class ReleaseContract(unittest.TestCase):
    def setUp(self):
        self.contract = json.loads((Path(ROOT) / "game.contract.json").read_text())
        self.contract.update(contract_version="1.3", bench_cmd="python3 -m chonoi.bench",
                             soak_cmd="python3 -m chonoi.soak")

    def load(self, contract):
        with Workdir() as work:
            return load_contract(write_json(work.path("contract.json"), contract))

    def test_v13_requires_bench_and_soak_commands(self):
        loaded = self.load(self.contract)
        self.assertEqual(loaded["contract_version"], "1.3")
        self.assertEqual(loaded["tuning"]["_contract_version"], "1.2")
        for key in ("bench_cmd", "soak_cmd"):
            for invalid in (None, "", "  ", []):
                with self.subTest(key=key, value=invalid):
                    broken = copy.deepcopy(self.contract)
                    broken[key] = invalid
                    with self.assertRaises(BadInput):
                        self.load(broken)

    def test_v13_does_not_change_v12_tuning(self):
        v12 = copy.deepcopy(self.contract)
        v12["contract_version"] = "1.2"
        self.assertEqual(self.load(v12)["tuning"], self.load(self.contract)["tuning"])

    def test_v13_inventory_is_strict_individual_schema(self):
        self.assertEqual(inventory_version("1.3"), "1.2")
        items = [{"id": "I10", "kind": "ca_loc", "fresh": 29.991666666666667}]
        with Workdir() as work:
            path = work.path("inventory.json")
            write_inventory(path, items, contract_version="1.3")
            self.assertEqual(read_inventory(path, contract_version="1.3"), items)
            write_json(path, {"items": {"ca_loc": 1}})
            with self.assertRaises(BadInput):
                read_inventory(path, contract_version="1.3")

    def test_v13_scenario_uses_individual_validation(self):
        tuning = self.load(self.contract)["tuning"]
        with Workdir() as work:
            path = write_json(work.path("scenario.json"), {"gather": {
                "hold": [{"id": "I1", "kind": "ca_loc", "fresh": 30}]}})
            self.assertEqual(load_scenario(path, "gather", tuning)["hold"][0]["id"], "I1")
            write_json(path, {"gather": {"hold": ["ca_loc"]}})
            with self.assertRaises(BadInput):
                load_scenario(path, "gather", tuning)

    def test_v13_snapshots_and_events_match_v12_in_all_three_modes(self):
        v12 = copy.deepcopy(self.contract)
        v12["contract_version"] = "1.2"
        tunings = [self.load(v12)["tuning"], self.load(self.contract)["tuning"]]
        for mode in ("gather", "quan", "day"):
            with self.subTest(mode=mode):
                sessions = [Session(mode, tuning, {}, 42) for tuning in tunings]
                self.assertEqual(sessions[0].snapshot(), sessions[1].snapshot())
                for _ in range(10):
                    events = [session.step(InputState((0, 0), {}, set())) for session in sessions]
                    self.assertEqual(events[0], events[1])
                    self.assertEqual(sessions[0].snapshot(), sessions[1].snapshot())


if __name__ == "__main__":
    unittest.main()
