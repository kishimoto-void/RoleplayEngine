#!/usr/bin/env python3
"""γ index を舞台装置に、Δ index をキャラと小道具にする。

新しい層は作らない。閉じた語のまま。
  γ  topic = 場面
  Δ  立場  = キャラ
  Δ  状態  = 小道具と場
  Δ  課題  = その場の用

Hash-A は触らない。発言は事実にしない。
"""
from __future__ import annotations

from dataclasses import asdict
from typing import Any

from hole_play import _delta_rows, _gamma_rows
from roleplay_engine import CapsuleRoleplayEngine
from stage_marisa import PLACES, mount

# 場面ごとの小道具。公式本文の写しではない。
PROPS = {
    "kirisame-house": ("箒", "ミニ八卦炉", "魔導書", "キノコ籠"),
    "forest-path": ("箒", "キノコ籠"),
    "forest-gate": ("箒",),
    "alice-house": ("箒", "人形"),
    "hakurei-shrine": ("箒", "茶"),
    "scarlet-mansion": ("箒", "借りたい本"),
    "forest-deal": ("箒",),
}

KIT = {
    "Marisa": ("箒", "ミニ八卦炉"),
    "Alice": ("人形",),
}


def _scene_filt(eng: CapsuleRoleplayEngine, project: str) -> dict[str, str]:
    return {
        "time_label": eng.scene.time_label,
        "project": project,
        "topic": eng.scene.scene_id,
    }


def scene_props(scene_id: str) -> list[str]:
    return list(PROPS.get(scene_id, ()))


def held_props(name: str) -> list[str]:
    return list(KIT.get(name, ()))


def props_for(scene_id: str, names: list[str] | None = None) -> list[str]:
    seen = []
    for item in scene_props(scene_id):
        if item not in seen:
            seen.append(item)
    for name in names or ():
        for item in held_props(name):
            if item not in seen:
                seen.append(item)
    return seen


def stamp_stage(eng: CapsuleRoleplayEngine, authorize: bool = True) -> dict[str, Any]:
    """今の Scene を γ 住所として着ける。舞台装置。"""
    mount(eng)
    frozen = {name: ch.hash_a0 for name, ch in eng.chars.items()}
    frozen["World"] = eng.world.hash_a0
    eng.world.bind(eng.scene)
    for ch in eng.chars.values():
        ch.bind_scene(eng.scene)
    wfilt = _scene_filt(eng, "World")
    floor = scene_props(eng.scene.scene_id)
    state = f"場所={eng.scene.location} / 場={','.join(floor)}"
    pkt = {
        "gamma": wfilt,
        "delta": [{"field": "状態", "new_value": state}],
        "is": [{"field": "状態", "value": state}],
    }
    report = eng.world.rt.commit(pkt, identity=1.0, authorize=authorize)
    moved = [n for n, h in frozen.items() if (eng.chars[n].hash_a0 if n != "World" else eng.world.hash_a0) != h]
    if eng.world.box.hash_a() != frozen["World"]:
        raise RuntimeError("Hash-A moved on stamp_stage")
    return {
        "ok": bool(report.get("committed")),
        "gamma": wfilt,
        "gamma_index": _gamma_rows(eng.world.box, wfilt),
        "hash_a_moved": False,
        "moved": moved,
        "write": report.get("write"),
    }


def stamp_cast(eng: CapsuleRoleplayEngine, authorize: bool = True) -> dict[str, Any]:
    """キャラを Δ.立場、小道具を Δ.状態へ。"""
    present = [n for n in eng.scene.participants if n in eng.chars]
    floor = scene_props(eng.scene.scene_id)
    out = []
    for name in present:
        ch = eng.chars[name]
        partners = [p for p in present if p != name]
        target = partners[0] if partners else "world"
        z = eng.zeta_of(name, target)
        filt = _scene_filt(eng, name)
        ch.rt.bind(filt)
        held = held_props(name)
        pkt = {
            "gamma": filt,
            "delta": [
                {"field": "立場", "new_value": f"{name}->{target} trust={z.trust:.2f}"},
                {"field": "状態", "new_value": "所持=" + ",".join(held)},
                {"field": "課題", "new_value": ch.goal or eng.scene.objective},
            ],
            "is": [
                {"field": "立場", "value": f"{name}->{target} trust={z.trust:.2f}"},
                {"field": "状態", "value": "所持=" + ",".join(held)},
                {"field": "課題", "value": ch.goal or eng.scene.objective},
            ],
        }
        frozen = ch.hash_a0
        report = ch.rt.commit(pkt, identity=1.0, authorize=authorize)
        if ch.box.hash_a() != frozen:
            raise RuntimeError(f"Hash-A moved on stamp_cast:{name}")
        out.append(
            {
                "name": name,
                "ok": bool(report.get("committed")),
                "gamma": filt,
                "delta": _delta_rows(ch.box, filt),
            }
        )
    return {"ok": all(row["ok"] for row in out) if out else False, "cast": out, "props": floor, "hash_a_moved": False}


def read_stage(eng: CapsuleRoleplayEngine) -> dict[str, Any]:
    """γ index を舞台として読む。"""
    wfilt = _scene_filt(eng, "World")
    rows = _gamma_rows(eng.world.box, wfilt)
    book = [{"scene_id": p.scene_id, "name": p.name, "current": p.scene_id == eng.scene.scene_id} for p in PLACES]
    return {
        "address": wfilt,
        "gamma_index": rows,
        "location": eng.scene.location,
        "scene_id": eng.scene.scene_id,
        "book": book,
    }


def _parts(state: str, key: str) -> list[str]:
    if key + "=" not in state:
        return []
    chunk = state.split(key + "=", 1)[1]
    chunk = chunk.split(" / ")[0]
    return [x for x in chunk.split(",") if x]


def read_cast(eng: CapsuleRoleplayEngine) -> dict[str, Any]:
    """Δ index をキャラと小道具として読む。"""
    people = []
    props: list[str] = []
    wstate = ""
    wrows = _delta_rows(eng.world.box, _scene_filt(eng, "World"))
    for row in reversed(wrows):
        if row.get("field") == "状態":
            wstate = str(row.get("new_value") or "")
            break
    for item in _parts(wstate, "場"):
        if item not in props:
            props.append(item)
    for name, ch in eng.chars.items():
        filt = _scene_filt(eng, name)
        deltas = _delta_rows(ch.box, filt)
        stance = next((d["new_value"] for d in reversed(deltas) if d["field"] == "立場"), "")
        state = next((d["new_value"] for d in reversed(deltas) if d["field"] == "状態"), "")
        task = next((d["new_value"] for d in reversed(deltas) if d["field"] == "課題"), "")
        held = _parts(state, "所持") or _parts(state, "小道具")
        for item in held:
            if item not in props:
                props.append(item)
        people.append({"name": name, "立場": stance, "課題": task, "所持": held, "小道具": held, "delta": deltas})
    return {"characters": people, "props": props, "場": _parts(wstate, "場")}


def rig(eng: CapsuleRoleplayEngine) -> dict[str, Any]:
    """舞台装置を γ に、キャラと小道具を Δ に載せる。"""
    stage = stamp_stage(eng)
    cast = stamp_cast(eng)
    return {
        "ok": bool(stage.get("ok") and cast.get("ok")),
        "stage": read_stage(eng),
        "cast": read_cast(eng),
        "hash_a_intact": all(ch.intact() for ch in eng.chars.values()) and eng.world.intact(),
        "world_facts": list(eng.world.facts),
    }
