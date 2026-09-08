#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from demo import SAMPLE, run_demo


def run() -> dict:
    out = run_demo(SAMPLE)
    print(out["script"])
    cases = [
        {"id": "script", "ok": "【スタート】" in out["script"] and "【帰結】" in out["script"]},
        {"id": "unknown", "ok": bool((out.get("material") or {}).get("unknown"))},
        {"id": "no_world", "ok": not out["world_written"]},
    ]
    report = {"passed": all(c["ok"] for c in cases), "cases": cases}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return report


if __name__ == "__main__":
    dest = Path(__file__).resolve().parent / "demo_result.json"
    out = run()
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    raise SystemExit(0 if out["passed"] else 1)
