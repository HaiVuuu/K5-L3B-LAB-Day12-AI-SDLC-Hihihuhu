"""Lệnh nhóm: kiểm luật gather, chạy từ thư mục bất kỳ."""

from pathlib import Path
import sys
import unittest


def main():
    root = Path(__file__).resolve().parents[1]
    sys.path[:0] = [str(root / "tests"), str(root)]
    suite = unittest.defaultTestLoader.discover(str(root / "tests"), pattern="test_gather.py")
    return 0 if unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
