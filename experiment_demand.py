#!/usr/bin/env python3
"""需要面の実走。保存・tick・繰り返し回避・出口。"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from roleplay_engine import make_demo_engine


def run() -> dict:
    cases = []
    eng = make_demo_engine()
    a0 = eng.chars["Alice"].hash_a0

    s1 = eng.user_says("お前、本当に俺を信用してるのか？", speaker="Marisa", target="Alice")
    cases.append({"id": "event", "ok": s1["chosen"] == "認める"})

    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "s.json"
        eng.save(path)
        other = make_demo_engine()
        loaded = other.load(path)
        cases.append({
            "id": "save_load",
            "ok": loaded["ok"]
            and abs(other.zeta_of("Alice", "Marisa").trust - 0.51) < 1e-9
            and other.chars["Alice"].hash_a0 == a0,
        })

    t = eng.tick()
    cases.append({"id": "tick", "ok": t["commit"]["event"]["speaker"] == "Marisa" and t["ok"]})

    x = make_demo_engine()
    a = x.user_says("助けてくれ", speaker="Marisa", target="Alice")
    b = x.user_says("助けてくれ", speaker="Marisa", target="Alice")
    cases.append({"id": "no_clone", "ok": a["utterance"] != b["utterance"]})

    e = make_demo_engine().enter("取引", location="森の奥の空き地", scene_id="forest-deal")
    cases.append({"id": "exit", "ok": e["ok"] and e["hash_a_intact"]})

    bad = make_demo_engine().enter("紅魔館")
    cases.append({"id": "no_widen", "ok": not bad["ok"]})

    st = eng.status()
    cases.append({"id": "status", "ok": st["intact"]["Alice"] and st["intact"]["World"]})

    out = {"passed": all(c["ok"] for c in cases), "cases": cases}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return out


if __name__ == "__main__":
    dest = Path(__file__).resolve().parent / "demand_result.json"
    out = run()
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print("wrote", dest)
    raise SystemExit(0 if out["passed"] else 1)
