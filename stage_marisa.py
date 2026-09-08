#!/usr/bin/env python3
"""霧雨魔理沙の舞台装置。

roleplay_engine から分離する。
Hash-A に封入しない。世界事実でもない。
東方二次創作の要約引用。公式本文の写しではない。

出典の置き場（要約のみ）:
  人間の魔法使い。魔法の森に住み、霧雨魔法店を出す。
  蒐集と研究が生活の中心。派手な魔法を好む。
  博麗神社へよく顔を出す。紅魔館の蔵書を「借りる」。
  隣の人形遣いとは長い付き合い。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from roleplay_engine import SceneBook, SceneCapsule, SceneCard, CapsuleRoleplayEngine

SOURCE = "霧雨魔理沙の生活圏（二次創作要約。公式本文ではない）"


@dataclass(frozen=True)
class Place:
    scene_id: str
    name: str
    why: str
    cues: tuple[str, ...]
    opening: str
    objective: str
    current_state: str
    unresolved: tuple[str, ...]
    links: tuple[str, ...]
    exits: tuple[str, ...]
    cite: str


@dataclass(frozen=True)
class EventHook:
    event_id: str
    place: str
    cues: tuple[str, ...]
    hook: str
    cite: str


PLACES: tuple[Place, ...] = (
    Place(
        scene_id="kirisame-house",
        name="霧雨魔法店",
        why="自宅兼店。研究と蒐集の拠点。",
        cues=("店", "家", "実験", "研究", "魔法店", "帰"),
        opening="机の上が魔導書とキノコで埋まっている。返していない本が残る。",
        objective="研究の続きと借り物の始末",
        current_state="店番というより実験中",
        unresolved=("返していない本がある",),
        links=("forest-gate", "forest-path", "alice-house", "hakurei-shrine"),
        exits=("forest-gate", "forest-path", "alice-house"),
        cite="森の家に住み、店を出す人間の魔法使い",
    ),
    Place(
        scene_id="forest-path",
        name="魔法の森の獣道",
        why="キノコ採りと実験の歩き場。生活圏そのもの。",
        cues=("森", "キノコ", "きのこ", "獣道", "散歩"),
        opening="湿った葉の匂い。踏み跡は魔理沙の生活路。",
        objective="材料を拾いながら話を続ける",
        current_state="歩きながら話す",
        unresolved=("今日の採取はまだ途中",),
        links=("forest-gate", "kirisame-house", "alice-house"),
        exits=("forest-gate", "kirisame-house", "alice-house"),
        cite="魔法の森を生活圏にする",
    ),
    Place(
        scene_id="forest-gate",
        name="魔法の森の入口",
        why="人里と森の境。顔を合わせやすい。",
        cues=("入口", "森の入口", "出会"),
        opening="夕方の境。まだどこへも決まっていない。",
        objective="今日の行き先を決める",
        current_state="立ち話",
        unresolved=("行き先が空",),
        links=("forest-path", "kirisame-house", "alice-house", "hakurei-shrine"),
        exits=("forest-path", "kirisame-house", "alice-house", "hakurei-shrine"),
        cite="森の住人として境を出入りする",
    ),
    Place(
        scene_id="alice-house",
        name="人形遣いの家",
        why="隣に住む長い付き合い。寄りやすい。",
        cues=("アリス", "人形", "隣", "人形遣い"),
        opening="棚の人形が黙って見ている。客を上げた直後。",
        objective="用があるのか、ただ寄ったのかを決める",
        current_state="上がり框",
        unresolved=("用の有無",),
        links=("forest-path", "kirisame-house", "forest-gate"),
        exits=("forest-path", "kirisame-house", "forest-gate"),
        cite="森の人形遣いとの長い付き合い",
    ),
    Place(
        scene_id="hakurei-shrine",
        name="博麗神社",
        why="顔を出す場所。世間話と酒と異変の話。",
        cues=("神社", "霊夢", "賽銭", "酒", "異変"),
        opening="本殿の縁。賽銭箱は静か。魔理沙がよく上がり込む場所。",
        objective="用でも世間話でも、場に居る",
        current_state="縁側で足を下ろす",
        unresolved=("今日の用はまだ言っていない",),
        links=("forest-gate", "kirisame-house"),
        exits=("forest-gate",),
        cite="博麗神社へ頻繁に顔を出す",
    ),
    Place(
        scene_id="scarlet-mansion",
        name="紅魔館の門前",
        why="蔵書を借りに来る場所。招かれたとは限らない。",
        cues=("紅魔館", "パチュリー", "蔵書", "図書館", "借り"),
        opening="門は重い。来たと言っただけでは中には入れない。",
        objective="用を門の外で足すか、引き返すか",
        current_state="招かれていない",
        unresolved=("用があるのかまだ不明",),
        links=(),
        exits=("forest-gate",),
        cite="紅魔館の本を蒐集のために借りる癖",
    ),
)


EVENTS: tuple[EventHook, ...] = (
    EventHook("borrowed-book", "kirisame-house", ("本", "返し", "借り"), "返していない魔導書が机にある。", "蒐集癖"),
    EventHook("mushroom", "forest-path", ("キノコ", "きのこ", "採取"), "今日のキノコはまだ籠が軽い。", "森で材料を取る"),
    EventHook("shrine-idle", "hakurei-shrine", ("酒", "霊夢", "暇"), "用より先に縁側へ座る癖。", "神社へ入り浸る"),
    EventHook("spark-test", "kirisame-house", ("実験", "マスタースパーク", "弾幕"), "裏庭で火力を試したがる。", "派手な魔法を研究する"),
    EventHook("library-run", "scarlet-mansion", ("パチュリー", "蔵書", "盗み"), "門前まで来ても、中へ入ったことにはならない。", "本を借りに紅魔館へ行く"),
)


def _card(place: Place) -> SceneCard:
    return SceneCard(
        scene=SceneCapsule(
            scene_id=place.scene_id,
            participants=("Alice", "Marisa"),
            location=place.name,
            objective=place.objective,
            current_state=place.current_state,
            unresolved=list(place.unresolved),
            exits=list(place.exits),
            time_label="2026-09-08",
        ),
        links=place.links,
        opening=place.opening,
    )


def book() -> SceneBook:
    cards = {p.scene_id: _card(p) for p in PLACES}
    return SceneBook(cards, source=SOURCE)


def mount(eng: CapsuleRoleplayEngine) -> list[str]:
    """エンジンの帳へ舞台を載せる。Hash-A は触らない。事実は増やさない。"""
    added = []
    for place in PLACES:
        eng.book.add(_card(place))
        added.append(place.scene_id)
    return added


def suggest(text: str, current: str = "") -> Optional[dict[str, Any]]:
    """会話の語から、訪れる場所と出来事を引く。答えは指定しない。"""
    raw = text or ""
    place_hit = next((p for p in PLACES if any(c in raw for c in p.cues)), None)
    event_hit = None
    if place_hit is not None:
        event_hit = next((e for e in EVENTS if e.place == place_hit.scene_id and any(c in raw for c in e.cues)), None)
        if event_hit is None:
            event_hit = next((e for e in EVENTS if any(c in raw for c in e.cues) and e.place == place_hit.scene_id), None)
    else:
        event_hit = next((e for e in EVENTS if any(c in raw for c in e.cues)), None)
        if event_hit:
            place_hit = next((p for p in PLACES if p.scene_id == event_hit.place), None)
    if place_hit is None:
        return None
    return {
        "scene_id": place_hit.scene_id,
        "place": place_hit.name,
        "why": place_hit.why,
        "cite": place_hit.cite,
        "event": None
        if event_hit is None
        else {
            "event_id": event_hit.event_id,
            "hook": event_hit.hook,
            "cite": event_hit.cite,
        },
        "same_place": place_hit.scene_id == current,
        "source": SOURCE,
    }


def follow(eng: CapsuleRoleplayEngine, text: str, jump: bool = False) -> dict[str, Any]:
    """手がかりがあれば場面を換装する。発言を事実にしない。"""
    mount(eng)
    hint = suggest(text, eng.scene.scene_id)
    if hint is None:
        return {"ok": False, "reason": "no_cue", "scene": eng.scene.scene_id}
    if hint["same_place"]:
        return {
            "ok": True,
            "reason": "already_here",
            "hint": hint,
            "opening": eng.book.get(hint["scene_id"]).opening if eng.book.get(hint["scene_id"]) else "",
            "world_facts": list(eng.world.facts),
            "hash_a_intact": eng.chars["Marisa"].intact(),
        }
    moved = eng.prepare(hint["scene_id"], jump=jump)
    moved["hint"] = hint
    moved["cue"] = text
    return moved


def natural_turn(eng: CapsuleRoleplayEngine, text: str, speaker: str = "Marisa", jump: bool = False) -> dict[str, Any]:
    """舞台を先に合わせ、発話はイベントとして通す。完成和は出さない。"""
    stage = follow(eng, text, jump=jump)
    target = next((p for p in eng.scene.participants if p != speaker), "Alice")
    step = eng.user_says(text, speaker=speaker, target=target)
    return {
        "stage": stage,
        "step": {
            "utterance": step.get("utterance"),
            "chosen": step.get("chosen"),
            "ok": step.get("ok"),
        },
        "scene": eng.scene.scene_id,
        "location": eng.scene.location,
        "world_facts": list(eng.world.facts),
        "hash_a_intact": all(ch.intact() for ch in eng.chars.values()),
    }
