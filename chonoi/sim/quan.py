"""Buổi tối — Mở Quán. KHUNG: đi lại, chặn biên, đồng hồ, kho nạp từ file/scenario.

Nhóm viết tiếp (PRD-0 mục F, Quán):
  TODO(nhóm, lát 3): khách đến theo lịch, chọn món nấu được, giữ chỗ nguyên liệu, kiên nhẫn,
                     bỏ đi (customer_left), no_dish, vòng đời khách.
  TODO(nhóm, lát 4): interact tại bếp/bàn (cook_started, dish_ready, dish_picked, served),
                     ăn xong trả tiền (paid), boa, uy tín, hết ca (quan_end).
"""

import math

from ..ids import id_key, sort_by_id
from .ramp import ramp_velocity

TICK = 60.0


class QuanSim:
    mode = "quan"
    phase = "quan"

    def __init__(self, tuning, scenario, streams, ids, inventory=None):
        t = tuning["quan"]
        self.t = t
        self.menu = tuning["menu"]
        self.rng = streams
        self.ids = ids
        p = scenario.get("player", {})
        self.pos = [float(c) for c in p.get("pos", t["start_pos"])]
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        # kho: --inventory HOẶC scenario.stock (cả hai -> cli đã báo mã 2)
        self.stock = dict(inventory if inventory is not None else scenario.get("stock", {}))
        self.hand = scenario.get("hand")
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * TICK)))
        self.reputation = float(scenario.get("reputation", t["reputation_initial"]))
        self.stoves = [dict(s, state=s.get("state", "idle"), dish=s.get("dish"),
                            cook_ticks_left=s.get("cook_ticks_left", 0), ready_ticks=s.get("ready_ticks", 0))
                       for s in self._merge(t["stoves"], scenario.get("stoves", []))]
        self.tables = self._merge(t["tables"], scenario.get("tables", []))
        self.random_customers = scenario.get("random_customers", True)
        self._sim_tick = 0
        self._next_customer_tick = int(t["first_customer_tick"])

        self.customers = []
        pat_max = int(round(t["patience_s"] * TICK))
        eat_max = int(round(t["eat_s"] * TICK))
        for raw in scenario.get("customers", []):
            c = dict(raw)
            c.setdefault("state", "waiting")
            c.setdefault("patience_ticks_left", pat_max)
            c.setdefault("eat_ticks_left", eat_max if c["state"] == "eating" else 0)
            if "reserved" in c:
                c["reserved"] = dict(c["reserved"])
            elif c["state"] == "waiting" and c.get("dish_id") in self.menu:
                c["reserved"] = self._reserve_if_available(c["dish_id"])
            else:
                c["reserved"] = {}
            self.customers.append(c)
            ids.reserve(c["id"])

        self.money = 0
        self.earned = 0
        self.shift_earned = 0
        self.done = False
        self.reason = None

    def _reserve_if_available(self, dish_id: str) -> dict:
        recipe = self.menu[dish_id]["recipe"]
        if all(self.stock.get(k, 0) >= qty for k, qty in recipe.items()):
            for k, qty in recipe.items():
                self.stock[k] -= qty
            return dict(recipe)
        return {}

    def _release_reserved(self, customer: dict):
        for k, qty in customer.get("reserved", {}).items():
            self.stock[k] = self.stock.get(k, 0) + qty
        customer["reserved"] = {}

    def _clamp_reputation(self, value: float) -> float:
        return max(float(self.t["reputation_min"]), min(float(self.t["reputation_max"]), value))

    @staticmethod
    def _merge(defaults, updates):
        by_id = {d["id"]: dict(d) for d in defaults}
        for u in updates:
            if u["id"] not in by_id:
                from ..errors import BadInput
                raise BadInput(f"id bếp/bàn không tồn tại: {u['id']}")
            by_id[u["id"]].update(u)
        return sort_by_id(list(by_id.values()))

    def snapshot(self) -> dict:
        occupied = {c["table_id"]: c["id"] for c in self.customers}
        return {
            "player": {"pos": self.pos},
            "stock": {k: self.stock[k] for k in sorted(self.stock) if self.stock[k] > 0},
            "hand": self.hand,
            "stoves": [{k: s.get(k) for k in ("id", "pos", "state", "dish", "cook_ticks_left", "ready_ticks")}
                       for s in self.stoves],
            "tables": [{"id": tb["id"], "pos": tb["pos"], "customer_id": occupied.get(tb["id"])} for tb in self.tables],
            "customers": sort_by_id(self.customers),
        }

    def step(self, inp):
        events = []
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        self._sim_tick += 1

        self._step_stoves(events)
        self._step_customers(events)
        self._move(inp)

        if inp.pressed("interact"):
            self._handle_interact(events)

        if self.random_customers and self._sim_tick == self._next_customer_tick:
            self._next_customer_tick += int(round(self.t["customer_interval_s"] * TICK))
            self._spawn_customer(events)

        if self.time_left_ticks <= 0:
            self.done = True
            self.reason = "time"
            events.append(("quan_end", {"reason": "time", "money": self.money, "earned": self.earned,
                                        "shift_earned": self.shift_earned, "reputation": self.reputation}))
        return events

    def _step_stoves(self, events):
        for s in sort_by_id(self.stoves):
            if s["state"] == "cooking":
                s["cook_ticks_left"] -= 1
                if s["cook_ticks_left"] <= 0:
                    s["cook_ticks_left"] = 0
                    s["state"] = "ready"
                    events.append(("dish_ready", {"stove_id": s["id"], "dish_id": s["dish"]}))

    def _step_customers(self, events):
        pat_max = int(round(self.t["patience_s"] * TICK))
        remaining = []
        for c in sort_by_id(self.customers):
            if c["state"] == "waiting":
                c["patience_ticks_left"] -= 1
                if c["patience_ticks_left"] <= 0:
                    c["patience_ticks_left"] = 0
                    self._release_reserved(c)
                    self.reputation = self._clamp_reputation(self.reputation + self.t["left_reputation_delta"])
                    events.append(("customer_left", {"customer_id": c["id"], "table_id": c["table_id"],
                                                     "dish_id": c.get("dish_id")}))
                    continue
            elif c["state"] == "eating":
                c["eat_ticks_left"] -= 1
                if c["eat_ticks_left"] <= 0:
                    c["eat_ticks_left"] = 0
                    price = self.menu[c["dish_id"]]["price"]
                    ratio = (c["patience_ticks_left"] / pat_max) if pat_max > 0 else 0.0
                    got_tip = ratio >= self.t["tip_min_patience_ratio"]
                    tip = int(round(price * self.t["tip_rate"])) if got_tip else 0
                    total = price + tip
                    self.money += total
                    self.earned += total
                    self.shift_earned += total
                    if got_tip:
                        self.reputation = self._clamp_reputation(self.reputation + self.t["tip_reputation"])
                    events.append(("paid", {"customer_id": c["id"], "table_id": c["table_id"],
                                            "dish_id": c["dish_id"], "amount": total, "tip": tip}))
                    continue
            remaining.append(c)
        self.customers = remaining

    def _handle_interact(self, events):
        rad = float(self.t["interact_radius"])
        candidates = []
        for s in self.stoves:
            d = math.dist(self.pos, s["pos"])
            if d <= rad:
                candidates.append((d, 0, id_key(s["id"]), "stove", s))
        for tb in self.tables:
            d = math.dist(self.pos, tb["pos"])
            if d <= rad:
                candidates.append((d, 1, id_key(tb["id"]), "table", tb))
        if not candidates:
            return
        candidates.sort(key=lambda item: (item[0], item[1], item[2]))
        _, _, _, kind, obj = candidates[0]
        if kind == "stove":
            self._interact_stove(obj, events)
        else:
            self._interact_table(obj, events)

    def _interact_stove(self, stove, events):
        if stove["state"] == "ready" and self.hand is None:
            dish_id = stove["dish"]
            self.hand = dish_id
            stove["state"] = "idle"
            stove["dish"] = None
            stove["cook_ticks_left"] = 0
            stove["ready_ticks"] = 0
            events.append(("dish_picked", {"stove_id": stove["id"], "dish_id": dish_id}))
            return
        if stove["state"] == "idle":
            customer = self._next_customer_to_cook()
            if customer is None:
                return
            dish_id = customer["dish_id"]
            customer["reserved"] = {}
            stove["state"] = "cooking"
            stove["dish"] = dish_id
            stove["cook_ticks_left"] = int(round(self.menu[dish_id]["cook_s"] * TICK))
            events.append(("cook_started", {"stove_id": stove["id"], "dish_id": dish_id}))

    def _next_customer_to_cook(self):
        # Đếm số món đang có sẵn (trên bếp hoặc trên tay) để không nấu trùng
        available = {}
        if self.hand:
            available[self.hand] = available.get(self.hand, 0) + 1
        for s in self.stoves:
            if s["state"] in ("cooking", "ready") and s["dish"]:
                available[s["dish"]] = available.get(s["dish"], 0) + 1
        waiting = [c for c in sort_by_id(self.customers) if c["state"] == "waiting" and c.get("dish_id") in self.menu]
        waiting.sort(key=lambda c: (c["patience_ticks_left"], id_key(c["id"])))
        for c in waiting:
            dish_id = c["dish_id"]
            if available.get(dish_id, 0) > 0:
                available[dish_id] -= 1
            else:
                return c
        return None

    def _interact_table(self, table, events):
        if self.hand is None:
            return
        customer = next((c for c in self.customers if c["table_id"] == table["id"]), None)
        if customer is None or customer["state"] != "waiting" or customer.get("dish_id") != self.hand:
            return
        dish_id = self.hand
        self.hand = None
        customer["state"] = "eating"
        customer["eat_ticks_left"] = int(round(self.t["eat_s"] * TICK))
        customer["reserved"] = {}
        events.append(("served", {"customer_id": customer["id"], "table_id": table["id"], "dish_id": dish_id}))

    def _spawn_customer(self, events):
        occupied = {c["table_id"] for c in self.customers}
        free_tables = [tb for tb in sort_by_id(self.tables) if tb["id"] not in occupied]
        if not free_tables:
            return
        table = free_tables[0]
        affordable = [
            dish_id for dish_id in sorted(self.menu)
            if all(self.stock.get(k, 0) >= qty for k, qty in self.menu[dish_id]["recipe"].items())
        ]
        if not affordable:
            events.append(("no_dish", {"table_id": table["id"]}))
            return
        dish_id = self.rng.get("customer_order").choice(affordable)
        reserved = self._reserve_if_available(dish_id)
        cid = self.ids.new("C")
        self.customers.append({
            "id": cid,
            "table_id": table["id"],
            "dish_id": dish_id,
            "state": "waiting",
            "patience_ticks_left": int(round(self.t["patience_s"] * TICK)),
            "eat_ticks_left": 0,
            "reserved": reserved,
        })
        events.append(("customer_arrived", {"customer_id": cid, "table_id": table["id"], "dish_id": dish_id}))

    def _move(self, inp):
        speed = self.t["walk_speed"]
        mx, mz = inp.move
        self.vel = ramp_velocity(self, (mx * speed, mz * speed), int(self.t.get("ramp_max_ticks", 6)))
        b = self.t["bounds"]
        for i, axis in enumerate(("x", "z")):
            self.pos[i] += self.vel[i] / TICK
            lo, hi = b[axis]
            if self.pos[i] <= lo:
                self.pos[i], self.vel[i] = lo, max(0.0, self.vel[i])
            elif self.pos[i] >= hi:
                self.pos[i], self.vel[i] = hi, min(0.0, self.vel[i])
