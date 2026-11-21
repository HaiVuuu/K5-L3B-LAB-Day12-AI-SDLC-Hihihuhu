"""Phase 4 tests for soak_cmd (10-day continuous deterministic run)."""

import json
import os
import tempfile
import unittest

from chonoi.contract import load_contract
from chonoi.soak import main as soak_main, run_soak


class SoakPhase4Tests(unittest.TestCase):
    def test_soak_10_days_completes_with_zero_crashes_and_repeats_deterministically(self):
        tuning = load_contract("game.contract.json")["tuning"]
        r1 = run_soak(seed=7, days=10, tuning=tuning)
        r2 = run_soak(seed=7, days=10, tuning=tuning)

        self.assertEqual(r1["days"], 10)
        self.assertEqual(r1["days_completed"], 10)
        self.assertEqual(r1["crashes"], 0)
        self.assertEqual(len(r1["results"]), 10)
        self.assertEqual([x["day"] for x in r1["results"]], list(range(1, 11)))
        self.assertEqual(r1["results"], r2["results"])

    def test_soak_cli_writes_valid_json(self):
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "soak.json")
            code = soak_main(["--seed", "7", "--days", "2", "--out", out])
            self.assertEqual(code, 0)
            with open(out, encoding="utf-8") as f:
                data = json.load(f)
            self.assertEqual(set(data.keys()), {"days", "days_completed", "crashes", "results", "duration_s"})
            self.assertEqual(data["days_completed"], 2)
            self.assertEqual(data["crashes"], 0)


if __name__ == "__main__":
    unittest.main()
