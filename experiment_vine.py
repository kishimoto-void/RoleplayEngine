#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from roleplay_engine import make_demo_engine
from stage_marisa import follow
from vine import study


def run() -> dict:
    eng = make_demo_engine()
    follow(eng, "ちょっと神社寄るぜ", jump=False)
    tea = study(eng, "茶")
    shop = study(eng, "霧雨魔法店")
    print("tea", tea["gamma"], tea["delta"]["場"])
    print("shop", shop["gamma"], shop["delta"]["場"])
    cases = [
        {"id": "tea_place", "ok": tea["gamma"]["topic"] == "hakurei-shrine"},
        {"id": "no_book", "ok": "魔導書" not in str(tea["delta"])},
        {"id": "shop_no_tea", "ok": "茶" not in shop["delta"]["場"]},
        {"id": "clean", "ok": not tea["contaminated"] and not shop["contaminated"]},
    ]
    report = {"passed": all(c["ok"] for c in cases), "cases": cases}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return report


if __name__ == "__main__":
    dest = Path(__file__).resolve().parent / "vine_result.json"
    out = run()
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    raise SystemExit(0 if out["passed"] else 1)
