#!/usr/bin/env python3
"""散歩世界の本役。封入はしない。配置と反応の種。

公式プロフィール本文の写しではない。公開設定の要約。
出典: Touhou Wiki / 萃夢想おまけ の公開要約。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from gravity import lean


@dataclass(frozen=True)
class Npc:
    nid: str
    name: str
    title: str
    home: str
    hang: tuple[str, ...]
    tone: str
    center: str
    values: tuple[str, ...]
    kit: tuple[str, ...]
    idle: str
    craft: str
    wall: str
    cite: str


CAST: tuple[Npc, ...] = (
    Npc(
        "Reimu",
        "霊夢",
        "博麗神社の巫女",
        "hakurei-shrine",
        ("engawa", "keidai", "hakurei-shrine"),
        "短い。急がない。怒るときは怒る。",
        "縁側と日和り",
        ("その場のノリ", "裏表を作らない", "用がなければ座っている"),
        ("茶", "御幣"),
        "縁側で茶を飲んでいる。急いではいない。",
        "賽銭箱を見て、今日も静かだと言う。",
        "……あら、来たのね。",
        "巫女。住処は神社。思考は単純で、縁側で日和る。",
    ),
    Npc(
        "Marisa",
        "魔理沙",
        "普通の魔法使い",
        "kirisame-house",
        ("forest-path", "torii", "hakurei-shrine", "kirisame-house"),
        "砕けた男言葉。だぜ / だな。",
        "魔法と蒐集",
        ("実力", "派手さ", "借りは返す"),
        ("箒", "ミニ八卦炉", "キノコ籠"),
        "まあ、今日は森だぜ。",
        "キノコはまだ足りねぇな。",
        "勝手に触るなよ。",
        "人間の魔法使い。森の店。神社へよく顔を出す。",
    ),
    Npc(
        "Alice",
        "アリス",
        "人形遣い",
        "alice-house",
        ("alice-house", "forest-path"),
        "短い。少し高い壁。",
        "人形と自制",
        ("自分から謝らない", "助けたいとは言わない", "強気を基調にする"),
        ("人形", "糸"),
        "……人形がうるさいな。",
        "糸は、まだ切れてない。",
        "……別に、呼ばれた覚えはない。",
        "森の家。他人には淡白。魔法と蒐集に執着する。",
    ),
    Npc(
        "Patchouli",
        "パチュリー",
        "動かない大図書館",
        "scarlet-mansion",
        ("scarlet-mansion",),
        "短い。室内。歩かない。",
        "本と知識",
        ("外へ出ない", "知識には動く", "蔵書を乱さない"),
        ("本", "茶"),
        "門の内側は、今日も静かだ。",
        "その本は、まだ返っていない。",
        "……中へは、招いていない。",
        "紅魔館の魔女。外出は稀。門前までが散歩の端。",
    ),
)


def by_id(nid: str) -> Npc | None:
    return next((n for n in CAST if n.nid == nid or n.name == nid), None)


def at_place(place: str) -> list[Npc]:
    return [n for n in CAST if place in n.hang or n.home == place]


def line_of(nid: str, pattern: str = "") -> str:
    npc = by_id(nid)
    if npc is None:
        return ""
    pat = pattern or lean(npc.nid)
    return {"idle": npc.idle, "craft": npc.craft, "wall": npc.wall}.get(pat) or npc.idle


def card(nid: str) -> dict[str, Any]:
    npc = by_id(nid)
    if npc is None:
        return {}
    return {
        "id": npc.nid,
        "name": npc.name,
        "title": npc.title,
        "home": npc.home,
        "hang": list(npc.hang),
        "tone": npc.tone,
        "center": npc.center,
        "values": list(npc.values),
        "kit": list(npc.kit),
        "store": False,
        "hash_a": False,
        "cite": npc.cite,
    }
