"""Kiểm điều kiện Phase 4 từ dữ liệu thật; không tạo số bench/soak, tag hoặc Release."""

import argparse
import json
import math
import os
from pathlib import Path
import shlex
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    parser.add_argument("--measure", action="store_true", help="chạy bench 30s và soak hai lần để kiểm tất định")
    args = parser.parse_args(argv)
    target = Path(args.out).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    logs = target.parent / "release-check-logs"
    logs.mkdir(exist_ok=True)
    checks = []
    contract = json.loads((ROOT / "game.contract.json").read_text())
    env = dict(os.environ, PYTHONPATH=str(ROOT / "tests") + os.pathsep + str(ROOT))

    def add(name, passed, detail):
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    def run(name, command):
        result = subprocess.run(command, cwd=ROOT, env=env, text=True, capture_output=True)
        content = "$ " + shlex.join(command) + "\n" + result.stdout + result.stderr + "\nexit_code=" + str(result.returncode)
        (logs / (name + ".txt")).write_text(
            "\n".join(line.rstrip() for line in content.splitlines()) + "\n", encoding="utf-8")
        return result.returncode == 0

    add("manifest", contract.get("contract_version") == "1.3" and
        all(isinstance(contract.get(k), str) and contract[k].strip() for k in ("bench_cmd", "soak_cmd")),
        "contract_version=1.3, bench_cmd và soak_cmd khác rỗng")
    add("team", run("team", [sys.executable, "tools/check_team.py"]), "xem release-check-logs/team.txt")
    sys.path.insert(0, str(ROOT / "tools"))
    from check_team import parse_team
    members = parse_team((ROOT / "TEAM.md").read_text())
    missing = [m["name"] for m in members if not m["handle"] or
               not (ROOT / "docs/members" / (m["handle"] + ".md")).is_file()]
    add("member_reflections", not missing, {"missing": missing})
    license_files = [p.name for p in ROOT.iterdir() if p.is_file() and p.name.upper() in
                     ("LICENSE", "LICENSE.MD", "LICENSE.TXT", "COPYING")]
    add("license_file", bool(license_files), {"found": license_files,
        "note": "Không tự gán giấy phép khi chưa được chủ mã nguồn xác nhận."})
    add("regression", run("regression", [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"]),
        "regression P1–P3 + test hiện có, log giữ cả skip và failure")
    modules = {"bench": (ROOT / "chonoi/bench.py").is_file(), "soak": (ROOT / "chonoi/soak.py").is_file()}
    for name, exists in modules.items():
        add(name + "_module", exists, "chonoi/" + name + ".py")

    measured = {}
    if args.measure and all(modules.values()):
        bench_path, soak_path = logs / "bench.json", logs / "soak.json"
        bench_ok = run("bench", [*shlex.split(contract["bench_cmd"]), "--seed", "42", "--duration", "30", "--out", str(bench_path)])
        if bench_ok:
            try:
                value = json.loads(bench_path.read_text())
                keys = {"avg_fps", "p1_low_fps", "frames", "measured_s", "load_ms"}
                bench_ok = set(value) == keys and all(
                    isinstance(value[k], (int, float)) and not isinstance(value[k], bool) and
                    math.isfinite(value[k]) and value[k] >= 0 for k in keys)
                bench_ok = bench_ok and isinstance(value["frames"], int) and value["frames"] > 0 and value["measured_s"] > 0
                measured["bench"] = value
                measured["reported_targets"] = {"avg_fps_ge_60": value["avg_fps"] >= 60,
                    "p1_low_fps_ge_30": value["p1_low_fps"] >= 30, "load_ms_le_10000": value["load_ms"] <= 10000}
            except (OSError, ValueError, KeyError, TypeError):
                bench_ok = False
        add("bench_execution_schema", bench_ok, "FPS/load là mốc báo cáo, không tự biến thành số đo giả")
        runs = []
        for i in range(2):
            path = soak_path if i == 0 else logs / "soak-repeat.json"
            passed = run("soak-" + str(i + 1), [*shlex.split(contract["soak_cmd"]), "--seed", "7", "--days", "10", "--out", str(path)])
            try:
                value = json.loads(path.read_text()) if passed else {}
                valid = value.get("days") == 10 and value.get("days_completed") == 10 and value.get("crashes") == 0
                results = value.get("results", [])
                valid = valid and isinstance(results, list) and len(results) == 10
                valid = valid and isinstance(value.get("duration_s"), (int, float)) and math.isfinite(value["duration_s"]) and value["duration_s"] >= 0
                for day, result in enumerate(results, 1):
                    valid = valid and result["day"] == day and result["earned"] >= 0 and 0 <= result["reputation"] <= 5
                    valid = valid and result["score"] == result["earned"] + contract["tuning"]["score"]["reputation_multiplier"] * math.floor(result["reputation"])
                runs.append({k: v for k, v in value.items() if k != "duration_s"})
            except (OSError, ValueError, KeyError, TypeError):
                valid = False
            add("soak_execution_" + str(i + 1), passed and valid, "10 Ngày, schema và điểm sau Shop")
        add("soak_deterministic", len(runs) == 2 and runs[0] == runs[1], "so gameplay, bỏ duration_s")
    else:
        add("measurements", False, "chưa chạy bench/soak thực; cần module của đồng đội và --measure")
    revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True)
    worktree = subprocess.run(["git", "status", "--short"], cwd=ROOT, text=True, capture_output=True)
    report = {"release": "v1.0.0", "commit": revision.stdout.strip() if revision.returncode == 0 else None,
              "worktree_status_at_check": worktree.stdout.splitlines(),
              "ready_for_team_release_review": all(c["passed"] for c in checks), "checks": checks, "measurements": measured,
              "remaining_manual_checks": ["clone sạch và UI cảnh báo/tương phản cao", "các thành viên xác nhận phản tư thật, Bảo hiện còn nháp", "bằng chứng QA đúng commit main", "review rồi cùng commit cho phase-4/v1.0.0"]}
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ready": report["ready_for_team_release_review"], "failed": [c["name"] for c in checks if not c["passed"]], "report": str(target)}, ensure_ascii=False))
    return 0 if report["ready_for_team_release_review"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
