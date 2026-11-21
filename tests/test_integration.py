"""Test tích hợp (QA lead): chuỗi gather -> kho (inventory) -> quan, tất định theo seed.

Kiểu HỘP ĐEN như test_smoke_p1.py: chỉ chạy `headless_cmd` và đọc JSONL / file kho.

Chạy được trên cả hai contract:
- v1.0/v1.1: giỏ là mảng chuỗi kind, kho là {"items": {kind: số}}.
- v1.2 (Phase 3): giỏ/kho là mảng cá thể {id, kind, fresh}. Fixture dựng bằng `hold()`, kho so theo SỐ LƯỢNG từng
  loại (`counts()`), không so độ tươi vì gather có hao tươi (độ tươi do test_smoke_p3.py kiểm).
- Phần quán ở v1.2 chỉ chạy khi `QuanSim` đã nhận kho cá thể (dò một lần); chưa thì test tự bỏ qua ở bước quán
  (phần gather phía trước vẫn được kiểm). Hải làm xong quan v1.2 thì các test này tự chạy tiếp, không cần sửa.

Chạy: python -m unittest discover -s tests -v
"""

import json
import unittest

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


def read(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def read_bytes(path):
    with open(path, "rb") as f:
        return f.read()


def tuning():
    with open("game.contract.json", encoding="utf-8") as f:
        return json.load(f)["tuning"]


def contract_version():
    with open("game.contract.json", encoding="utf-8") as f:
        return json.load(f)["contract_version"]


V12 = contract_version() == "1.2"


def hold(*kinds):
    """Giỏ fixture theo đúng schema của contract đang chạy."""
    if V12:
        return [{"id": f"I{i + 1}", "kind": k, "fresh": 100} for i, k in enumerate(kinds)]
    return list(kinds)


def counts(items):
    """Kho/giỏ/stock ở mọi dạng (dict đếm, mảng chuỗi, mảng cá thể) -> {kind: số lượng}."""
    if isinstance(items, dict):
        return {k: v for k, v in sorted(items.items()) if v > 0}
    out = {}
    for x in items:
        kind = x if isinstance(x, str) else x["kind"]
        out[kind] = out.get(kind, 0) + 1
    return dict(sorted(out.items()))


def saved_counts(inv_path):
    data = read(inv_path)
    assert list(data) == ["items"], data
    return counts(data["items"])


_QUAN_READY = None


def quan_ready():
    """v1.1: luôn sẵn sàng. v1.2: dò xem quan --inventory đã nhận kho cá thể chưa (dò một lần)."""
    global _QUAN_READY
    if _QUAN_READY is None:
        if not V12:
            _QUAN_READY = True
        else:
            with Workdir() as w:
                inv = write_json(w.path("probe.json"), {"items": [{"id": "I1", "kind": "ca_loc", "fresh": 100}]})
                code, _ = run_headless("--mode", "quan", "--seed", "1", "--ticks", "0", "--inventory", inv,
                                       "--out", w.path("p.jsonl"))
                _QUAN_READY = code == 0
    return _QUAN_READY


def gather_to_inventory(w, scenario, inputs, ticks, seed=42, name="g"):
    """Chạy gather, trả (mã thoát, stderr, đường dẫn kho, đường dẫn jsonl)."""
    sc = write_json(w.path(f"{name}-sc.json"), {"gather": scenario})
    inp = write_json(w.path(f"{name}-in.json"), inputs)
    inv, out = w.path(f"{name}-inv.json"), w.path(f"{name}.jsonl")
    code, err = run_headless("--mode", "gather", "--seed", str(seed), "--ticks", str(ticks), "--scenario", sc,
                             "--inputs", inp, "--inventory-out", inv, "--out", out)
    return code, err, inv, out


def quan_from_inventory(w, inv, ticks=0, seed=42, name="q"):
    if not quan_ready():
        raise unittest.SkipTest("quan chưa nhận kho cá thể (contract v1.2) — chờ Hải làm quan v1.2")
    out = w.path(f"{name}.jsonl")
    code, err = run_headless("--mode", "quan", "--seed", str(seed), "--ticks", str(ticks), "--inventory", inv,
                             "--out", out)
    return code, err, out


class ChuoiGatherKhoQuan(unittest.TestCase):
    """Kho là cầu nối duy nhất giữa hai buổi."""

    def test_chuoi_giu_nguyen_kho_qua_hai_buoi(self):
        want = {"bong_dien_dien": 1, "bong_sung": 2, "ca_linh": 1, "ca_loc": 1}
        h = hold("ca_loc", "ca_linh", "bong_sung", "bong_sung", "bong_dien_dien")
        with Workdir() as w:
            code, err, inv, _ = gather_to_inventory(w, {"hold": h}, frames({"tick": 0, "interact": True}), 1)
            self.assertEqual(code, 0, err)
            self.assertEqual(saved_counts(inv), want)
            code, err, q = quan_from_inventory(w, inv)
            self.assertEqual(code, 0, err)
            self.assertEqual(counts(snapshots(read_jsonl(q))[0]["stock"]), want)

    def test_chuoi_tat_dinh_theo_seed(self):
        """Cùng seed + cùng đầu vào -> file kho và JSONL của cả hai buổi trùng từng byte."""
        runs = []
        for i in (1, 2):
            with Workdir() as w:
                code, err, inv, gout = gather_to_inventory(
                    w, {"hold": hold("ca_loc", "bong_sung")},
                    frames({"tick": 0, "move": [1, 1]}, {"tick": 30, "move": [0, 0]}, {"tick": 40, "interact": True}),
                    60, seed=7)
                self.assertEqual(code, 0, err)
                code, err, q = quan_from_inventory(w, inv, ticks=120, seed=7)
                self.assertEqual(code, 0, err)
                runs.append((read_bytes(gout), read_bytes(inv), read_bytes(q)))
        self.assertEqual(runs[0], runs[1])

    def test_kho_rong_van_vao_quan_duoc(self):
        with Workdir() as w:
            code, err, inv, _ = gather_to_inventory(w, {"hold": []}, frames({"tick": 0, "interact": True}), 1)
            self.assertEqual(code, 0, err)
            self.assertEqual(read(inv), {"items": [] if V12 else {}})
            code, err, q = quan_from_inventory(w, inv)
            self.assertEqual(code, 0, err)
            self.assertEqual(counts(snapshots(read_jsonl(q))[0]["stock"]), {})

    def test_het_gio_gather_van_xuat_kho_dung_mot_lan(self):
        with Workdir() as w:
            code, err, inv, out = gather_to_inventory(
                w, {"hold": hold("ca_loc"), "time_left_ticks": 3, "player": {"pos": [50, 10]}}, frames(), 100)
            self.assertEqual(code, 0, err)
            self.assertEqual(len(events(read_jsonl(out), "gather_end")), 1)
            self.assertEqual(saved_counts(inv), {"ca_loc": 1})
            code, err, _ = quan_from_inventory(w, inv)
            self.assertEqual(code, 0, err)

    def test_quan_chay_het_ca_voi_kho_tu_gather(self):
        """Quán hết giờ đúng ticks cấu hình và có đúng một quan_end khi chạy hết ca với kho từ gather."""
        with Workdir() as w:
            code, err, inv, _ = gather_to_inventory(w, {"hold": hold("ca_loc")}, frames({"tick": 0, "interact": True}), 1)
            self.assertEqual(code, 0, err)
            duration = int(round(tuning()["quan"]["duration_s"] * 60))
            code, err, q = quan_from_inventory(w, inv, ticks=duration + 5)
            self.assertEqual(code, 0, err)
            rows = read_jsonl(q)
            self.assertEqual(rows[-1]["reason"], "time")
            self.assertEqual(len(events(rows, "quan_end")), 1)


class GatherRoiKhoQuan(unittest.TestCase):
    """Luật gather (Minh) đi qua kho vào quán: hái, ngất, giỏ đầy."""

    def test_hai_nut_mat_nuoc_vao_kho(self):
        with Workdir() as w:
            sc = {"nodes": [{"id": "N1", "kind": "bong_sung", "pos": [50, 0]}],
                  "random_fish": False, "player": {"pos": [50, 0]}, "time_left_ticks": 5}
            code, err, inv, out = gather_to_inventory(w, sc, frames({"tick": 0, "interact": True}), 100)
            self.assertEqual(code, 0, err)
            self.assertEqual(len(events(read_jsonl(out), "gather")), 1)
            self.assertEqual(saved_counts(inv), {"bong_sung": 1})
            code, err, q = quan_from_inventory(w, inv)
            self.assertEqual(code, 0, err)
            self.assertEqual(counts(snapshots(read_jsonl(q))[0]["stock"]), {"bong_sung": 1})

    def test_ngat_mat_gio_kho_rong(self):
        """Máu về 0 -> faint, gather_end reason fainted, giỏ mất hết, kho rỗng."""
        with Workdir() as w:
            sc = {"hold": hold("ca_loc", "bong_sung"), "random_fish": False,
                  "player": {"pos": [50, 15], "oxygen_ticks": 0, "hp": 1}}
            code, err, inv, out = gather_to_inventory(w, sc, frames(), 600)
            self.assertEqual(code, 0, err)
            end = events(read_jsonl(out), "gather_end")
            self.assertEqual(len(end), 1)
            self.assertEqual(end[0]["data"]["reason"], "fainted")
            self.assertEqual(read(inv), {"items": [] if V12 else {}})
            code, err, q = quan_from_inventory(w, inv)
            self.assertEqual(code, 0, err)
            self.assertEqual(counts(snapshots(read_jsonl(q))[0]["stock"]), {})

    def test_gio_day_khong_nhat_them(self):
        cap = tuning()["gather"]["hold_capacity"]
        with Workdir() as w:
            sc = {"hold": hold(*(["ca_loc"] * cap)),
                  "nodes": [{"id": "N1", "kind": "bong_sung", "pos": [50, 0]}],
                  "random_fish": False, "player": {"pos": [50, 0]}, "time_left_ticks": 5}
            code, err, inv, out = gather_to_inventory(w, sc, frames({"tick": 0, "interact": True}), 100)
            self.assertEqual(code, 0, err)
            self.assertEqual(len(events(read_jsonl(out), "hold_full")), 1)
            self.assertEqual(saved_counts(inv), {"ca_loc": cap})


class CanLoiQuan(unittest.TestCase):
    """Cần quan lát 3-4 (Hải). Điền khi luật khách/món/tiền được chốt trong PRD-0."""

    @unittest.skip("Chờ sim/quan lát 3-4 và công thức tiền/boa/uy tín (PRD-0 mục F)")
    def test_khach_an_tru_kho_va_tra_tien(self):
        """Gather -> kho -> quan: phục vụ một món thì kho giảm đúng công thức, money/earned tăng, có paid."""

    @unittest.skip("Chờ sim/quan lát 3-4")
    def test_giu_cho_nguyen_lieu_khong_vuot_kho(self):
        """Tổng nguyên liệu giữ chỗ cho khách không bao giờ vượt stock."""


if __name__ == "__main__":
    unittest.main()
