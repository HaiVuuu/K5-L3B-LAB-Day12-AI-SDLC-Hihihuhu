"""Kho v1.0/v1.1 đếm theo kind; v1.2 dùng cá thể {id,kind,fresh}.

Đọc: từ chối sai schema / id lạ / số âm (BadInput -> mã 2).
Ghi: kho đếm bỏ lượng 0; kho cá thể giữ cả hàng ươn. Dùng file tạm rồi thay nguyên tử.
"""

import json
import os
import tempfile
import math
from fractions import Fraction

from .errors import BadInput
from .ids import sort_by_id

KINDS_P1 = ("ca_loc", "ca_linh", "bong_dien_dien", "bong_sung")
KINDS_P2 = (*KINDS_P1, "ca_keo", "keo_neo")
FRESH_SCALE = 240  # Đơn vị biểu diễn được Ticket-03 gợi ý, không phải số tuning gameplay.


def inventory_version(contract_version=None):
    """Caller có thể chỉ rõ phiên bản; mặc định theo manifest đang chạy, không đoán từ file kho."""
    if contract_version is None:
        from .contract import DEFAULT_PATH
        try:
            with open(DEFAULT_PATH, encoding="utf-8") as source:
                contract_version = json.load(source)["contract_version"]
        except (OSError, ValueError, KeyError, TypeError) as error:
            raise BadInput(f"không đọc được contract_version: {error}")
    if contract_version not in ("1.0", "1.1", "1.2"):
        raise BadInput(f"contract_version chưa hỗ trợ: {contract_version}")
    return contract_version


def validate_instances(items, kinds=KINDS_P2):
    if not isinstance(items, list):
        raise BadInput("items v1.2 phải là mảng cá thể, không nhận kho đếm")
    seen, result = set(), []
    for item in items:
        if not isinstance(item, dict) or set(item) != {"id", "kind", "fresh"}:
            raise BadInput("cá thể cần đúng id,kind,fresh")
        ident, kind, fresh = item["id"], item["kind"], item["fresh"]
        if not isinstance(ident, str) or not ident or ident in seen:
            raise BadInput("id cá thể phải là chuỗi khác rỗng và duy nhất")
        if not isinstance(kind, str) or kind not in kinds:
            raise BadInput(f"nguyên liệu lạ: {kind!r}")
        if isinstance(fresh, bool) or not isinstance(fresh, (int, float)) or not 0 <= fresh <= 100:
            raise BadInput("fresh phải hữu hạn trong [0,100]")
        seen.add(ident)
        result.append({"id": ident, "kind": kind, "fresh": fresh})
    return result


def validate_items(items, kinds=KINDS_P2, *, contract_version=None):
    if inventory_version(contract_version) == "1.2":
        return validate_instances(items, kinds)
    if not isinstance(items, dict):
        raise BadInput("items phải là object")
    out = {}
    for k, v in items.items():
        if k not in kinds:
            raise BadInput(f"nguyên liệu lạ: {k}")
        if isinstance(v, bool) or not isinstance(v, int) or v < 0:
            raise BadInput(f"số lượng không hợp lệ cho {k}: {v!r}")
        if v > 0:
            out[k] = v
    return out


def read_inventory(path: str, kinds=KINDS_P2, *, contract_version=None):
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được file kho {path}: {e}")
    if not isinstance(data, dict) or set(data.keys()) != {"items"}:
        raise BadInput("file kho chỉ được có khóa gốc 'items'")
    items = validate_items(data["items"], kinds, contract_version=contract_version)
    return sort_by_id(items) if isinstance(items, list) else items


def hold_to_items(hold: list, *, contract_version=None):
    """Hold theo thứ tự nhặt -> kho đếm v1.1 hoặc list cá thể sắp ID v1.2."""
    if inventory_version(contract_version) == "1.2":
        return sort_by_id(validate_instances(hold))
    counts = {}
    for k in hold:
        counts[k] = counts.get(k, 0) + 1
    return {k: counts[k] for k in sorted(counts)}


def write_inventory(path: str, items, *, contract_version=None):
    items = validate_items(items, contract_version=contract_version)
    items = sort_by_id(items) if isinstance(items, list) else {k: items[k] for k in sorted(items)}
    d = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(prefix=".inv-", suffix=".tmp", dir=d)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            json.dump({"items": items}, f, ensure_ascii=False, separators=(",", ":"))
            f.write("\n")
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def fresh_units(value):
    """Chuẩn 100/30/97.5 dùng số nguyên; fixture thập phân khác giữ phần hữu tỉ, không lượng tử hóa."""
    units = Fraction(str(value)) * FRESH_SCALE
    return units.numerator if units.denominator == 1 else units


def fresh_value(units, spoiled_below):
    """Xuất số JSON đủ chính xác, giữ phía ngưỡng và tránh đọc lại làm ươn sớm một tick."""
    exact = Fraction(units, FRESH_SCALE)
    value = float(exact)
    if Fraction(str(value)) < exact:
        value = math.nextafter(value, math.inf)
    if exact < Fraction(str(spoiled_below)) and value >= spoiled_below:
        value = math.nextafter(float(spoiled_below), -math.inf)
    return value


class FreshnessTracker:
    """Bộ số chính xác dùng chung cho hold/stock; chỉ caller gọi khi gameplay thực sự chạy."""
    def __init__(self, tuning):
        self.config = tuning["freshness"]
        self.hz = tuning["tick_hz"]
        self.units = {}

    def decay(self, items, *, location, rate):
        events = []
        decrement = Fraction(fresh_units(rate), self.hz)
        if decrement.denominator == 1:
            decrement = decrement.numerator
        threshold = fresh_units(self.config["spoiled_below"])
        living = {item["id"] for item in items}
        self.units = {key: value for key, value in self.units.items() if key in living}
        for item in sort_by_id(items):
            ident = item["id"]
            before = self.units[ident] if ident in self.units else fresh_units(item["fresh"])
            after = max(0, before - decrement)
            self.units[ident] = after
            item["fresh"] = fresh_value(after, self.config["spoiled_below"])
            if before >= threshold > after:
                events.append(("spoiled", {"item_id": ident, "kind": item["kind"], "location": location}))
        return events
