#!/usr/bin/env python3
"""記憶深度。

γ   場所の知識。住所。
Δ   その場所の出来事と小道具。深さ 1。
Δ2  γ が当たったとき、Δ の人物関係から次を出す。深さ 2。

Δ2 は格納層ではない。読む面。Capsule に足さない。
"""
from __future__ import annotations

from typing import Any

from hole_play import _delta_rows, _gamma_rows
from index_stage import props_for, stamp_cast, stamp_stage
from roleplay_engine import CapsuleRoleplayEngine
from stage_marisa import EVENTS, PLACES, mount


def know_places(eng: CapsuleRoleplayEngine, authorize: bool = True) -> dict[str, Any]:
    """場所の知識を World の γ index に載せる。今いる場所以外も知る。"""
    mount(eng)
    frozen = eng.world.hash_a0
    known = []
    current = dict(eng.scene.__dict__)
    for place in PLACES:
        filt = {
            "time_label": eng.scene.time_label,
            "project": "World",
            "topic": place.scene_id,
        }
        eng.world.rt.bind(filt)
        pkt = {
            "gamma": filt,
            "delta": [{"field": "状態", "new_value": f"場所={place.name}"}],
            "is": [{"field": "状態", "value": f"場所={place.name}"}],
        }
        report = eng.world.rt.commit(pkt, identity=1.0, authorize=authorize)
        known.append(
            {
                "topic": place.scene_id,
                "name": place.name,
                "ok": bool(report.get("committed")),
            }
        )
    eng.world.bind(eng.scene)
    if eng.world.box.hash_a() != frozen:
        raise RuntimeError("Hash-A moved on know_places")
    _ = current
    return {
        "ok": all(row["ok"] for row in known),
        "places": known,
        "gamma_topics": sorted({row["topic"] for row in known}),
        "hash_a_moved": False,
    }


def remember_here(eng: CapsuleRoleplayEngine, authorize: bool = True) -> dict[str, Any]:
    """今の γ に、出来事と小道具を Δ として残す。"""
    stamp_stage(eng, authorize=authorize)
    stamped = stamp_cast(eng, authorize=authorize)
    hooks = [e for e in EVENTS if e.place == eng.scene.scene_id]
    if hooks and "Marisa" in eng.chars:
        ch = eng.chars["Marisa"]
        filt = {
            "time_label": eng.scene.time_label,
            "project": "Marisa",
            "topic": eng.scene.scene_id,
        }
        ch.rt.bind(filt)
        hook = hooks[0]
        frozen = ch.hash_a0
        ch.rt.commit(
            {
                "gamma": filt,
                "delta": [{"field": "課題", "new_value": hook.hook}],
                "is": [{"field": "課題", "value": hook.hook}],
            },
            identity=1.0,
            authorize=authorize,
        )
        if ch.box.hash_a() != frozen:
            raise RuntimeError("Hash-A moved on remember_here")
    return {
        "ok": True,
        "scene_id": eng.scene.scene_id,
        "props": stamped.get("props") or props_for(eng.scene.scene_id, list(eng.chars)),
        "events": [{"event_id": e.event_id, "hook": e.hook} for e in hooks],
        "hash_a_moved": False,
    }


def _latest(deltas: list[dict], field: str) -> str:
    rows = [d for d in deltas if d.get("field") == field]
    return str(rows[-1]["new_value"]) if rows else ""


def depth_view(eng: CapsuleRoleplayEngine) -> dict[str, Any]:
    """γ が当たれば Δ を読み、人物関係から Δ2 を出す。"""
    topic = eng.scene.scene_id
    world_hits = []
    for place in PLACES:
        filt = {
            "time_label": eng.scene.time_label,
            "project": "World",
            "topic": place.scene_id,
        }
        rows = _gamma_rows(eng.world.box, filt)
        if rows:
            world_hits.append(place.scene_id)
    matched = topic in world_hits
    delta = {"props": [], "events": [], "people": []}
    delta2: list[dict[str, Any]] = []
    if matched:
        present = [n for n in eng.scene.participants if n in eng.chars]
        for name in present:
            filt = {
                "time_label": eng.scene.time_label,
                "project": name,
                "topic": topic,
            }
            rows = _delta_rows(eng.chars[name].box, filt)
            stance = _latest(rows, "立場")
            state = _latest(rows, "状態")
            task = _latest(rows, "課題")
            held = []
            if state.startswith("小道具="):
                held = [x for x in state.split("=", 1)[1].split(",") if x]
            delta["people"].append({"name": name, "立場": stance, "課題": task, "小道具": held})
            for item in held:
                if item not in delta["props"]:
                    delta["props"].append(item)
            if task and task not in delta["events"]:
                delta["events"].append(task)
        for i, a in enumerate(present):
            for b in present[i + 1 :]:
                z = eng.zeta_of(a, b)
                shared = [p for p in props_for(topic, [a, b]) if p in (delta["props"] or props_for(topic, present))]
                nxt = "間を取る"
                if "茶" in delta["props"] or "茶" in shared:
                    nxt = "縁側で茶"
                elif "魔導書" in delta["props"]:
                    nxt = "借り物の話"
                elif "キノコ籠" in delta["props"]:
                    nxt = "採取を続ける"
                elif z.trust < 0.35:
                    nxt = "距離を測る"
                delta2.append(
                    {
                        "from": a,
                        "to": b,
                        "trust": z.trust,
                        "props": shared,
                        "next": nxt,
                        "writes": False,
                    }
                )
    return {
        "form": "γ → Δ → Δ2",
        "gamma": {
            "topic": topic,
            "known": world_hits,
            "match": matched,
        },
        "delta": delta,
        "delta2": delta2,
        "store": False,
        "hash_a_intact": all(ch.intact() for ch in eng.chars.values()) and eng.world.intact(),
    }


def remember(eng: CapsuleRoleplayEngine) -> dict[str, Any]:
    places = know_places(eng)
    here = remember_here(eng)
    view = depth_view(eng)
    return {
        "ok": bool(places.get("ok") and here.get("ok") and view["gamma"]["match"]),
        "places": places,
        "here": here,
        "depth": view,
        "hash_a_intact": view["hash_a_intact"],
        "world_facts": list(eng.world.facts),
    }
