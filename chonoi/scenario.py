"""Nạp và kiểm scenario (Contract D). Trả về dict của đúng khối theo mode.

KHUNG: kiểm cú pháp, id trùng, bộ đếm âm, khoang vượt sức chứa, trường lạ.

QA (Phase 2-3): loại nguyên liệu / nút / cá lấy từ contract (không cứng 4 loại của v1.0), kiểm `monsters`,
và khi contract ĐANG CHẠY v1.2 (`tuning._contract_version == "1.2"`, do load_contract gắn; KHÔNG suy từ việc
có khối `freshness`, vì manifest có thể chứa freshness mà vẫn ở v1.1 trong lúc chuyển tiếp) thì giỏ/kho/giữ chỗ là
MẢNG CÁ THỂ {id, kind, fresh}: id duy nhất, fresh trong [0, 100], giữ chỗ chỉ trỏ tới id có trong kho, chưa ươn,
không trùng giữa các đơn và đủ công thức của món.
TODO(nhóm): bổ sung kiểm mâu thuẫn mức luật mà nhóm cần (khách giữ chỗ quá kho, đơn assigned
phải có đúng một món, khách eating thiếu giá/tip...) — xem PRD-0 mục D và 'Mâu thuẫn -> mã 2'.
"""

import json

from .errors import BadInput
from .inventory import validate_items

GATHER_KEYS = {"player", "hold", "nodes", "fish", "random_fish", "time_left_ticks", "monsters"}
GATHER_PLAYER_KEYS = {"pos", "vel", "heading_deg", "hp", "oxygen_ticks", "zero_oxy_ticks",
                      "invuln_ticks", "catch_cd_ticks"}
MONSTER_STATES = ("patrol", "chase", "recoil")
QUAN_PLAYER_KEYS = {"pos", "vel"}
QUAN_KEYS = {"player", "stock", "hand", "stoves", "tables", "customers", "random_customers",
             "reputation", "time_left_ticks"}


def node_kinds(tuning):
    return tuple(sorted({n["kind"] for n in tuning["gather"]["nodes"]}))


def fish_kinds(tuning):
    return tuple(sorted(tuning["gather"]["fish_yield"]))


def ingredient_kinds(tuning):
    """Mọi loại nguyên liệu hợp lệ: vật liệu trong công thức + loại nút + loại cá (v1.0: 4 loại, v1.1: 6 loại)."""
    kinds = set(node_kinds(tuning)) | set(fish_kinds(tuning))
    for dish in tuning["menu"].values():
        kinds |= set(dish["recipe"])
    return tuple(sorted(kinds))


def _is_v12(tuning):
    return tuning.get("_contract_version") == "1.2" and "freshness" in tuning


def _spoiled_below(tuning):
    return tuning["freshness"].get("spoiled_below", 30)


def _check_items(name, arr, tuning, capacity=None, seen_ids=None):
    """Mảng cá thể v1.2: [{id, kind, fresh}], id duy nhất (kể cả giữa các mảng nếu truyền seen_ids)."""
    if not isinstance(arr, list):
        raise BadInput(f"{name} phải là mảng cá thể {{id, kind, fresh}} (contract {tuning.get('contract_version', '1.2')}, không dùng bộ đếm)")
    if capacity is not None and len(arr) > capacity:
        raise BadInput(f"{name} vượt sức chứa")
    kinds = ingredient_kinds(tuning)
    seen = seen_ids if seen_ids is not None else set()
    for it in arr:
        if not isinstance(it, dict) or set(it) != {"id", "kind", "fresh"}:
            raise BadInput(f"{name}: mỗi cá thể phải có đúng id, kind, fresh")
        if not isinstance(it["id"], str) or not it["id"]:
            raise BadInput(f"{name}: id cá thể phải là chuỗi khác rỗng")
        if it["id"] in seen:
            raise BadInput(f"{name}: id cá thể trùng {it['id']}")
        seen.add(it["id"])
        if it["kind"] not in kinds:
            raise BadInput(f"{name}.{it['id']}: nguyên liệu lạ {it['kind']!r}")
        if not _num(it["fresh"]) or not (0 <= it["fresh"] <= 100):
            raise BadInput(f"{name}.{it['id']}: fresh phải là số trong [0, 100]")


def _check_ids(name, arr):
    if not isinstance(arr, list):
        raise BadInput(f"{name} phải là mảng")
    seen = set()
    for e in arr:
        if not isinstance(e, dict) or not isinstance(e.get("id"), str) or not e["id"]:
            raise BadInput(f"{name}: mỗi phần tử cần id (chuỗi khác rỗng)")
        if e["id"] in seen:
            raise BadInput(f"{name}: id trùng {e['id']}")
        seen.add(e["id"])


def load_scenario(path, mode: str, tuning: dict) -> dict:
    if path is None:
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được scenario {path}: {e}")
    if not isinstance(data, dict) or not set(data) <= {"gather", "quan"}:
        raise BadInput("scenario chỉ được có khối 'gather' hoặc 'quan'")
    if set(data) - {mode}:
        raise BadInput(f"khối sai mode: chạy --mode {mode} chỉ nhận khối '{mode}'")
    block = data.get(mode, {})
    if not isinstance(block, dict):
        raise BadInput(f"khối {mode} phải là object")
    allowed = GATHER_KEYS if mode == "gather" else QUAN_KEYS
    extra = set(block) - allowed
    if extra:
        raise BadInput(f"trường lạ/chưa hỗ trợ trong {mode}: {sorted(extra)}")
    dur = int(round(tuning[mode]["duration_s"] * 60))
    if "time_left_ticks" in block:
        t = block["time_left_ticks"]
        if isinstance(t, bool) or not isinstance(t, int) or not (1 <= t <= dur):
            raise BadInput(f"time_left_ticks phải là số nguyên trong [1, {dur}]")
    if mode == "gather":
        _validate_gather(block, tuning)
    else:
        _validate_quan(block, tuning)
    return block


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _nonneg_int(name, v):
    if isinstance(v, bool) or not isinstance(v, int) or v < 0:
        raise BadInput(f"{name} phải là số nguyên không âm")


def _pos(name, pos, bounds, axes=("x", "d")):
    if not (isinstance(pos, list) and len(pos) == 2 and all(_num(c) for c in pos)):
        raise BadInput(f"{name} phải là [{axes[0]}, {axes[1]}]")
    for c, axis in zip(pos, axes):
        lo, hi = bounds[axis]
        if not (lo <= c <= hi):
            raise BadInput(f"{name} nằm ngoài vùng nước ({axis} ∈ [{lo}, {hi}])")


def _validate_gather(b, tuning):
    g = tuning["gather"]
    bounds = g["bounds"]
    for arr in ("nodes", "fish"):
        if arr in b:
            _check_ids(arr, b[arr])
    if "random_fish" in b and not isinstance(b["random_fish"], bool):
        raise BadInput("random_fish phải là boolean")
    if "hold" in b:
        h = b["hold"]
        if _is_v12(tuning):
            _check_items("hold", h, tuning, capacity=g["hold_capacity"])
        else:
            if not isinstance(h, list) or any(k not in ingredient_kinds(tuning) for k in h):
                raise BadInput("hold phải là mảng id nguyên liệu hợp lệ")
            if len(h) > g["hold_capacity"]:
                raise BadInput("hold vượt sức chứa")
    if "monsters" in b:
        _validate_monsters(b["monsters"], tuning)
    p = b.get("player", {})
    if not isinstance(p, dict):
        raise BadInput("player phải là object")
    extra = set(p) - GATHER_PLAYER_KEYS
    if extra:
        raise BadInput(f"trường lạ/chưa hỗ trợ trong gather.player: {sorted(extra)}")
    if "pos" in p:
        _pos("player.pos", p["pos"], bounds)
    if "vel" in p and not (isinstance(p["vel"], list) and len(p["vel"]) == 2 and all(_num(c) for c in p["vel"])):
        raise BadInput("player.vel phải là [x, d]")
    if "heading_deg" in p and not _num(p["heading_deg"]):
        raise BadInput("player.heading_deg phải là số")
    for key in ("invuln_ticks", "catch_cd_ticks", "zero_oxy_ticks", "oxygen_ticks", "hp"):
        if key in p:
            _nonneg_int(f"player.{key}", p[key])
    omax = int(round(g["oxygen_max_s"] * 60))
    if "oxygen_ticks" in p and p["oxygen_ticks"] > omax:
        raise BadInput("player.oxygen_ticks vượt oxy tối đa")
    if "hp" in p and not (1 <= p["hp"] <= g["hp_max"]):
        raise BadInput("player.hp phải trong [1, hp_max]")
    if "zero_oxy_ticks" in p:
        pos = p.get("pos", g["start_pos"])
        oxy = p.get("oxygen_ticks", omax)
        if p["zero_oxy_ticks"] > 59:
            raise BadInput("player.zero_oxy_ticks phải trong [0, 59]")
        if p["zero_oxy_ticks"] > 0 and not (oxy == 0 and pos[1] > g["surface_depth"]):
            raise BadInput("player.zero_oxy_ticks > 0 chỉ khi oxy = 0 và đang dưới nước")
    nkinds, fkinds = node_kinds(tuning), fish_kinds(tuning)
    for n in b.get("nodes", []):
        if n.get("kind") not in nkinds:
            raise BadInput(f"nodes.{n['id']}: kind phải là một trong {nkinds}")
        _pos(f"nodes.{n['id']}.pos", n.get("pos"), bounds)
        if n["pos"][1] != 0:
            raise BadInput(f"nodes.{n['id']}: nút hái nằm ở mặt nước (d = 0)")
        if "regrow_ticks" in n:
            _nonneg_int(f"nodes.{n['id']}.regrow_ticks", n["regrow_ticks"])
    for f in b.get("fish", []):
        if f.get("kind") not in fkinds:
            raise BadInput(f"fish.{f['id']}: kind phải là một trong {fkinds}")
        _pos(f"fish.{f['id']}.pos", f.get("pos"), bounds)
        if f["pos"][1] <= g["surface_depth"]:
            raise BadInput(f"fish.{f['id']}: đàn cá phải ở dưới nước")
        if "heading_deg" in f and not _num(f["heading_deg"]):
            raise BadInput(f"fish.{f['id']}.heading_deg phải là số")


def _validate_monsters(arr, tuning):
    mcfg = tuning["gather"].get("monsters")
    if not mcfg:
        raise BadInput("contract này chưa có monsters (cần v1.1 trở lên)")
    _check_ids("monsters", arr)
    bounds = tuning["gather"]["bounds"]
    species = mcfg["species"]
    for m in arr:
        if m.get("kind") not in species:
            raise BadInput(f"monsters.{m['id']}: kind phải là một trong {tuple(sorted(species))}")
        _pos(f"monsters.{m['id']}.pos", m.get("pos"), bounds)
        lo, hi = species[m["kind"]]["depths"]
        if not (lo <= m["pos"][1] <= hi):
            raise BadInput(f"monsters.{m['id']}: d phải trong dải độ sâu của loài [{lo}, {hi}]")
        if "state" in m and m["state"] not in MONSTER_STATES:
            raise BadInput(f"monsters.{m['id']}.state phải là một trong {MONSTER_STATES}")
        if "waypoints" in m:
            wp = m["waypoints"]
            if not isinstance(wp, list) or len(wp) < 1:
                raise BadInput(f"monsters.{m['id']}.waypoints phải là mảng điểm không rỗng")
            for i, w in enumerate(wp):
                _pos(f"monsters.{m['id']}.waypoints[{i}]", w, bounds)


def _validate_reserved(b, tuning):
    """v1.2: customers[].reserved là mảng id cá thể trong stock; không ươn, không trùng giữa các đơn."""
    stock = {it["id"]: it for it in b.get("stock", []) if isinstance(it, dict)}
    below = _spoiled_below(tuning)
    taken = {}
    for c in b.get("customers", []):
        if "reserved" not in c:
            continue
        r = c["reserved"]
        if not isinstance(r, list) or any(not isinstance(x, str) for x in r):
            raise BadInput(f"customers.{c['id']}.reserved phải là mảng id cá thể (v1.2)")
        if len(r) != len(set(r)):
            raise BadInput(f"customers.{c['id']}.reserved có id trùng")
        for x in r:
            if x not in stock:
                raise BadInput(f"customers.{c['id']}: giữ chỗ id không có trong stock: {x}")
            if stock[x]["fresh"] < below:
                raise BadInput(f"customers.{c['id']}: giữ chỗ hàng ươn {x} (fresh < {below})")
            if x in taken:
                raise BadInput(f"id {x} bị giữ chỗ bởi cả {taken[x]} và {c['id']}")
            taken[x] = c["id"]
        dish = tuning["menu"].get(c.get("dish_id"))
        if dish is not None and r:  # "đủ công thức": số lượng từng loại đúng bằng công thức của món
            need = dict(dish["recipe"])
            got = {}
            for x in r:
                got[stock[x]["kind"]] = got.get(stock[x]["kind"], 0) + 1
            if got != need:
                raise BadInput(f"customers.{c['id']}: reserved không khớp công thức {c['dish_id']}: {got} != {need}")


def _validate_quan(b, tuning):
    for arr in ("stoves", "tables", "customers"):
        if arr in b:
            _check_ids(arr, b[arr])
    if "stock" in b:
        if _is_v12(tuning):
            _check_items("stock", b["stock"], tuning)
        else:
            validate_items(b["stock"], ingredient_kinds(tuning), contract_version="1.1")  # nhánh bộ đếm cũ: không phụ thuộc manifest
    p = b.get("player", {})
    if not isinstance(p, dict) or set(p) - QUAN_PLAYER_KEYS:
        raise BadInput("quan.player chỉ có pos và vel")
    qb = tuning["quan"]["bounds"]
    if "pos" in p:
        _pos("player.pos", p["pos"], qb, axes=("x", "z"))
    if "vel" in p and not (isinstance(p["vel"], list) and len(p["vel"]) == 2 and all(_num(c) for c in p["vel"])):
        raise BadInput("player.vel phải là [x, z]")
    table_ids = [c.get("table_id") for c in b.get("customers", [])]
    known = {t["id"] for t in tuning["quan"]["tables"]} | {t.get("id") for t in b.get("tables", [])}
    for c in b.get("customers", []):
        if not isinstance(c.get("table_id"), str) or c["table_id"] not in known:
            raise BadInput(f"customers.{c['id']}: table_id phải là bàn có thật")
    if len(table_ids) != len(set(table_ids)):
        raise BadInput("hai khách cùng bàn")
    if _is_v12(tuning):
        _validate_reserved(b, tuning)
