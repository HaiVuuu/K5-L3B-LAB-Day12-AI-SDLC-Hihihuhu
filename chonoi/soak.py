"""Soak headless runner (Phase 4 — TICKET-04):
    python3 -m chonoi.soak --seed 7 --days 10 --out soak.json
"""

import argparse
import json
import sys
import time

from .contract import load_contract
from .errors import BadInput
from .inputs import InputState
from .runner import Session


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage(sys.stderr)
        sys.stderr.write(f"lỗi: {message}\n")
        sys.exit(2)


def _int(name):
    def conv(s):
        try:
            return int(s)
        except ValueError:
            raise argparse.ArgumentTypeError(f"{name} phải là số nguyên")
    return conv


def _bot_input(sess: Session) -> InputState:
    """Bot tất định: ở gather cập bến, ở shop mua nâng cấp nếu đủ tiền rồi đóng."""
    phase = sess.sim.phase
    if phase == "gather":
        # Út Sen xuất phát trong bán kính bến -> interact để bàn giao nhanh
        return InputState((0.0, 0.0), {"interact"}, {"interact"})
    if phase == "shop":
        shop = sess.sim.sim
        buy_action = None
        for key in ("oxygen", "hp"):
            levels = shop.upgrades_cfg.get(key, [])
            cur = shop.upgrades.get(key, 0)
            nxt = next((lv for lv in levels if lv["level"] == cur + 1), None)
            if nxt and shop.money >= nxt["price"]:
                buy_action = key
                break
        return InputState((0.0, 0.0), {"shop_done"}, {"shop_done"}, buy=buy_action)
    return InputState((0.0, 0.0), set(), set())


def run_soak(seed: int, days: int, tuning: dict) -> dict:
    t0 = time.perf_counter()
    crashes = 0
    results = []
    sess = Session("day", tuning, {}, seed, days=days)
    sess.initial_events()
    max_ticks = days * 25000

    try:
        while not sess.done and sess.tick < max_ticks:
            inp = _bot_input(sess)
            evs = sess.step(inp)
            for ev in evs:
                if ev["name"] == "shop_end":
                    snap = sess.snapshot()
                    results.append({
                        "day": ev["day"],
                        "earned": snap["earned"],
                        "reputation": snap["reputation"],
                        "score": snap["score"],
                    })
    except Exception:
        crashes += 1

    duration_s = round(time.perf_counter() - t0, 3)
    return {
        "days": days,
        "days_completed": sess.sim.days_completed,
        "crashes": crashes,
        "results": results,
        "duration_s": duration_s,
    }


def main(argv=None) -> int:
    p = _Parser(prog="chonoi.soak")
    p.add_argument("--seed", required=True, type=_int("seed"))
    p.add_argument("--days", required=True, type=_int("days"))
    p.add_argument("--out", required=True)
    a = p.parse_args(argv)
    if a.days < 1:
        sys.stderr.write("đầu vào sai: --days phải >= 1\n")
        return 2
    try:
        tuning = load_contract()["tuning"]
        report = run_soak(a.seed, a.days, tuning)
        with open(a.out, "w", encoding="utf-8", newline="\n") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
            f.write("\n")
    except BadInput as e:
        sys.stderr.write(f"đầu vào sai: {e}\n")
        return 2
    except OSError as e:
        sys.stderr.write(f"lỗi ghi: {e}\n")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
