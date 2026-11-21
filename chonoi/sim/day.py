"""Vòng ngày và Shop (Phase 2 — TICKET-02).

Chu trình một ngày:
  day_start -> day_plan -> phase_start(gather)
  -> gather_end -> phase_start(quan)
  -> quan_end -> phase_start(shop)
  -> shop_end -> ngày kế hoặc kết thúc (days_complete).
"""

import copy

from ..ids import IdAllocator
from .gather import GatherSim
from .quan import QuanSim


class ShopSim:
    mode = "day"
    phase = "shop"

    def __init__(self, tuning, stock, money, earned, reputation, upgrades):
        shop_cfg = tuning.get("shop", {})
        self.upgrades_cfg = shop_cfg.get("upgrades", {})
        self.time_left_ticks = int(shop_cfg.get("max_ticks", 600))
        self.stock = list(stock) if isinstance(stock, list) else dict(stock)
        self.money = money
        self.earned = earned
        self.reputation = reputation
        self.upgrades = dict(upgrades)
        self.done = False
        self.reason = None

    def snapshot(self) -> dict:
        if isinstance(self.stock, list):
            stock_view = list(self.stock)
        else:
            stock_view = {k: self.stock[k] for k in sorted(self.stock) if self.stock[k] > 0}
        return {
            "stock": stock_view,
            "time_left_ticks": self.time_left_ticks,
        }

    def step(self, inp):
        events = []
        self.time_left_ticks = max(0, self.time_left_ticks - 1)

        if getattr(inp, "buy", None):
            self._handle_buy(inp.buy, events)

        if inp.pressed("shop_done"):
            self.done = True
            self.reason = "done"
            events.append(("shop_end", {"reason": "done"}))
            return events

        if self.time_left_ticks <= 0:
            self.done = True
            self.reason = "time"
            events.append(("shop_end", {"reason": "time"}))
        return events

    def _handle_buy(self, action: str, events):
        if action not in self.upgrades_cfg:
            events.append(("buy_failed", {"action": action, "reason": "unknown"}))
            return
        levels = self.upgrades_cfg[action]
        cur = self.upgrades.get(action, 0)
        nxt = next((lv for lv in levels if lv["level"] == cur + 1), None)
        if nxt is None:
            events.append(("buy_failed", {"action": action, "reason": "max_level"}))
            return
        price = nxt["price"]
        if self.money < price:
            events.append(("buy_failed", {"action": action, "reason": "funds"}))
            return
        self.money -= price
        self.upgrades[action] = nxt["level"]
        events.append(("bought", {"upgrade": action, "level": nxt["level"], "price": price, "money": self.money}))


class DaySession:
    """Quản lý vòng nhiều ngày: gather -> quan -> shop."""

    mode = "day"

    def __init__(self, tuning, scenario, streams, days=1):
        self.base_tuning = tuning
        self.scenario = scenario or {}
        self.streams = streams
        self.target_days = days
        self.days_completed = 0

        day_cfg = self.scenario.get("day", {})
        self.money = day_cfg.get("money", 0)
        self.earned = day_cfg.get("earned", 0)
        self.reputation = float(day_cfg.get("reputation", tuning["quan"]["reputation_initial"]))
        self.upgrades = dict(day_cfg.get("upgrades", {}))
        self.active_upgrades = dict(self.upgrades)

        self.day = 1
        self.phase = "gather"
        self.phase_tick = 0
        self.done = False
        self.reason = None
        self._pending_initial_events = []
        self.item_ids = IdAllocator()

        self.sim = self._build_gather()
        self._queue_day_start_events()

    @property
    def time_left_ticks(self):
        return self.sim.time_left_ticks

    def _plan_for_day(self, day_num: int) -> dict:
        override = self.scenario.get("day", {}).get("day_plan", {})
        if str(day_num) in override:
            plan = override[str(day_num)]
        elif day_num in override:
            plan = override[day_num]
        else:
            plans = self.base_tuning.get("day_plan", [])
            wrapped = ((day_num - 1) % len(plans)) + 1 if plans else day_num
            plan = next((p for p in plans if p["day"] == day_num), None)
            if plan is None:
                plan = next((p for p in plans if p["day"] == wrapped), {"day": day_num, "dishes": {}, "ingredients": {}})
        dishes = dict(plan.get("dishes", {}))
        if "ingredients" in plan:
            ingredients = dict(plan["ingredients"])
        else:
            ingredients = {}
            for dish_id, count in dishes.items():
                for k, qty in self.base_tuning["menu"][dish_id]["recipe"].items():
                    ingredients[k] = ingredients.get(k, 0) + qty * count
        return {"dishes": dishes, "ingredients": ingredients}

    def _tuned_for_active_upgrades(self):
        t = copy.deepcopy(self.base_tuning)
        shop_up = t.get("shop", {}).get("upgrades", {})
        ox_lv = self.active_upgrades.get("oxygen", 0)
        if ox_lv > 0:
            entry = next((lv for lv in shop_up.get("oxygen", []) if lv["level"] == ox_lv), None)
            if entry:
                t["gather"]["oxygen_max_s"] = entry["oxygen_max_s"]
        hp_lv = self.active_upgrades.get("hp", 0)
        if hp_lv > 0:
            entry = next((lv for lv in shop_up.get("hp", []) if lv["level"] == hp_lv), None)
            if entry:
                t["gather"]["hp_max"] = entry["hp_max"]
        return t

    def _build_gather(self):
        tuning = self._tuned_for_active_upgrades()
        g_sc = self.scenario.get("gather", {}) if self.day == 1 else {}
        sim = GatherSim(tuning, g_sc, self.streams, IdAllocator())
        sim.money = self.money
        sim.earned = self.earned
        sim.reputation = self.reputation
        return sim

    def _build_quan(self, inventory):
        q_sc = self.scenario.get("quan", {}) if self.day == 1 else {}
        plan = self._plan_for_day(self.day)
        allowed = set(plan["dishes"].keys()) if plan["dishes"] else None
        return QuanSim(
            self.base_tuning,
            q_sc,
            self.streams,
            IdAllocator(),
            inventory=inventory,
            allowed_dishes=allowed,
            money=self.money,
            earned=self.earned,
            reputation=self.reputation,
        )

    def _stock_for_shop(self):
        if getattr(self.sim, "v12", False):
            return [{"id": it["id"], "kind": it["kind"], "fresh": round(it["fresh"], 3)}
                    for it in sorted(self.sim.stock_items, key=lambda x: x["id"])]
        return {k: v for k, v in self.sim.stock.items() if v > 0}

    def _queue_day_start_events(self):
        plan = self._plan_for_day(self.day)
        self._pending_initial_events.extend([
            ("day_start", {}, "gather", self.day),
            ("day_plan", plan, "gather", self.day),
            ("phase_start", {}, "gather", self.day),
        ])

    def pop_initial_events(self):
        evs, self._pending_initial_events = self._pending_initial_events, []
        return evs

    def snapshot(self) -> dict:
        s = self.sim.snapshot()
        s.update({
            "day": self.day,
            "day_plan": self._plan_for_day(self.day),
            "upgrades": dict(self.upgrades),
            "active_upgrades": dict(self.active_upgrades),
        })
        return s

    def step(self, inp):
        raw_events = self.sim.step(inp)
        self.phase_tick += 1
        cur_phase = self.phase
        cur_day = self.day
        tagged = [(name, data, cur_phase, cur_day) for name, data in raw_events]

        self.money = self.sim.money
        self.earned = self.sim.earned
        self.reputation = self.sim.reputation

        if self.sim.done:
            if cur_phase == "gather":
                inv = self.sim.inventory_items()
                if isinstance(inv, dict) and isinstance(inv.get("items"), list):
                    inv = inv["items"]
                elif self.base_tuning.get("v12_enabled", False) and isinstance(inv, dict):
                    inv = [
                        {"id": self.item_ids.new("I"), "kind": k, "fresh": 100.0}
                        for k in sorted(inv) for _ in range(inv[k])
                    ]
                self.phase = "quan"
                self.phase_tick = 0
                self.sim = self._build_quan(inv)
                tagged.append(("phase_start", {}, "quan", cur_day))
            elif cur_phase == "quan":
                stock = self._stock_for_shop()
                self.phase = "shop"
                self.phase_tick = 0
                self.sim = ShopSim(self.base_tuning, stock, self.money, self.earned, self.reputation, self.upgrades)
                tagged.append(("phase_start", {}, "shop", cur_day))
            elif cur_phase == "shop":
                self.upgrades = dict(self.sim.upgrades)
                self.days_completed += 1
                if self.days_completed >= self.target_days:
                    self.done = True
                    self.reason = "days_complete"
                else:
                    self.day += 1
                    self.active_upgrades = dict(self.upgrades)
                    self.phase = "gather"
                    self.phase_tick = 0
                    self.sim = self._build_gather()
                    plan = self._plan_for_day(self.day)
                    tagged.append(("day_start", {}, "gather", self.day))
                    tagged.append(("day_plan", plan, "gather", self.day))
                    tagged.append(("phase_start", {}, "gather", self.day))
        return tagged
