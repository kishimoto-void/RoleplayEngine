#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from index_stage import rig
from roleplay_engine import make_demo_engine
from stage_marisa import follow


def run() -> dict:
    eng = make_demo_engine()
    follow(eng, "ちょっと神社寄るぜ", jump=False)
    out = rig(eng)
    print("stage", out["stage"]["address"], out["stage"]["location"])
    print("props", out["cast"]["props"])
    print("cast", [(c["name"], c["立場"], c["小道具"]) for c in out["cast"]["characters"]])
    cases = [
        {"id": "gamma", "ok": out["stage"]["address"]["topic"] == "hakurei-shrine"},
        {"id": "delta_prop", "ok": "茶" in out["cast"]["props"]},
        {"id": "delta_char", "ok": any(c["立場"].startswith("Marisa") for c in out["cast"]["characters"])},
        {"id": "intact", "ok": out["hash_a_intact"]},
        {"id": "not_fact", "ok": not any("茶" in f for f in out["world_facts"])},
    ]
    report = {"passed": all(c["ok"] for c in cases), "cases": cases}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return report


if __name__ == "__main__":
    dest = Path(__file__).resolve().parent / "index_stage_result.json"
    out = run()
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    raise SystemExit(0 if out["passed"] else 1)
