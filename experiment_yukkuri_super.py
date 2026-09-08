#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from yukkuri_super import super_make


def run() -> dict:
    sample = "魔理沙が森でキノコを探してたら、霊夢に会って神社に行くことになった"
    dest = Path(__file__).resolve().parent / "yukkuri_super.txt"
    out = super_make(sample, out=dest)
    print(out["script"])
    print("panel", out["panel"])
    cases = [
        {"id": "title", "ok": "【タイトル】" in out["script"]},
        {"id": "end", "ok": "ゆっくりしていってね" in out["script"]},
        {"id": "unknown", "ok": "理由" in out["script"]},
        {"id": "export", "ok": dest.exists() and dest.stat().st_size > 0},
        {"id": "no_world", "ok": not out["panel"]["world_written"]},
    ]
    report = {"passed": all(c["ok"] for c in cases), "cases": cases, "export": str(dest)}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return report


if __name__ == "__main__":
    dest = Path(__file__).resolve().parent / "yukkuri_super_result.json"
    out = run()
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    raise SystemExit(0 if out["passed"] else 1)
