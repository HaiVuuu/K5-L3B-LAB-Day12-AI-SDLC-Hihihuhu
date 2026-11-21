"""Bench P4: phép tính FPS và mã thoát; không cần trình duyệt."""

import unittest
from unittest import mock

from chonoi import bench


class BenchTest(unittest.TestCase):
    def test_summarize_tinh_avg_va_1pct_low(self):
        dts = [10.0] * 99 + [100.0]
        out = bench.summarize(dts)
        self.assertEqual(out["frames"], 100)
        self.assertEqual(out["measured_s"], 1.09)
        self.assertAlmostEqual(out["avg_fps"], 100 / 1.09, places=1)
        self.assertEqual(out["p1_low_fps"], 10.0)

    def test_duration_khong_duong_tra_2(self):
        self.assertEqual(bench.main(["--seed", "42", "--duration", "0", "--out", "x.json"]), 2)

    def test_co_sai_tra_2(self):
        with self.assertRaises(SystemExit) as cm, mock.patch("sys.stderr"):
            bench.main(["--seed", "x", "--duration", "30", "--out", "x.json"])
        self.assertEqual(cm.exception.code, 2)

    def test_khong_co_trinh_duyet_tra_1_khong_ghi_file(self):
        with mock.patch.object(bench, "find_browser", return_value=None), mock.patch("sys.stderr"), \
                mock.patch.object(bench, "run_bench") as run:
            self.assertEqual(bench.main(["--seed", "42", "--duration", "30", "--out", "x.json"]), 1)
        run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
