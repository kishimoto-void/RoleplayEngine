#!/usr/bin/env python3
"""stub 在庫。封入した β から3型。

idle   口調。間。
craft  役と中心。仕事。
wall   価値観。距離。

公式の台詞の写しではない。設定の型だけ借りる。
"""
from __future__ import annotations

from typing import Any

from gravity import lean

# 出典は roleplay_engine の Beta / BetaFact と stage の手がかり。
SOURCE = {
    "Alice": {
        "tone": "短い。少し高い壁。丁寧語は稀。",
        "center": "人形と自制",
        "values": ("自分から謝らない", "助けても助けたいとは言わない", "強気を基調にする"),
        "role": "人形使い",
    },
    "Marisa": {
        "tone": "砕けた男言葉。だぜ / だな。",
        "center": "魔法と蒐集",
        "values": ("実力", "派手さ", "借りは返す"),
        "role": "魔法使い",
    },
}

STOCK = {
    "Alice": {
        "idle": (
            "……少し、座ってる。",
            "……人形がうるさいな。",
        ),
        "craft": (
            "糸は、まだ切れてない。",
            "人形は動く。それだけでいい。",
        ),
        "wall": (
            "……別に、お前を助けたいわけじゃない。",
            "……信用してなきゃ、ここにはいない。",
            "今は無理だ。近づくな。",
        ),
    },
    "Marisa": {
        "idle": (
            "まあ、今日は森だぜ。",
            "少し座るか。天気は悪くねえな。",
        ),
        "craft": (
            "キノコはまだ足りねぇな。",
            "借りた本、まだ読んでんだ。返すのはそのあとだぜ。",
        ),
        "wall": (
            "助けが要る、とか言うつもりはねぇぜ。",
            "信用してるかって？ …まあ、ゼロじゃねえだろ。",
            "今は無理だぜ。",
        ),
    },
}

MOVE_TO_PATTERN = {
    "話題を逸らす": "idle",
    "黙る": "idle",
    "取引を持ちかける": "craft",
    "嘘をつく": "craft",
    "強がる": "wall",
    "認める": "wall",
    "素直に頼む": "wall",
    "拒絶する": "wall",
}


def pattern_of(stimulus: str, move: str = "", actor: str = "") -> str:
    if actor:
        return lean(actor, stimulus, move)
    raw = stimulus or ""
    if any(w in raw for w in ("茶", "縁側", "暇", "間", "座", "日常", "ゆっくり")):
        return "idle"
    if any(w in raw for w in ("キノコ", "本", "箒", "実験", "人形", "蒐集", "採取")):
        return "craft"
    if any(w in raw for w in ("信用", "助け", "頼", "拒絶", "壁")):
        return "wall"
    return MOVE_TO_PATTERN.get(move, "idle")


def lines_of(actor: str, pattern: str) -> tuple[str, ...]:
    table = STOCK.get(actor) or STOCK["Alice"]
    return table.get(pattern) or table["idle"]


def pick(actor: str, stimulus: str = "", move: str = "", last: str = "") -> dict[str, Any]:
    pat = pattern_of(stimulus, move, actor)
    lines = list(lines_of(actor, pat))
    if move == "認める" and actor == "Alice" and "信用" in (stimulus or ""):
        chosen = "……信用してなきゃ、ここにはいない。"
    elif move == "強がる" and actor == "Alice" and "助け" in (stimulus or ""):
        chosen = "……別に、お前を助けたいわけじゃない。"
    else:
        chosen = next((ln for ln in lines if ln != last), lines[0])
    return {
        "actor": actor,
        "pattern": pat,
        "line": chosen,
        "cite": SOURCE.get(actor) or SOURCE["Alice"],
        "stock": True,
    }
