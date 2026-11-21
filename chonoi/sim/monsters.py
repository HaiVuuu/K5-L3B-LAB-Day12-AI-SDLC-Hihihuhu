"""Cá Sấu: patrol/chase/recoil và chọn một va chạm, TICKET-02 §1.2/4.5.

GatherSim giữ quyền xử lý Máu, bất tử, LIFO và kết thúc; module này chỉ cập nhật quái.
"""

import math

from ..ids import sort_by_id


class Monsters:
    def __init__(self, tuning, scenario, ids, day=1):
        self.t = tuning["gather"].get("monsters", {})
        self.bounds = tuning["gather"]["bounds"]
        self.hz = tuning["tick_hz"]
        source = scenario.get("monsters", [m for m in self.t.get("spawns", []) if m["from_day"] <= day])
        self.entities = []
        for m in sort_by_id(source):
            self.entities.append({
                "id": m["id"], "kind": m["kind"], "pos": list(m["pos"]),
                "waypoints": [list(p) for p in m["waypoints"]],
                "target_idx": m.get("target_idx", 1), "state": m.get("state", "patrol"),
                "state_ticks_left": m.get("state_ticks_left", 0),
                "recoil_dir": list(m["recoil_dir"]) if m.get("recoil_dir") is not None else None,
            })
            ids.reserve(m["id"])

    def snapshot(self):
        return [{k: ([list(p) for p in value] if k == "waypoints" else list(value))
                 if isinstance(value, list) else value for k, value in m.items()}
                for m in sort_by_id(self.entities)]

    def step(self, player_pos):
        """Di chuyển theo id; trả danh sách có thể gây hit trong chính bước này."""
        hittable = []
        for m in sort_by_id(self.entities):
            spec = self.t["species"][m["kind"]]
            if m["state"] == "recoil":
                distance = spec["recoil_dist"] / spec["recoil_ticks"]
                for axis in range(2):
                    m["pos"][axis] += m["recoil_dir"][axis] * distance
                self._clamp(m, spec)
                m["state_ticks_left"] -= 1
                if m["state_ticks_left"] == 0:
                    m.update(state="patrol", recoil_dir=None)
                # Không phát hiện hay hit kể cả bước vừa hết recoil.
                continue
            distance = math.dist(m["pos"], player_pos)
            in_depth = player_pos[1] >= spec["depths"][0]
            if m["state"] == "chase":
                if not in_depth or distance > spec["exit_radius"]:
                    m["state"] = "patrol"
            elif in_depth and distance <= spec["detect_radius"]:
                m["state"] = "chase"
            if m["state"] == "chase":
                self._toward(m, player_pos, spec["chase_speed"] / self.hz)
            else:
                waypoint = m["waypoints"][m["target_idx"]]
                if self._toward(m, waypoint, spec["patrol_speed"] / self.hz):
                    m["target_idx"] = 1 - m["target_idx"]
            self._clamp(m, spec)
            if in_depth and math.dist(m["pos"], player_pos) <= spec["hit_radius"]:
                hittable.append(m)
        return hittable

    def recoil(self, monster, player_pos):
        dx, dd = (monster["pos"][i] - player_pos[i] for i in range(2))
        distance = math.hypot(dx, dd)
        direction = [dx / distance, dd / distance] if distance else [1.0, 0.0]
        monster.update(state="recoil", recoil_dir=direction,
                       state_ticks_left=self.t["species"][monster["kind"]]["recoil_ticks"])

    @staticmethod
    def _toward(monster, target, step):
        distance = math.dist(monster["pos"], target)
        if distance <= step:
            monster["pos"] = list(target)
            return True
        monster["pos"] = [p + (t - p) * step / distance for p, t in zip(monster["pos"], target)]
        return False

    def _clamp(self, monster, spec):
        for i, axis in enumerate(("x", "d")):
            lo, hi = self.bounds[axis]
            if i == 1:
                lo, hi = max(lo, spec["depths"][0]), min(hi, spec["depths"][1])
            monster["pos"][i] = min(hi, max(lo, monster["pos"][i]))
