#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from eye import compare
from roleplay_engine import make_demo_engine
from stage_marisa import follow


def run() -> dict:
    eng = make_demo_engine()
    follow(eng, "ちょっと神社寄るぜ", jump=False)
    out = compare(eng, "茶")
    for eye, view in out["views"].items():
        print(eye, view["delta"])
    cases = [
        {"id": "same_place", "ok": out["same_gamma"]},
        {"id": "world_empty_hands", "ok": out["views"]["World"]["delta"]["所持"] == {}},
        {"id": "split_kit", "ok": "ミニ八卦炉" not in str(out["views"]["Alice"]["delta"]["所持"])},
        {"id": "no_store", "ok": out["store"] is False},
    ]
    report = {"passed": all(c["ok"] for c in cases), "cases": cases}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return report


if __name__ == "__main__":
    dest = Path(__file__).resolve().parent / "eye_result.json"
    out = run()
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    raise SystemExit(0 if out["passed"] else 1)
