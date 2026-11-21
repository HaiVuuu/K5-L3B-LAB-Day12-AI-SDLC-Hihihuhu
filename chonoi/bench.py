"""Đo FPS cảnh lặn thật trong trình duyệt headless (Chrome/Chromium/Edge), chỉ dùng thư viện chuẩn.

    python3 -m chonoi.bench --seed 42 --duration 30 --out bench.json

Chạy cảnh gather (seed cho trước) qua đúng client `web/index.html` ở 1280×720, làm nóng 3s rồi đo `duration` giây
bằng requestAnimationFrame. Xuất {avg_fps, p1_low_fps, frames, measured_s, load_ms}:
- p1_low_fps: FPS trung bình của 1% khung chậm nhất.
- load_ms: từ lúc lệnh bắt đầu tới khung đầu tiên vẽ có snapshot (gồm khởi động trình duyệt).
Không có trình duyệt hoặc quá hạn -> mã 1, không ghi file (không thay bằng số headless).
Đặt CHONOI_BROWSER=<đường dẫn> để chọn trình duyệt.
"""

import argparse
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from http.server import ThreadingHTTPServer

from .contract import load_contract
from .live import LiveGame, _Handler

MAX_BENCH_BODY = 2_000_000
BROWSERS = ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome", "msedge", "microsoft-edge")
BROWSER_PATHS = (
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
)


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage(sys.stderr)
        sys.stderr.write(f"lỗi: {message}\n")
        sys.exit(2)


def summarize(dts_ms):
    """Khoảng cách khung (ms) -> 4 trường FPS của bench.json."""
    frames = len(dts_ms)
    total_ms = sum(dts_ms)
    worst = sorted(dts_ms, reverse=True)[:max(1, frames // 100)]
    return {
        "avg_fps": round(frames * 1000 / total_ms, 2),
        "p1_low_fps": round(len(worst) * 1000 / sum(worst), 2),
        "frames": frames,
        "measured_s": round(total_ms / 1000, 3),
    }


def find_browser():
    env = os.environ.get("CHONOI_BROWSER")
    if env:
        return env
    for name in BROWSERS:
        found = shutil.which(name)
        if found:
            return found
    return next((p for p in BROWSER_PATHS if os.path.isfile(p)), None)


class _QuietServer(ThreadingHTTPServer):
    def handle_error(self, request, client_address):  # trình duyệt bị tắt giữa chừng: reset kết nối là bình thường
        pass


class _BenchHandler(_Handler):
    done = None    # threading.Event, gán trên lớp con
    result = None  # dict {"ready_at": float, "dts": [...]}

    def do_POST(self):
        path = self.path.split("?", 1)[0]
        if path not in ("/bench", "/bench/ready"):
            return super().do_POST()
        try:
            n = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            n = -1
        if not 0 <= n <= MAX_BENCH_BODY:
            return self._send(400, b'{"error":"body sai"}')
        raw = self.rfile.read(n) if n else b""
        if path == "/bench/ready":
            self.result.setdefault("ready_at", time.perf_counter())
        else:
            try:
                dts = json.loads(raw.decode("utf-8"))["dts"]
                if not dts or not all(isinstance(x, (int, float)) and math.isfinite(x) and x > 0 for x in dts):
                    raise ValueError("dts rỗng hoặc sai")
            except (ValueError, KeyError, TypeError, UnicodeDecodeError) as e:
                return self._send(400, json.dumps({"error": str(e)}).encode("utf-8"))
            self.result["dts"] = dts
            self.done.set()
        self._send(200, b'{"ok":true}')


def run_bench(seed, duration, warmup, browser, timeout):
    """Trả dict bench.json. Raise RuntimeError nếu trình duyệt không báo kết quả kịp."""
    t0 = time.perf_counter()
    game = LiveGame("gather", load_contract()["tuning"], {}, seed, menu=False)
    state = {"done": threading.Event(), "result": {}}
    handler = type("BenchHandler", (_BenchHandler,), {"game": game, **state})
    httpd = _QuietServer(("127.0.0.1", 0), handler)
    httpd.daemon_threads = True
    url = f"http://127.0.0.1:{httpd.server_address[1]}/?bench={duration}&warmup={warmup}"
    profile = tempfile.mkdtemp(prefix="chonoi-bench-")
    game.start()
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    proc = subprocess.Popen(
        [browser, "--headless=new", "--window-size=1280,720", "--no-first-run", "--no-default-browser-check",
         "--disable-extensions", "--disable-background-timer-throttling", "--disable-renderer-backgrounding",
         "--disable-backgrounding-occluded-windows", f"--user-data-dir={profile}", url],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        if not state["done"].wait(timeout):
            raise RuntimeError(f"trình duyệt không gửi kết quả sau {timeout:.0f}s")
    finally:
        proc.terminate()
        try:
            proc.wait(5)
        except subprocess.TimeoutExpired:
            proc.kill()
        httpd.shutdown()
        httpd.server_close()
        game.stop()
        shutil.rmtree(profile, ignore_errors=True)
    out = summarize(state["result"]["dts"])
    out["load_ms"] = round((state["result"]["ready_at"] - t0) * 1000)
    return out


def main(argv=None) -> int:
    p = _Parser(prog="chonoi.bench", description="Đo FPS cảnh lặn 1280×720 trong trình duyệt headless.")
    p.add_argument("--seed", required=True, type=int)
    p.add_argument("--duration", required=True, type=float, help="giây đo, sau làm nóng")
    p.add_argument("--out", required=True)
    p.add_argument("--warmup", type=float, default=3.0)
    p.add_argument("--timeout", type=float, help="giây chờ tối đa, mặc định duration + warmup + 60")
    a = p.parse_args(argv)
    if not (math.isfinite(a.duration) and a.duration > 0) or not (math.isfinite(a.warmup) and a.warmup >= 0):
        sys.stderr.write("đầu vào sai: --duration phải > 0, --warmup phải >= 0\n")
        return 2
    browser = find_browser()
    if not browser:
        sys.stderr.write("không tìm thấy Chrome/Chromium/Edge; đặt CHONOI_BROWSER=<đường dẫn>\n")
        return 1
    try:
        report = run_bench(a.seed, a.duration, a.warmup, browser, a.timeout or a.duration + a.warmup + 60)
        with open(a.out, "w", encoding="utf-8", newline="\n") as f:
            json.dump(report, f, indent=2)
            f.write("\n")
    except (RuntimeError, OSError) as e:
        sys.stderr.write(f"bench lỗi: {e}\n")
        return 1
    print(json.dumps(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
