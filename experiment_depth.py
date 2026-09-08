#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from depth_index import remember
from roleplay_engine import make_demo_engine
from stage_marisa import follow


def run() -> dict:
    eng = make_demo_engine()
    follow(eng, "ちょっと神社寄るぜ", jump=False)
    out = remember(eng)
    d = out["depth"]
    print("γ", d["gamma"])
    print("Δ", d["delta"])
    print("Δ2", d["delta2"])
    cases = [
        {"id": "know", "ok": "hakurei-shrine" in out["places"]["gamma_topics"]},
        {"id": "match", "ok": d["gamma"]["match"]},
        {"id": "prop", "ok": "茶" in d["delta"]["props"]},
        {"id": "rel", "ok": d["delta2"] and d["delta2"][0]["next"] == "縁側で茶"},
        {"id": "no_store", "ok": d["store"] is False and out["hash_a_intact"]},
    ]
    report = {"passed": all(c["ok"] for c in cases), "cases": cases}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return report


if __name__ == "__main__":
    dest = Path(__file__).resolve().parent / "depth_result.json"
    out = run()
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    raise SystemExit(0 if out["passed"] else 1)
