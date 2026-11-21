"""Đọc/kiểm Test Contract v1.0–v1.3; v1.3 giữ gameplay/schema của v1.2."""

import json
import os
import math

from .errors import BadInput

DEFAULT_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "game.contract.json")


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def _between(name, v, lo, hi):
    if not _num(v) or not (lo <= v <= hi):
        raise BadInput(f"tuning.{name} phải trong [{lo}, {hi}], đang là {v!r}")


def load_contract(path=DEFAULT_PATH) -> dict:
    try:
        with open(path, encoding="utf-8") as f:
            c = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được {path}: {e}")
    if c.get("contract_version") not in ("1.0", "1.1", "1.2", "1.3"):
        raise BadInput("contract_version chưa hỗ trợ")
    validate_tuning(c.get("tuning"))
    if c["contract_version"] in ("1.2", "1.3") and "freshness" not in c["tuning"]:
        raise BadInput("contract v1.2/v1.3 cần tuning.freshness")
    if c["contract_version"] == "1.3":
        for key in ("bench_cmd", "soak_cmd"):
            if not isinstance(c.get(key), str) or not c[key].strip():
                raise BadInput(f"contract v1.3 cần {key} là lệnh khác rỗng")
    # Ticket-04: chỉ thêm công cụ đo; các sim/scenario tiếp tục dùng chính schema v1.2.
    c["tuning"]["_contract_version"] = "1.2" if c["contract_version"] == "1.3" else c["contract_version"]
    # Quan/Day từ nhánh Hải dùng cờ này cho kho rỗng và adapter chuyển tiếp.
    c["tuning"]["v12_enabled"] = c["contract_version"] in ("1.2", "1.3")
    return c


def _int_between(name, v, lo, hi):
    if isinstance(v, bool) or not isinstance(v, int) or not (lo <= v <= hi):
        raise BadInput(f"tuning.{name} phải là số nguyên trong [{lo}, {hi}], đang là {v!r}")


def _pos_in(name, pos, bounds, keys):
    if (not isinstance(pos, list) or len(pos) != 2 or not all(_num(c) for c in pos)):
        raise BadInput(f"tuning.{name} phải là [số, số]")
    for c, k in zip(pos, keys):
        lo, hi = bounds[k]
        if not (lo <= c <= hi):
            raise BadInput(f"tuning.{name} nằm ngoài vùng {k} ∈ [{lo}, {hi}]")


def _bounds(name, b, keys):
    if not isinstance(b, dict) or set(b) != set(keys):
        raise BadInput(f"tuning.{name}.bounds phải có đúng khóa {list(keys)}")
    for k in keys:
        v = b[k]
        if not (isinstance(v, list) and len(v) == 2 and all(_num(c) for c in v) and v[0] == 0 and v[1] > 0):
            raise BadInput(f"tuning.{name}.bounds.{k} phải là [0, số dương]")


def _validate_gather(g):
    """Dải hợp lệ P1 theo PRD mục 13.2."""
    _between("gather.duration_s", g.get("duration_s"), 60, 600)
    _bounds("gather", g.get("bounds"), ("x", "d"))
    b = g["bounds"]
    _between("gather.dock_radius", g.get("dock_radius"), 0.5, 5)
    _between("gather.interact_radius", g.get("interact_radius"), 0.5, 5)
    _between("gather.catch_radius", g.get("catch_radius"), 0.5, 5)
    _between("gather.swim_speed", g.get("swim_speed"), 1, 10)
    _between("gather.catch_cooldown_s", g.get("catch_cooldown_s"), 0, 10)
    _between("gather.oxygen_max_s", g.get("oxygen_max_s"), 10, 120)
    _int_between("gather.ramp_max_ticks", g.get("ramp_max_ticks"), 0, 6)
    _int_between("gather.hold_capacity", g.get("hold_capacity"), 4, 30)
    _int_between("gather.hp_max", g.get("hp_max"), 1, 99)
    _int_between("gather.oxygen_refill_per_tick", g.get("oxygen_refill_per_tick"), 1, 10_000)
    _int_between("gather.choke_interval_ticks", g.get("choke_interval_ticks"), 1, 10_000)
    _int_between("gather.node_yield", g.get("node_yield"), 1, 12)
    _between("gather.regrow_s", g.get("regrow_s"), 0.1, 600)
    _between("gather.surface_depth", g.get("surface_depth"), 0, 5)
    _pos_in("gather.dock_pos", g.get("dock_pos"), b, ("x", "d"))
    _pos_in("gather.start_pos", g.get("start_pos"), b, ("x", "d"))
    if not _num(g.get("start_heading_deg")):
        raise BadInput("tuning.gather.start_heading_deg phải là số")
    fy = g.get("fish_yield")
    if not isinstance(fy, dict) or not {"ca_linh", "ca_loc"} <= set(fy):
        raise BadInput("tuning.gather.fish_yield phải có ca_linh và ca_loc")
    for k, v in fy.items():
        _int_between(f"gather.fish_yield.{k}", v, 1, g["hold_capacity"])
    nodes = g.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        raise BadInput("tuning.gather.nodes phải là mảng không rỗng")
    seen, kinds = set(), set()
    for n in nodes:
        if not isinstance(n, dict) or not isinstance(n.get("id"), str) or n["id"] in seen:
            raise BadInput("tuning.gather.nodes: mỗi nút cần id duy nhất")
        seen.add(n["id"])
        allowed_nodes = {"bong_dien_dien", "bong_sung"}
        if isinstance(g.get("fish_initial"), int):
            allowed_nodes.add("keo_neo")
        if n.get("kind") not in allowed_nodes:
            raise BadInput(f"tuning.gather.nodes.{n['id']}: kind không hợp lệ")
        kinds.add(n["kind"])
        _pos_in(f"gather.nodes.{n['id']}.pos", n.get("pos"), b, ("x", "d"))
        if n["pos"][1] != 0:
            raise BadInput(f"tuning.gather.nodes.{n['id']}: nút hái nằm ở mặt nước (d = 0)")
    if kinds != allowed_nodes:
        raise BadInput("tuning.gather.nodes phải có ít nhất một nút mỗi loại cây")
    fish = g.get("fish_initial")
    if isinstance(fish, int) and not isinstance(fish, bool):
        _int_between("gather.fish_initial", fish, 0, g.get("fish_max", 0))
        return
    if not isinstance(fish, list) or len(fish) != 6:
        raise BadInput("tuning.gather.fish_initial phải là danh sách đúng 6 đàn")
    seen = set()
    for f in fish:
        if not isinstance(f, dict) or not isinstance(f.get("id"), str) or f["id"] in seen:
            raise BadInput("tuning.gather.fish_initial: mỗi đàn cần id duy nhất")
        seen.add(f["id"])
        if f.get("kind") not in fy:
            raise BadInput(f"tuning.gather.fish_initial.{f['id']}: kind phải thuộc fish_yield")
        _pos_in(f"gather.fish_initial.{f['id']}.pos", f.get("pos"), b, ("x", "d"))
        if f["pos"][1] <= g["surface_depth"]:
            raise BadInput(f"tuning.gather.fish_initial.{f['id']}: đàn cá phải ở dưới nước")


def validate_tuning(t):
    if not isinstance(t, dict):
        raise BadInput("thiếu khối tuning")
    g, q, menu = t.get("gather"), t.get("quan"), t.get("menu")
    if not isinstance(g, dict) or not isinstance(q, dict) or not isinstance(menu, dict):
        raise BadInput("tuning phải có gather, quan, menu")
    _validate_gather(g)
    # Quán: dải hợp lệ P1 (PRD mục 13.2)
    _between("quan.duration_s", q.get("duration_s"), 60, 600)
    _bounds("quan", q.get("bounds"), ("x", "z"))
    _between("quan.patience_s", q.get("patience_s"), 20, 180)
    _between("quan.walk_speed", q.get("walk_speed"), 1, 10)
    _between("quan.interact_radius", q.get("interact_radius"), 0.5, 5)
    _int_between("quan.ramp_max_ticks", q.get("ramp_max_ticks", 6), 0, 6)
    _between("quan.eat_s", q.get("eat_s"), 0.1, 600)
    _between("quan.customer_interval_s", q.get("customer_interval_s"), 0.1, 600)
    _int_between("quan.first_customer_tick", q.get("first_customer_tick"), 1, int(q["duration_s"] * 60) - 1)
    if not (_num(q.get("tip_rate")) and q["tip_rate"] > 0 and _num(q.get("left_reputation_delta"))
            and q["left_reputation_delta"] < 0):
        raise BadInput("tip_rate phải > 0 và left_reputation_delta phải < 0")
    ratio = q.get("tip_min_patience_ratio")
    if not (_num(ratio) and 0 < ratio <= 1):
        raise BadInput("quan.tip_min_patience_ratio phải thuộc (0, 1]")
    if not (_num(q.get("tip_reputation")) and q["tip_reputation"] > 0):
        raise BadInput("quan.tip_reputation phải > 0")
    if q.get("burn_s") is not None:
        raise BadInput("burn_s phải là null ở Phase 1")
    # TODO(nhóm): bổ sung kiểm các khóa còn lại nếu muốn chặt hơn (bếp/bàn, uy tín, ...).
    for dish_id, d in menu.items():
        price, cook = d.get("price"), d.get("cook_s")
        if isinstance(price, bool) or not isinstance(price, int) or price <= 0 or not _num(cook) or cook <= 0:
            raise BadInput(f"menu.{dish_id}: price (nguyên) và cook_s phải > 0")
    if isinstance(g.get("fish_initial"), int):
        _validate_p2(t)
    if "freshness" in t:
        config = t["freshness"]
        if not isinstance(config, dict) or set(config) != {"initial", "gather_decay_per_s", "quan_decay_per_s", "spoiled_below"}:
            raise BadInput("tuning.freshness thiếu/sai khóa")
        for key in ("initial", "spoiled_below"):
            _between("freshness." + key, config[key], 0, 100)
        for key in ("gather_decay_per_s", "quan_decay_per_s"):
            _between("freshness." + key, config[key], 0, 100)


def _validate_p2(t):
    g = t["gather"]
    _int_between("tick_hz", t.get("tick_hz"), 60, 60)
    for key in ("fish_turn_ticks", "fish_max", "fish_spawn_ticks"):
        _int_between("gather." + key, g.get(key), 1, 100_000)
    for key in ("fish_speed", "fish_spawn_clearance"):
        _between("gather." + key, g.get(key), 0.001, 100)
    fish_kinds = {"ca_linh", "ca_loc", "ca_keo"}
    for key in ("fish_depths", "fish_spawn_depths", "fish_weights", "fish_yield"):
        if not isinstance(g.get(key), dict) or set(g[key]) != fish_kinds:
            raise BadInput(f"tuning.gather.{key} cần đủ ba loài cá")
    region = g.get("fish_x")
    if not (isinstance(region, list) and len(region) == 2 and all(_num(v) for v in region)
            and g["bounds"]["x"][0] <= region[0] < region[1] <= g["bounds"]["x"][1]):
        raise BadInput("tuning.gather.fish_x phải là miền hợp lệ")
    xs = g.get("fish_spawn_x")
    if not isinstance(xs, list) or not xs or any(not _num(x) or not g["fish_x"][0] <= x <= g["fish_x"][1] for x in xs):
        raise BadInput("tuning.gather.fish_spawn_x không hợp lệ")
    for kind in sorted(fish_kinds):
        depths = g["fish_depths"][kind]
        if not (isinstance(depths, list) and len(depths) == 2 and all(_num(v) for v in depths)
                and g["surface_depth"] < depths[0] < depths[1] <= g["bounds"]["d"][1]):
            raise BadInput(f"tuning.gather.fish_depths.{kind} không hợp lệ")
        spawn = g["fish_spawn_depths"][kind]
        if not isinstance(spawn, list) or not spawn or any(not _num(d) or not depths[0] <= d <= depths[1] for d in spawn):
            raise BadInput(f"tuning.gather.fish_spawn_depths.{kind} không hợp lệ")
        _between(f"gather.fish_weights.{kind}", g["fish_weights"][kind], 0.001, 100_000)
    monsters = g.get("monsters")
    if not isinstance(monsters, dict) or not isinstance(monsters.get("species"), dict) or not isinstance(monsters.get("spawns"), list):
        raise BadInput("tuning.gather.monsters cần species và spawns")
    _int_between("gather.monsters.invuln_ticks", monsters.get("invuln_ticks"), 1, 100_000)
    _between("gather.monsters.loss_ratio", monsters.get("loss_ratio"), 0, 1)
    if "ca_sau" not in monsters["species"]:
        raise BadInput("tuning.gather.monsters cần loài ca_sau")
    for kind, spec in monsters["species"].items():
        if not isinstance(spec, dict):
            raise BadInput(f"tuning.gather.monsters.species.{kind} phải là object")
        for key in ("patrol_speed", "chase_speed", "detect_radius", "exit_radius", "hit_radius", "recoil_dist"):
            _between(f"gather.monsters.species.{kind}.{key}", spec.get(key), 0.001, 1000)
        _int_between(f"gather.monsters.species.{kind}.recoil_ticks", spec.get("recoil_ticks"), 1, 100_000)
        depths = spec.get("depths")
        if not (isinstance(depths, list) and len(depths) == 2 and all(_num(d) for d in depths)
                and 0 <= depths[0] < depths[1] <= g["bounds"]["d"][1]):
            raise BadInput("tuning.gather.monsters.species.depths không hợp lệ")
    seen = set()
    for monster in monsters["spawns"]:
        if not isinstance(monster, dict) or not isinstance(monster.get("id"), str) or monster["id"] in seen:
            raise BadInput("tuning.gather.monsters.spawns cần id duy nhất")
        seen.add(monster["id"])
        if monster.get("kind") not in monsters["species"]:
            raise BadInput("tuning.gather.monsters.spawns.kind không hợp lệ")
        _pos_in("gather.monsters.spawns.pos", monster.get("pos"), g["bounds"], ("x", "d"))
        waypoints = monster.get("waypoints")
        if not isinstance(waypoints, list) or len(waypoints) != 2:
            raise BadInput("tuning.gather.monsters.spawns cần hai waypoint")
        for point in waypoints:
            _pos_in("gather.monsters.waypoint", point, g["bounds"], ("x", "d"))
        _int_between("gather.monsters.from_day", monster.get("from_day"), 1, 5)
    shop = t.get("shop")
    if not isinstance(shop, dict) or not isinstance(shop.get("upgrades"), dict):
        raise BadInput("tuning.shop cần upgrades")
    _int_between("shop.max_ticks", shop.get("max_ticks"), 1, 100_000)
    for key, field in (("oxygen", "oxygen_max_s"), ("hp", "hp_max")):
        levels = shop["upgrades"].get(key)
        if not isinstance(levels, list) or len(levels) != 2:
            raise BadInput(f"tuning.shop.upgrades.{key} cần hai cấp")
        for level, entry in enumerate(levels, 1):
            if not isinstance(entry, dict) or entry.get("level") != level:
                raise BadInput(f"tuning.shop.upgrades.{key} sai cấp")
            _int_between(f"shop.upgrades.{key}.price", entry.get("price"), 1, 1_000_000)
            _int_between(f"shop.upgrades.{key}.{field}", entry.get(field), 1, 10_000)
    plans = t.get("day_plan")
    if not isinstance(plans, list) or len(plans) != 5:
        raise BadInput("tuning.day_plan cần đủ D1–D5")
    for day, plan in enumerate(plans, 1):
        if not isinstance(plan, dict) or plan.get("day") != day or not isinstance(plan.get("dishes"), dict) or not plan["dishes"]:
            raise BadInput("tuning.day_plan sai ngày hoặc dishes")
        ingredients = {}
        for dish, count in plan["dishes"].items():
            if dish not in t["menu"]:
                raise BadInput("tuning.day_plan có món lạ")
            _int_between("day_plan.dishes", count, 1, 100_000)
            for kind, amount in t["menu"][dish]["recipe"].items():
                ingredients[kind] = ingredients.get(kind, 0) + amount * count
        if plan.get("ingredients") != ingredients:
            raise BadInput("tuning.day_plan.ingredients không khớp công thức")
