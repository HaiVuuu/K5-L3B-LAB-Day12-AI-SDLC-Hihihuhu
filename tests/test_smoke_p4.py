"""Smoke Phase 4 (QA, hộp đen): `bench_cmd` và `soak_cmd` khai trong game.contract.json (Test Contract v1.3).

Chỉ chạy khi manifest có CẢ HAI khóa gốc `bench_cmd` và `soak_cmd`; trước đó tự bỏ qua với lý do rõ ràng.
Schema lấy từ docs/plan/phase-4.md (chưa có Ticket-04 trong repo), nên chỉ khẳng định những điều plan nêu thẳng:
- soak: `--seed N --days K --out soak.json` -> {days, days_completed, crashes, results[], duration_s}.
- bench: `--seed 42 --duration S --out bench.json` -> {avg_fps, p1_low_fps, frames, measured_s, load_ms}.
Các điều plan chưa nêu (nội dung từng phần tử `results[]`, ngưỡng fps, mã thoát khi tham số sai) KHÔNG đoán ở đây —
xem docs/verification/phase-4.md.

Chạy: python -m unittest discover -s tests -p test_smoke_p4.py -v
"""

import json
import os
import shlex
import subprocess
import unittest

from helpers import ROOT, Workdir, read_jsonl  # noqa: F401  (ROOT dùng để chạy lệnh đúng thư mục gốc repo)


def contract():
    with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as f:
        return json.load(f)


C = contract()
HAS_CMDS = isinstance(C.get("bench_cmd"), str) and isinstance(C.get("soak_cmd"), str) and C["bench_cmd"] and C["soak_cmd"]
SKIP = unittest.skipUnless(HAS_CMDS, "game.contract.json chưa có bench_cmd và soak_cmd (chưa lên v1.3) — chờ Integrator")


def run_cmd(key, *args, timeout=600):
    p = subprocess.run([*shlex.split(C[key]), *args], cwd=ROOT, capture_output=True, text=True, timeout=timeout)
    return p.returncode, p.stderr


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def is_num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


@SKIP
class Soak(unittest.TestCase):
    KEYS = {"days", "days_completed", "crashes", "results", "duration_s"}

    def test_schema_va_hoan_thanh_10_ngay(self):
        """Plan: 10 Ngày liên tục trong 1 tiến trình, không crash."""
        with Workdir() as w:
            out = w.path("soak.json")
            code, err = run_cmd("soak_cmd", "--seed", "7", "--days", "10", "--out", out)
            self.assertEqual(code, 0, err)
            s = load(out)
            self.assertTrue(self.KEYS <= set(s), set(s))
            self.assertEqual(s["days"], 10)
            self.assertEqual(s["days_completed"], 10)
            self.assertEqual(s["crashes"], 0)
            self.assertIsInstance(s["results"], list)
            self.assertEqual(len(s["results"]), 10)
            self.assertTrue(is_num(s["duration_s"]) and s["duration_s"] > 0)

    def test_so_ngay_tuy_chon(self):
        with Workdir() as w:
            out = w.path("soak.json")
            code, err = run_cmd("soak_cmd", "--seed", "7", "--days", "2", "--out", out)
            self.assertEqual(code, 0, err)
            s = load(out)
            self.assertEqual((s["days"], s["days_completed"], len(s["results"])), (2, 2, 2))

    def test_tat_dinh_theo_seed(self):
        """Cùng seed, cùng số ngày -> kết quả giống nhau (trừ duration_s là số đo đồng hồ thật)."""
        outs = []
        with Workdir() as w:
            for i in (1, 2):
                out = w.path(f"soak{i}.json")
                code, err = run_cmd("soak_cmd", "--seed", "7", "--days", "3", "--out", out)
                self.assertEqual(code, 0, err)
                s = load(out)
                s.pop("duration_s")
                outs.append(s)
        self.assertEqual(outs[0], outs[1])


@SKIP
class Bench(unittest.TestCase):
    KEYS = {"avg_fps", "p1_low_fps", "frames", "measured_s", "load_ms"}

    def test_schema(self):
        """Dùng --duration ngắn cho smoke; số liệu chuẩn (30 s) lưu ở docs/proof/phase-4/bench.json."""
        with Workdir() as w:
            out = w.path("bench.json")
            code, err = run_cmd("bench_cmd", "--seed", "42", "--duration", "2", "--out", out)
            self.assertEqual(code, 0, err)
            b = load(out)
            self.assertTrue(self.KEYS <= set(b), set(b))
            for k in ("avg_fps", "p1_low_fps", "measured_s", "load_ms"):
                self.assertTrue(is_num(b[k]) and b[k] >= 0, (k, b[k]))
            self.assertIsInstance(b["frames"], int)
            self.assertGreater(b["frames"], 0)
            self.assertLessEqual(b["p1_low_fps"], b["avg_fps"] + 1e-6, "1% thấp nhất không thể cao hơn trung bình")


class ChoTicket04(unittest.TestCase):
    """Ghi lại để không quên; chưa viết được chính xác vì chưa có Ticket-04."""

    @unittest.skip("Chờ Ticket-04: ngưỡng avg_fps/p1_low_fps đạt và mã thoát khi tham số sai của bench/soak")
    def test_nguong_va_tham_so_sai(self):
        pass


if __name__ == "__main__":
    unittest.main()
