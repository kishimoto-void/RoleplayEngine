#!/usr/bin/env python3
"""視点。同じ種を、見る側だけ変えて引く。

World     場所と場。所持は見ない。
人物      自分の所持と立場。他人の道具は持たない。
audience  今見える場と誰がいるか。信頼の数値は出さない。
"""
from __future__ import annotations

from typing import Any

from roleplay_engine import CapsuleRoleplayEngine
from vine import study

EYES = ("World", "Alice", "Marisa", "audience")


def _name(eye: str) -> str:
    return {"アリス": "Alice", "魔理沙": "Marisa", "世界": "World", "客": "audience"}.get(eye, eye)


def through(vine: dict[str, Any], eye: str, present: list[str] | None = None) -> dict[str, Any]:
    who = _name(eye)
    base = {
        "eye": who,
        "seed": vine.get("seed"),
        "gamma": vine.get("gamma"),
        "delta": {"場": [], "所持": {}, "events": []},
        "delta2": [],
        "contaminated": bool(vine.get("contaminated")),
        "store": False,
    }
    floor = list((vine.get("delta") or {}).get("場") or [])
    held = dict((vine.get("delta") or {}).get("所持") or {})
    events = list((vine.get("delta") or {}).get("events") or [])
    if who == "World":
        base["delta"]["場"] = floor
        base["delta"]["events"] = events
        return base
    if who == "audience":
        base["delta"]["場"] = floor
        base["delta"]["events"] = events
        base["delta2"] = [{"present": list(present or held.keys()), "next": None, "writes": False}]
        return base
    base["delta"]["場"] = floor
    if who in held:
        base["delta"]["所持"] = {who: list(held[who])}
    elif who in ("Alice", "Marisa"):
        base["delta"]["所持"] = {who: []}
    for row in vine.get("delta2") or []:
        if row.get("from") == who or row.get("to") == who or row.get("actor") == who:
            copied = dict(row)
            if who != "audience":
                base["delta2"].append(copied)
    if not base["delta2"]:
        stance_rows = [r for r in (vine.get("delta2") or []) if r.get("from") == who]
        base["delta2"] = stance_rows
    return base


def look(eng: CapsuleRoleplayEngine, seed: str, eye: str) -> dict[str, Any]:
    vine = study(eng, seed)
    present = [n for n in eng.scene.participants if n in eng.chars]
    view = through(vine, eye, present=present)
    view["hash_a_intact"] = bool(vine.get("hash_a_intact", True))
    # 他人の所持が混ざっていない
    who = _name(eye)
    others = [n for n in (view["delta"]["所持"] or {}) if n != who]
    if who in ("Alice", "Marisa") and others:
        view["contaminated"] = True
    return view


def compare(eng: CapsuleRoleplayEngine, seed: str) -> dict[str, Any]:
    """同じ種を四つの視点で見る。記憶は増やさない。"""
    views = {eye: look(eng, seed, eye) for eye in EYES}
    return {
        "seed": seed,
        "views": views,
        "same_gamma": len({str((v.get("gamma") or {}).get("topic")) for v in views.values()}) == 1,
        "store": False,
    }
