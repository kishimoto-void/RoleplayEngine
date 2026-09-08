#!/usr/bin/env python3
"""魔理沙の舞台で自然に場が動くかの実走。"""
from __future__ import annotations

import json
from pathlib import Path

from roleplay_engine import make_demo_engine
from stage_marisa import natural_turn, suggest


def run() -> dict:
    cases = []
    print("suggest", suggest("神社寄ろうぜ"))
    cases.append({"id": "cue", "ok": suggest("神社寄ろうぜ")["scene_id"] == "hakurei-shrine"})

    eng = make_demo_engine()
    out = natural_turn(eng, "ちょっと神社寄るぜ", speaker="Marisa")
    print("scene", out["scene"], out["location"])
    print("play ", out["step"]["utterance"])
    print("facts", out["world_facts"])
    cases.append({"id": "move", "ok": out["scene"] == "hakurei-shrine" and out["hash_a_intact"]})

    shop = natural_turn(eng, "あの本、いつ返すんだよ", speaker="Marisa", jump=True)
    print("shop", shop["scene"], shop["stage"].get("hint", {}).get("event"))
    cases.append({"id": "event", "ok": shop["scene"] == "kirisame-house"})

    report = {"passed": all(c["ok"] for c in cases), "cases": cases}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return report


if __name__ == "__main__":
    dest = Path(__file__).resolve().parent / "stage_result.json"
    out = run()
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    raise SystemExit(0 if out["passed"] else 1)
