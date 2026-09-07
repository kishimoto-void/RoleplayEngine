#!/usr/bin/env python3
"""場面帳の実走。用意・ hop・ジャンプ禁止。"""
from __future__ import annotations

import json
from pathlib import Path

from roleplay_engine import make_demo_engine


def run() -> dict:
    eng = make_demo_engine()
    cases = []
    print("book", eng.scenes())
    cases.append({"id": "book", "ok": {c["scene_id"] for c in eng.scenes()} >= {"forest-gate", "alice-house", "scarlet-mansion"}})

    a = eng.prepare("alice-house")
    print("prepare alice-house", a["ok"], eng.scene.location)
    frame = eng.frame_for("Alice")
    print("start", frame["start"])
    cases.append({"id": "prepare", "ok": a["ok"] and "七色の人形遣いの家" in frame["start"] and a["hash_a_intact"]})

    blocked = eng.prepare("scarlet-mansion", jump=False)
    print("no_route mansion", blocked)
    cases.append({"id": "no_route", "ok": blocked.get("reason") == "no_route"})

    staged = make_demo_engine().prepare("scarlet-mansion", jump=True)
    print("jump mansion", staged["ok"], "facts", staged["world_facts"])
    cases.append({"id": "jump_not_fact", "ok": staged["ok"] and not any("紅魔館に行った" in f for f in staged["world_facts"])})

    linked = make_demo_engine().prepare("kirisame-house", jump=False)
    print("route house", linked["ok"], linked.get("scene", {}).get("location"))
    cases.append({"id": "route", "ok": linked["ok"]})

    out = {"passed": all(c["ok"] for c in cases), "cases": cases}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return out


if __name__ == "__main__":
    dest = Path(__file__).resolve().parent / "scene_result.json"
    out = run()
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    raise SystemExit(0 if out["passed"] else 1)
