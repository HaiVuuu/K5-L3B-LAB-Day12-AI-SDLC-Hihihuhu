"""Lệnh nhóm: replay hai lần, so byte và thử bàn giao kho qua tiến trình quan."""

import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[1]


def main():
    contract = json.loads((ROOT / "game.contract.json").read_text(encoding="utf-8"))
    command = shlex.split(contract["headless_cmd"])
    fixture = json.loads((ROOT / "tests/fixtures/gather-replay.json").read_text(encoding="utf-8"))
    for case in fixture:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            scenario, inputs = work / "scenario.json", work / "inputs.json"
            scenario.write_text(json.dumps({"gather": case["scenario"]}), encoding="utf-8")
            inputs.write_text(json.dumps({"frames": case["frames"]}), encoding="utf-8")
            replays = []
            for attempt in range(2):
                out, inventory = work / f"g{attempt}.jsonl", work / f"inv{attempt}.json"
                subprocess.run([*command, "--mode", "gather", "--seed", "42", "--ticks", "600",
                                "--scenario", str(scenario), "--inputs", str(inputs),
                                "--out", str(out), "--inventory-out", str(inventory)], cwd=ROOT, check=True)
                replays.append((out.read_bytes(), inventory.read_bytes()))
            if replays[0] != replays[1]:
                raise RuntimeError(f"{case['name']}: replay khác byte")
            rows = [json.loads(line) for line in replays[0][0].splitlines()]
            saved = json.loads(replays[0][1])
            end_events = [r for r in rows if r.get("name") == "gather_end"]
            if len(end_events) != 1 or end_events[0]["data"]["inventory"] != saved:
                raise RuntimeError(f"{case['name']}: kho không khớp gather_end")
            if saved != case["inventory"] or rows[-1]["reason"] != case["reason"]:
                raise RuntimeError(f"{case['name']}: sai kho hoặc lý do kết thúc")
            quan = work / "quan.jsonl"
            subprocess.run([*command, "--mode", "quan", "--seed", "42", "--ticks", "0",
                            "--inventory", str(work / "inv0.json"), "--out", str(quan)], cwd=ROOT, check=True)
            stock = json.loads(quan.read_text(encoding="utf-8").splitlines()[0])["stock"]
            if stock != saved["items"]:
                raise RuntimeError(f"{case['name']}: quán đọc sai kho")
            print(json.dumps({"case": case["name"], "result": "PASS", "reason": rows[-1]["reason"],
                              "events": [r["name"] for r in rows if r["type"] == "event"],
                              "inventory": saved, "quan_stock": stock,
                              "jsonl_sha256": hashlib.sha256(replays[0][0]).hexdigest(),
                              "inventory_sha256": hashlib.sha256(replays[0][1]).hexdigest()}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
