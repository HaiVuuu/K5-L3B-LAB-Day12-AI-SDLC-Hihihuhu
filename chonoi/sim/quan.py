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

    def __init__(self, tuning, scenario, streams, ids, inventory=None,
                 allowed_dishes=None, money=0, earned=0, reputation=None):
        t = tuning["quan"]
        self.t = t
        self.menu = tuning["menu"]
        self.allowed_dishes = set(allowed_dishes) if allowed_dishes is not None else None
        self.rng = streams
        self.ids = ids
        self.fresh_cfg = tuning.get("freshness")
        has_raw_stock = inventory is not None or "stock" in scenario
        raw_stock = inventory if inventory is not None else scenario.get("stock", {})
        self.v12 = bool(self.fresh_cfg) and (
            isinstance(raw_stock, list)
            or (not has_raw_stock and tuning.get("v12_enabled", False))
        )
        p = scenario.get("player", {})
        self.pos = [float(c) for c in p.get("pos", t["start_pos"])]
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0

        self._init_stock(raw_stock)

        self.hand = scenario.get("hand")
        self.hand_price = scenario.get("hand_price")
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * TICK)))
        rep_default = t["reputation_initial"] if reputation is None else reputation
        self.reputation = float(scenario.get("reputation", rep_default))
        self.stoves = [dict(s, state=s.get("state", "idle"), dish=s.get("dish"),
                            cook_ticks_left=s.get("cook_ticks_left", 0), ready_ticks=s.get("ready_ticks", 0),
                            base_price=s.get("base_price"))
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
            c.setdefault("order_tick", 0)
            c.setdefault("patience_ticks_left", pat_max)
            c.setdefault("eat_ticks_left", eat_max if c["state"] == "eating" else 0)
            if self.v12:
                if "reserved" in c:
                    c["reserved"] = list(c["reserved"])
                elif c["state"] == "waiting" and c.get("dish_id") in self.menu:
                    c["reserved"] = self._reserve_v12(c["dish_id"])
                else:
                    c["reserved"] = []
            else:
                if "reserved" in c:
                    c["reserved"] = dict(c["reserved"])
                elif c["state"] == "waiting" and c.get("dish_id") in self.menu:
                    c["reserved"] = self._reserve_if_available(c["dish_id"])
                else:
                    c["reserved"] = {}
            self.customers.append(c)
            ids.reserve(c["id"])

        self.money = money
        self.earned = earned
        self.shift_earned = 0
        self.done = False
        self.reason = None

    def _init_stock(self, raw_stock):
        if self.v12:
            self.stock = {}
            self.stock_items = []
            items = raw_stock if isinstance(raw_stock, list) else []
            for it in items:
                fresh = float(it.get("fresh", 100.0))
                self.stock_items.append({
                    "id": it["id"],
                    "kind": it["kind"],
                    "fresh": fresh,
                    "units": fresh * 240.0,
                })
        else:
            self.stock_items = []
            self.stock = dict(raw_stock) if isinstance(raw_stock, dict) else {}

    def _reserved_ids(self) -> set:
        used = set()
        for c in self.customers:
            if isinstance(c.get("reserved"), list):
                used.update(c["reserved"])
        return used

    def _spoiled_units(self) -> float:
        return float(self.fresh_cfg["spoiled_below"]) * 240.0

    def _reserve_v12(self, dish_id: str) -> list:
        recipe = self.menu[dish_id]["recipe"]
        used_ids = self._reserved_ids()
        sp_units = self._spoiled_units()
        picked = []
        for kind in sorted(recipe):
            need = recipe[kind]
            avail = [
                it for it in self.stock_items
                if it["kind"] == kind and it["id"] not in used_ids and it["units"] >= sp_units
            ]
            avail.sort(key=lambda it: (-it["units"], id_key(it["id"])))
            if len(avail) < need:
                return []
            chosen = avail[:need]
            for it in chosen:
                used_ids.add(it["id"])
                picked.append(it["id"])
        return sorted(picked, key=id_key)

    def _reserve_if_available(self, dish_id: str) -> dict:
        recipe = self.menu[dish_id]["recipe"]
        if all(self.stock.get(k, 0) >= qty for k, qty in recipe.items()):
            for k, qty in recipe.items():
                self.stock[k] -= qty
            return dict(recipe)
        return {}

    def _release_reserved(self, customer: dict):
        if self.v12:
            customer["reserved"] = []
            return
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
        if self.v12:
            stock_view = [
                {"id": it["id"], "kind": it["kind"], "fresh": round(it["fresh"], 3)}
                for it in sort_by_id(self.stock_items)
            ]
        else:
            stock_view = {k: self.stock[k] for k in sorted(self.stock) if self.stock[k] > 0}
        return {
            "player": {"pos": self.pos},
            "stock": stock_view,
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

        if self.v12:
            self._step_freshness(events)
        self._step_stoves(events)
        self._step_customers(events)
        self._move(inp)

        if inp.pressed("interact"):
            self._handle_interact(events)

        if self.random_customers and self._sim_tick == self._next_customer_tick:
            self._next_customer_tick += int(round(self.t["customer_interval_s"] * TICK))
            self._spawn_customer(events)

        if self.time_left_ticks <= 0:
            self._close_shift(events)
            self.done = True
            self.reason = "time"
            events.append(("quan_end", {"reason": "time", "money": self.money, "earned": self.earned,
                                        "shift_earned": self.shift_earned, "reputation": self.reputation}))
        return events

    def _step_freshness(self, events):
        decay_units = float(self.fresh_cfg["quan_decay_per_s"]) * 240.0 / TICK
        sp_units = self._spoiled_units()
        newly_spoiled = set()
        for it in sort_by_id(self.stock_items):
            was_ok = it["units"] >= sp_units
            it["units"] = max(0.0, it["units"] - decay_units)
            it["fresh"] = it["units"] / 240.0
            if was_ok and it["units"] < sp_units:
                newly_spoiled.add(it["id"])
                events.append(("spoiled", {"item_id": it["id"], "kind": it["kind"], "location": "stock"}))

        if not newly_spoiled:
            return
        affected = [
            c for c in self.customers
            if c["state"] == "waiting" and any(iid in newly_spoiled for iid in c.get("reserved", []))
        ]
        affected.sort(key=lambda c: (c.get("order_tick", 0), id_key(c["table_id"])))
        for c in affected:
            c["reserved"] = []
            new_res = self._reserve_v12(c["dish_id"])
            if new_res:
                c["reserved"] = new_res
            else:
                c["unfulfillable"] = True

    def _pay_customer(self, c, pat_max, events):
        price = c.get("base_price", self.menu[c["dish_id"]]["price"])
        ratio = (c["patience_ticks_left"] / pat_max) if pat_max > 0 else 0.0
        got_tip = ratio >= self.t["tip_min_patience_ratio"]
        tip = math.floor(price * self.t["tip_rate"]) if got_tip else 0
        total = price + tip
        self.money += total
        self.earned += total
        self.shift_earned += total
        if got_tip:
            self.reputation = self._clamp_reputation(self.reputation + self.t["tip_reputation"])
        events.append(("paid", {"customer_id": c["id"], "table_id": c["table_id"],
                                "dish_id": c["dish_id"], "amount": total, "tip": tip}))

    def _close_shift(self, events):
        pat_max = int(round(self.t["patience_s"] * TICK))
        for c in sort_by_id(self.customers):
            if c["state"] == "eating":
                self._pay_customer(c, pat_max, events)
            else:
                self._release_reserved(c)
        self.customers = []
        self.hand = None
        for s in self.stoves:
            s["state"] = "idle"
            s["dish"] = None
            s["cook_ticks_left"] = 0
            s["ready_ticks"] = 0

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
                    self._pay_customer(c, pat_max, events)
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
            self.hand_price = stove.get("base_price")
            stove["state"] = "idle"
            stove["dish"] = None
            stove["cook_ticks_left"] = 0
            stove["ready_ticks"] = 0
            stove["base_price"] = None
            events.append(("dish_picked", {"stove_id": stove["id"], "dish_id": dish_id}))
            return
        if stove["state"] == "idle":
            customer = self._next_customer_to_cook()
            if customer is None:
                return
            dish_id = customer["dish_id"]
            ev_data = {"stove_id": stove["id"], "dish_id": dish_id}
            if self.v12:
                res_ids = set(customer.get("reserved", []))
                used_items = [it for it in self.stock_items if it["id"] in res_ids]
                self.stock_items = [it for it in self.stock_items if it["id"] not in res_ids]
                customer["reserved"] = []
                if used_items:
                    avg_fresh = sum(it["fresh"] for it in used_items) / len(used_items)
                    stove["base_price"] = math.floor(self.menu[dish_id]["price"] * avg_fresh / 100.0)
                    used_sorted = sorted(used_items, key=lambda it: (it["kind"], id_key(it["id"])))
                    ev_data["items"] = [
                        {"id": it["id"], "kind": it["kind"], "fresh": round(it["fresh"], 3)}
                        for it in used_sorted
                    ]
                else:
                    stove["base_price"] = self.menu[dish_id]["price"]
                    ev_data["items"] = []
            else:
                customer["reserved"] = {}
            stove["state"] = "cooking"
            stove["dish"] = dish_id
            stove["cook_ticks_left"] = int(round(self.menu[dish_id]["cook_s"] * TICK))
            events.append(("cook_started", ev_data))

    def _next_customer_to_cook(self):
        # Đếm số món đang có sẵn (trên bếp hoặc trên tay) để không nấu trùng
        available = {}
        if self.hand:
            available[self.hand] = available.get(self.hand, 0) + 1
        for s in self.stoves:
            if s["state"] in ("cooking", "ready") and s["dish"]:
                available[s["dish"]] = available.get(s["dish"], 0) + 1
        waiting = [
            c for c in sort_by_id(self.customers)
            if c["state"] == "waiting" and not c.get("unfulfillable") and c.get("dish_id") in self.menu
        ]
        waiting.sort(key=lambda c: (c.get("order_tick", 0), id_key(c["table_id"])))
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
        if self.hand_price is not None:
            customer["base_price"] = self.hand_price
        self.hand = None
        self.hand_price = None
        customer["state"] = "eating"
        customer["eat_ticks_left"] = int(round(self.t["eat_s"] * TICK))
        customer["reserved"] = [] if self.v12 else {}
        events.append(("served", {"customer_id": customer["id"], "table_id": table["id"], "dish_id": dish_id}))

    def _spawn_customer(self, events):
        occupied = {c["table_id"] for c in self.customers}
        free_tables = [tb for tb in sort_by_id(self.tables) if tb["id"] not in occupied]
        if not free_tables:
            return
        table = free_tables[0]
        menu_ids = sorted(self.allowed_dishes) if self.allowed_dishes is not None else sorted(self.menu)
        if self.v12:
            used_ids = self._reserved_ids()
            sp_units = self._spoiled_units()
            avail_counts = {}
            for it in self.stock_items:
                if it["id"] not in used_ids and it["units"] >= sp_units:
                    avail_counts[it["kind"]] = avail_counts.get(it["kind"], 0) + 1
            affordable = [
                dish_id for dish_id in menu_ids
                if dish_id in self.menu and all(avail_counts.get(k, 0) >= qty for k, qty in self.menu[dish_id]["recipe"].items())
            ]
        else:
            affordable = [
                dish_id for dish_id in menu_ids
                if dish_id in self.menu and all(self.stock.get(k, 0) >= qty for k, qty in self.menu[dish_id]["recipe"].items())
            ]
        if not affordable:
            events.append(("no_dish", {"table_id": table["id"]}))
            return
        dish_id = self.rng.get("customer_order").choice(affordable)
        reserved = self._reserve_v12(dish_id) if self.v12 else self._reserve_if_available(dish_id)
        cid = self.ids.new("C")
        self.customers.append({
            "id": cid,
            "table_id": table["id"],
            "dish_id": dish_id,
            "state": "waiting",
            "order_tick": self._sim_tick,
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
