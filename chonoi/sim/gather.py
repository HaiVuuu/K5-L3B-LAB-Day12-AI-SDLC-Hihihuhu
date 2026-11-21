"""Buổi sáng — Lặn & Hái (`gather`), lõi Phase 1–2.

Mặt cắt dòng sông nhìn NGANG: vị trí `[x, d]` (x sang phải, `d` độ sâu hướng xuống, d = 0 là mặt nước).
`move = [x, d]`: thành phần thứ hai DƯƠNG = bơi xuống. Hướng mặt là góc từ +x, dương = xuống.

Thứ tự: timer -> bơi/oxy/ngạt -> quái/hit -> bến/hái -> bắt -> hết giờ -> cá bơi/sinh.
Giỏ giữ thứ tự nhặt (mới nhất ở cuối); không ghi file từ sim, runner xuất kho khi kết thúc.
Luật/payload theo PRD-0 E–G và TICKET-02 1.1/1.2/4.5.
"""

import math

from ..ids import sort_by_id
from ..inventory import hold_to_items
from .ramp import ramp_velocity
from .monsters import Monsters

AXES = ("x", "d")


class GatherSim:
    mode = "gather"
    phase = "gather"

    def __init__(self, tuning, scenario, streams, ids, *, day=1, active_upgrades=None):
        t = tuning["gather"]
        self.t = t
        self.tick_hz = tuning["tick_hz"]
        self.rng = streams
        self.ids = ids
        self.phase_tick = 0
        self.day = day
        self.active_upgrades = dict(active_upgrades or {})
        oxygen_max_s, self.hp_max = t["oxygen_max_s"], t["hp_max"]
        for key, levels in tuning.get("shop", {}).get("upgrades", {}).items():
            level = self.active_upgrades.get(key, 0)
            selected = next((entry for entry in levels if entry["level"] == level), None)
            if selected is not None:
                if key == "oxygen":
                    oxygen_max_s = selected["oxygen_max_s"]
                elif key == "hp":
                    self.hp_max = selected["hp_max"]
        p = scenario.get("player", {})
        self.pos = [float(c) for c in p.get("pos", t["start_pos"])]
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        self.heading = float(p.get("heading_deg", t["start_heading_deg"]))
        self.oxygen_max = int(round(oxygen_max_s * self.tick_hz))
        self.oxygen_ticks = p.get("oxygen_ticks", self.oxygen_max)
        self.hp = p.get("hp", self.hp_max)
        self.zero_oxy_ticks = p.get("zero_oxy_ticks", 0)
        self.invuln_ticks = p.get("invuln_ticks", 0)
        self.catch_cd_ticks = p.get("catch_cd_ticks", 0)
        self.hold = list(scenario.get("hold", []))  # thứ tự nhặt, cuối mảng là mới nhất
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * self.tick_hz)))
        # nút và đàn cá: scenario THAY THẾ danh sách mặc định; random_fish=false tắt cá mặc định
        src_nodes = scenario["nodes"] if "nodes" in scenario else t["nodes"]
        self.nodes = [{"id": n["id"], "kind": n["kind"], "pos": [float(c) for c in n["pos"]],
                       "regrow_ticks": n.get("regrow_ticks", 0)} for n in src_nodes]
        self.random_fish = scenario.get("random_fish", True)
        self.fish_moving = isinstance(t["fish_initial"], int) and self.random_fish
        if "fish" in scenario:
            src_fish = scenario["fish"]
        elif self.random_fish and not self.fish_moving:
            src_fish = t["fish_initial"]
        else:
            src_fish = []
        self.fish = [{"id": f["id"], "kind": f["kind"], "pos": [float(c) for c in f["pos"]],
                      "heading_deg": f.get("heading_deg", 0), "age_ticks": f.get("age_ticks", 0)} for f in src_fish]
        for coll in (self.nodes, self.fish):
            for e in coll:
                ids.reserve(e["id"])
        if "fish" not in scenario and self.fish_moving:
            for _ in range(t["fish_initial"]):
                self._spawn_fish(initial=True)
        self._monsters = Monsters(tuning, scenario, ids, day=day)
        self.monsters = self._monsters.entities
        self.money = 0
        self.earned = 0
        self.reputation = tuning["quan"]["reputation_initial"]
        self.done = False
        self.reason = None

    # --- giao diện cho runner -------------------------------------------------
    def inventory_items(self) -> dict:
        return hold_to_items(self.hold)

    def snapshot(self) -> dict:
        return {
            "player": {"pos": self.pos, "vel": self.vel, "heading_deg": self.heading,
                       "oxygen_ticks": self.oxygen_ticks, "oxygen_max_ticks": self.oxygen_max,
                       "hp": self.hp, "hp_max": self.hp_max, "zero_oxy_ticks": self.zero_oxy_ticks,
                       "invuln_ticks": self.invuln_ticks, "catch_cd_ticks": self.catch_cd_ticks,
                       "at_surface": self._at_surface()},
            "hold": self.hold, "hold_count": len(self.hold),
            "hold_capacity": self.t["hold_capacity"],
            "nodes": [{"id": n["id"], "pos": n["pos"], "kind": n["kind"],
                       "ready": n["regrow_ticks"] == 0, "regrow_ticks": n["regrow_ticks"]}
                      for n in sort_by_id(self.nodes)],
            "fish": [{"id": f["id"], "pos": f["pos"], "kind": f["kind"],
                      "heading_deg": f["heading_deg"], "age_ticks": f["age_ticks"]}
                     for f in sort_by_id(self.fish)],
            "monsters": self._monsters.snapshot(),
        }

    # --- một bước ---------------------------------------------------------------
    def step(self, inp):
        if self.done:
            return []
        events = []
        self.phase_tick += 1
        # 1. đồng hồ và hàng có sẵn: giảm bộ đếm, nút mọc lại
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        self.invuln_ticks = max(0, self.invuln_ticks - 1)
        self.catch_cd_ticks = max(0, self.catch_cd_ticks - 1)
        for n in sort_by_id(self.nodes):
            if n["regrow_ticks"] > 0:
                n["regrow_ticks"] -= 1
                if n["regrow_ticks"] == 0:
                    events.append(("node_regrown", {"node_id": n["id"]}))
        # 2. bơi + chặn mép
        was_at_surface = self._at_surface()
        self._move(inp)
        at_surface = self._at_surface()
        if was_at_surface != at_surface:
            events.append(("surface" if at_surface else "dive", {"pos": list(self.pos)}))
        self._oxygen(at_surface, events)
        if self.done:
            return events
        # 3. quái di chuyển trước khi tương tác/bắt; ngạt xuyên bất tử.
        candidates = self._monsters.step(self.pos)
        if self.invuln_ticks == 0 and candidates:
            monster = min(candidates, key=lambda m: math.dist(self.pos, m["pos"]))
            count = math.floor(len(self.hold) * self.t["monsters"]["loss_ratio"])
            lost = [self.hold.pop() for _ in range(count)]
            self.hp = max(0, self.hp - 1)
            self.invuln_ticks = self.t["monsters"]["invuln_ticks"]
            self._monsters.recoil(monster, self.pos)
            events.append(("monster_hit", {"monster_id": monster["id"], "hp": self.hp,
                                           "lost": lost, "pos": list(self.pos)}))
            if self.hp == 0:
                self._faint("monster", events)
                return events
        # 4. interact: bến trước, rồi hái
        if inp.pressed("interact"):
            if self._in_dock():
                self._finish("docked", events)
                return events
            if at_surface:
                node = self._nearest([n for n in self.nodes if n["regrow_ticks"] == 0],
                                     self.t["interact_radius"])
                if node is not None:
                    data = {"node_id": node["id"], "kind": node["kind"], "amount": self.t["node_yield"]}
                    if self._collect(node["kind"], data["amount"], "gather", "node_id", node["id"], events):
                        node["regrow_ticks"] = int(round(self.t["regrow_s"] * self.tick_hz))
                        events.append(("gather", data))
        # 5. bắt cá theo vị trí trước khi bơi
        if inp.pressed("catch") and not at_surface and self.catch_cd_ticks == 0:
            fish = self._nearest(self.fish, self.t["catch_radius"])
            if fish is not None:
                data = {"fish_id": fish["id"], "kind": fish["kind"],
                        "yield": self.t["fish_yield"][fish["kind"]]}
                if self._collect(fish["kind"], data["yield"], "catch", "fish_id", fish["id"], events):
                    self.fish.remove(fish)
                    self.catch_cd_ticks = int(round(self.t["catch_cooldown_s"] * self.tick_hz))
                    events.append(("fish_caught", data))
        # 6. hết giờ; chỉ khi còn giờ mới bơi/sinh cá
        if self.time_left_ticks <= 0:
            self._finish("time", events)
        elif self.fish_moving:
            self._swim_fish()
            if self.phase_tick % self.t["fish_spawn_ticks"] == 0:
                self._spawn_fish(events=events)
        return events

    # --- tiện ích ---------------------------------------------------------------
    def _oxygen(self, at_surface, events):
        if at_surface:
            self.oxygen_ticks = min(self.oxygen_max, self.oxygen_ticks + self.t["oxygen_refill_per_tick"])
            self.zero_oxy_ticks = 0
            return
        previous = self.oxygen_ticks
        self.oxygen_ticks = max(0, previous - 1)
        if previous > 0 and self.oxygen_ticks == 0:
            events.append(("oxygen_empty", {"oxygen_ticks": 0}))
        if self.oxygen_ticks > 0:
            self.zero_oxy_ticks = 0
            return
        self.zero_oxy_ticks += 1
        if self.zero_oxy_ticks >= self.t["choke_interval_ticks"]:
            self.zero_oxy_ticks = 0
            self.hp = max(0, self.hp - 1)
            events.append(("choke", {"hp": self.hp}))
            if self.hp == 0:
                self._faint("choke", events)

    def _faint(self, cause, events):
        lost = list(reversed(self.hold))
        self.hold.clear()
        events.append(("faint", {"cause": cause, "lost": lost, "hp": 0}))
        self._finish("fainted", events)

    def _spawn_fish(self, initial=False, events=None):
        if len(self.fish) >= self.t["fish_max"]:
            return False
        clearance = 0 if initial else self.t["fish_spawn_clearance"]
        pools = {}
        for kind in sorted(self.t["fish_weights"]):
            points = [[x, d] for x in self.t["fish_spawn_x"] for d in self.t["fish_spawn_depths"][kind]]
            pools[kind] = [p for p in points if all(math.dist(p, f["pos"]) > clearance for f in self.fish)]
        kinds = [kind for kind in sorted(pools) if pools[kind]]
        if not kinds:
            return False
        rng = self.rng.get("fish_spawn")
        kind = rng.choices(kinds, weights=[self.t["fish_weights"][k] for k in kinds], k=1)[0]
        position = list(rng.choice(pools[kind]))
        entity = {"id": self.ids.new("F"), "kind": kind, "pos": position,
                  "heading_deg": self.rng.get("fish_heading").uniform(0, 360), "age_ticks": 0}
        self.fish.append(entity)
        if events is not None:
            events.append(("fish_spawned", {"id": entity["id"], "kind": kind, "pos": list(position)}))
        return True

    def _swim_fish(self):
        for f in sort_by_id(self.fish):
            f["age_ticks"] += 1
            if f["age_ticks"] % self.t["fish_turn_ticks"] == 0:
                f["heading_deg"] = self.rng.get("fish_turn:" + f["id"]).uniform(0, 360)
            angle = math.radians(f["heading_deg"])
            direction = [math.cos(angle), math.sin(angle)]
            distance = self.t["fish_speed"] / self.tick_hz
            for axis, bounds in enumerate((self.t["fish_x"], self.t["fish_depths"][f["kind"]])):
                lo, hi = bounds
                coordinate = f["pos"][axis] + direction[axis] * distance
                while coordinate < lo or coordinate > hi:
                    coordinate = 2 * lo - coordinate if coordinate < lo else 2 * hi - coordinate
                    direction[axis] *= -1
                if (coordinate == lo and direction[axis] < 0) or (coordinate == hi and direction[axis] > 0):
                    direction[axis] *= -1
                f["pos"][axis] = coordinate
            f["heading_deg"] = math.degrees(math.atan2(direction[1], direction[0])) % 360

    def _nearest(self, entities, radius):
        # min giữ phần tử đầu khi hòa khoảng cách; sort_by_id cho F2 trước F10.
        candidates = [(math.dist(self.pos, e["pos"]), e) for e in sort_by_id(entities)]
        candidates = [(distance, e) for distance, e in candidates if distance <= radius]
        return min(candidates, key=lambda pair: pair[0])[1] if candidates else None

    def _collect(self, kind, qty, action, id_field, ident, events):
        free = self.t["hold_capacity"] - len(self.hold)
        if qty > free:
            events.append(("hold_full", {"action": action, id_field: ident, "required": qty, "free": free}))
            return False
        self.hold.extend([kind] * qty)
        return True

    def _at_surface(self) -> bool:
        return self.pos[1] <= self.t["surface_depth"]

    def _in_dock(self) -> bool:
        return math.dist(self.pos, self.t["dock_pos"]) <= self.t["dock_radius"]

    def _finish(self, reason, events):
        self.done = True
        self.reason = reason
        events.append(("gather_end", {"reason": reason, "inventory": {"items": self.inventory_items()}}))

    def _move(self, inp):
        speed = self.t["swim_speed"]
        mx, md = inp.move
        self.vel = ramp_velocity(self, (mx * speed, md * speed), int(self.t["ramp_max_ticks"]))
        if (mx, md) != (0.0, 0.0):
            self.heading = math.degrees(math.atan2(md, mx)) % 360
        b = self.t["bounds"]
        for i, axis in enumerate(AXES):
            self.pos[i] += self.vel[i] / self.tick_hz
            lo, hi = b[axis]
            if self.pos[i] <= lo:
                self.pos[i] = lo
                self.vel[i] = max(0.0, self.vel[i])
            elif self.pos[i] >= hi:
                self.pos[i] = hi
                self.vel[i] = min(0.0, self.vel[i])
