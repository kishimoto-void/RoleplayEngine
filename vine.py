#!/usr/bin/env python3
"""芋づる式。汚染しない。

種を一つ取る。つながった γ → Δ → Δ2 だけを引く。
他の場所の小道具も、他の人の所持も、一緒に出さない。
"""
from __future__ import annotations

from typing import Any

from depth_index import _latest, know_places, remember_here
from hole_play import _delta_rows, _gamma_rows
from index_stage import KIT, PROPS, _parts, held_props, scene_props
from roleplay_engine import CapsuleRoleplayEngine
from stage_marisa import EVENTS, PLACES


def resolve(seed: str) -> dict[str, str]:
    raw = (seed or "").strip()
    for place in PLACES:
        if raw in (place.scene_id, place.name) or raw in place.cues:
            return {"kind": "place", "topic": place.scene_id, "name": place.name}
    for topic, items in PROPS.items():
        if raw in items:
            place = next(p for p in PLACES if p.scene_id == topic)
            return {"kind": "prop", "topic": topic, "name": place.name, "prop": raw}
    if raw in KIT or raw in ("Alice", "Marisa", "アリス", "魔理沙"):
        name = {"アリス": "Alice", "魔理沙": "Marisa"}.get(raw, raw)
        return {"kind": "person", "topic": "", "name": name}
    return {"kind": "unknown", "topic": "", "name": raw}


def _place_state(eng: CapsuleRoleplayEngine, topic: str) -> str:
    rows = _delta_rows(
        eng.world.box,
        {"time_label": eng.scene.time_label, "project": "World", "topic": topic},
    )
    return _latest(rows, "状態")


def pull(eng: CapsuleRoleplayEngine, seed: str) -> dict[str, Any]:
    """一本だけ引く。帳は見ても、今の住所は動かさない。"""
    hit = resolve(seed)
    vine = {
        "seed": seed,
        "kind": hit["kind"],
        "gamma": None,
        "delta": {"場": [], "所持": {}, "events": []},
        "delta2": [],
        "off_vine": [],
        "contaminated": False,
        "store": False,
    }
    if hit["kind"] == "unknown":
        vine["off_vine"].append(seed)
        return vine

    topic = hit["topic"] or eng.scene.scene_id
    place = next((p for p in PLACES if p.scene_id == topic), None)
    if place is None:
        vine["off_vine"].append(seed)
        return vine

    known = _gamma_rows(
        eng.world.box,
        {"time_label": eng.scene.time_label, "project": "World", "topic": topic},
    )
    vine["gamma"] = {
        "topic": topic,
        "name": place.name,
        "match": bool(known),
        "current": topic == eng.scene.scene_id,
    }
    floor = _parts(_place_state(eng, topic), "場") or scene_props(topic)
    if hit["kind"] == "prop":
        floor = [hit["prop"]] if hit["prop"] in floor or hit["prop"] in scene_props(topic) else []
    vine["delta"]["場"] = floor
    vine["delta"]["events"] = [e.hook for e in EVENTS if e.place == topic]

    people = []
    if hit["kind"] == "person":
        people = [hit["name"]] if hit["name"] in eng.chars else []
    else:
        people = [n for n in ("Alice", "Marisa") if n in eng.chars]

    held_map = {}
    for name in people:
        if hit["kind"] == "place" or hit["kind"] == "prop":
            # 場所の蔓。所持は、今その場にいるときだけ。
            if topic != eng.scene.scene_id:
                continue
        rows = _delta_rows(
            eng.chars[name].box,
            {"time_label": eng.scene.time_label, "project": name, "topic": topic},
        )
        held = _parts(_latest(rows, "状態"), "所持") or (held_props(name) if topic == eng.scene.scene_id else [])
        if hit["kind"] == "person" and name != hit["name"]:
            continue
        held_map[name] = held
        vine["delta"]["所持"][name] = held
        stance = _latest(rows, "立場")
        if stance:
            vine["delta2"].append(
                {
                    "from": name,
                    "立場": stance,
                    "next": None,
                    "writes": False,
                }
            )

    if hit["kind"] != "person" and topic == eng.scene.scene_id and len(held_map) >= 2:
        names = list(held_map)
        z = eng.zeta_of(names[0], names[1])
        nxt = "間を取る"
        if "茶" in floor:
            nxt = "縁側で茶"
        elif "魔導書" in floor:
            nxt = "借り物の話"
        elif "キノコ籠" in floor:
            nxt = "採取を続ける"
        vine["delta2"] = [
            {
                "from": names[0],
                "to": names[1],
                "trust": z.trust,
                "next": nxt,
                "writes": False,
            }
        ]

    allowed = set(floor)
    for items in vine["delta"]["所持"].values():
        allowed.update(items)
    allowed.add(place.name)
    allowed.add(topic)
    catalog = set()
    for sid, items in PROPS.items():
        if sid == topic:
            continue
        catalog.update(items)
        catalog.add(sid)
    leaked = sorted(x for x in catalog if x in allowed and x not in floor and x not in {p for hs in vine["delta"]["所持"].values() for p in hs})
    # 汚染: この topic の場に無い他場所の小道具が場へ混ざったか
    foreign = [item for sid, items in PROPS.items() if sid != topic for item in items]
    mixed = [item for item in floor if item in foreign and item not in scene_props(topic)]
    vine["off_vine"] = sorted(set(mixed))
    vine["contaminated"] = bool(mixed)
    vine["hash_a_intact"] = all(ch.intact() for ch in eng.chars.values()) and eng.world.intact()
    return vine


def study(eng: CapsuleRoleplayEngine, seed: str) -> dict[str, Any]:
    """覚える。種から一本。混ぜない。"""
    know_places(eng)
    remember_here(eng)
    return pull(eng, seed)
