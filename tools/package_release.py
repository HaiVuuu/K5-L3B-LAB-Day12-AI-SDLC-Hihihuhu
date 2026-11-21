"""Đóng gói đúng một commit Git (không lấy file chưa commit), không tạo tag/publish."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile


ROOT = Path(__file__).resolve().parents[1]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ref", default="HEAD")
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    revision = subprocess.check_output(
        ["git", "rev-parse", "--verify", "--end-of-options", args.ref + "^{commit}"], cwd=ROOT, text=True).strip()
    out = Path(args.out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    prefix = "chonoi-v1.0.0/"
    contract = json.loads(subprocess.check_output(["git", "show", revision + ":game.contract.json"], cwd=ROOT, text=True))
    if contract["contract_version"] != "1.3":
        raise RuntimeError("commit đóng gói chưa có contract v1.3")
    subprocess.run(["git", "archive", "--format=zip", "--prefix=" + prefix,
                    "--output=" + str(out), revision], cwd=ROOT, check=True)
    with zipfile.ZipFile(out) as archive:
        contract = json.loads(archive.read(prefix + "game.contract.json"))
        required = ["README.md", "CREDITS.md", "game.contract.json", "chonoi/live.py", "chonoi/web/index.html"]
        for path in required:
            if prefix + path not in archive.namelist():
                raise RuntimeError("thiếu file trong gói: " + path)
    manifest = {"commit": revision, "contract_version": contract["contract_version"],
                "archive": out.name, "sha256": hashlib.sha256(out.read_bytes()).hexdigest(),
                "bytes": out.stat().st_size, "status": "candidate; not a published release"}
    receipt = out.with_suffix(out.suffix + ".json")
    receipt.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
