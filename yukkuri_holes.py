#!/usr/bin/env python3
"""スタート / 本編 / 帰結を ? にする。

1 + ? = 0
  1  素材と見出し。所与
  ?  脚本。LLM が作る
  0  見出しだけ。本文ではない

完成和は捨てる。World には書かない。
"""
from __future__ import annotations

import json
from typing import Any, Callable, Optional

from yukkuri_maker import Line, convert, format_script

SLOTS = ("start", "body", "end")
HEADING = {
    "start": "スタート",
    "body": "本編",
    "end": "帰結",
}
FORM = "1 + ? = 0"


def open_slot(slot: str, material: dict[str, Any], beats: list[dict[str, Any]]) -> dict[str, Any]:
    if slot not in SLOTS:
        raise KeyError(slot)
    goal = f"0=見出し:{HEADING[slot]}"
    start = (
        f"1=素材 facts={material.get('facts')} "
        f"chars={material.get('characters')} "
        f"places={material.get('places')} "
        f"unknown={material.get('unknown')}"
    )
    return {
        "form": FORM,
        "slot": slot,
        "heading": HEADING[slot],
        "start": start,
        "open": "?",
        "goal": goal,
        "equation": f"{start} + ? = {goal}",
        "not": [
            "1+1=2 の完成形を一つの答えとして出す",
            "不明を確定する",
            "World に書く",
            "見出しを本文で畳む",
        ],
        "rule": "見出しは所与。? は脚本の穴。完成和を書くな。",
        "material": material,
        "beats": beats,
        "return": {
            "kari": "仮組み。plus より minus を先に。",
            "play": [{"speaker": "魔理沙|霊夢|アリス", "text": "発話"}],
        },
    }


def prompt_slot(hole: dict[str, Any]) -> str:
    return json.dumps(hole, ensure_ascii=False, indent=2)


def judge_slot(raw: Any) -> dict[str, Any]:
    obj = raw
    if isinstance(raw, str):
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError:
            return {"ok": False, "kind": "free_text", "reasons": ["完成文"], "play": []}
    if not isinstance(obj, dict):
        return {"ok": False, "kind": "free_text", "reasons": ["完成文"], "play": []}
    if "answer" in obj or "completion" in obj:
        return {"ok": False, "kind": "finished", "reasons": ["1+1=2 の完成和"], "play": []}
    play = obj.get("play") or []
    lines = []
    if isinstance(play, str):
        return {"ok": False, "kind": "free_text", "reasons": ["脚本が一つの答え"], "play": []}
    for row in play:
        if not isinstance(row, dict):
            continue
        speaker = str(row.get("speaker") or "").strip()
        text = str(row.get("text") or "").strip()
        if speaker and text:
            lines.append({"speaker": speaker, "text": text})
    return {
        "ok": bool(lines),
        "kind": "acting" if lines else "empty",
        "reasons": [],
        "kari": obj.get("kari"),
        "play": lines,
    }


def stub_llm(prompt: str) -> str:
    hole = json.loads(prompt)
    slot = hole.get("slot")
    facts = hole.get("material", {}).get("facts") or []
    unknown = hole.get("material", {}).get("unknown") or []
    if slot == "start":
        play = [
            {"speaker": "魔理沙", "text": "今日は魔法の森でキノコ探しだぜ"},
            {"speaker": "霊夢", "text": "またキノコなんて探してるの？"},
        ]
        minus = "帰結を先に書かない"
    elif slot == "body":
        play = [
            {"speaker": "魔理沙", "text": "お、霊夢じゃないか。ちょうどいい、神社まで付き合ってくれよ"},
            {"speaker": "霊夢", "text": "はいはい……"},
        ]
        minus = "書いてない理由を確定しない"
    else:
        tail = "理由はまだ空だな" if unknown else "まあ、そんなところだな"
        play = [
            {"speaker": "魔理沙", "text": f"よし、神社まで行くぜ。{tail}"},
            {"speaker": "霊夢", "text": "はいはい、分かったわよ"},
        ]
        minus = "不明を埋め切らない"
    return json.dumps(
        {
            "kari": {"plus": slot, "minus": minus, "cite": "material"},
            "play": play,
            "facts_seen": facts,
        },
        ensure_ascii=False,
    )


def fill_slot(hole: dict[str, Any], llm: Callable[[str], str]) -> dict[str, Any]:
    raw = llm(prompt_slot(hole))
    judged = judge_slot(raw)
    lines = [
        Line(speaker=row["speaker"], text=row["text"], origin="acted", beat=hole["slot"], scene_id=hole["slot"])
        for row in judged.get("play") or []
    ]
    return {
        "slot": hole["slot"],
        "heading": hole["heading"],
        "form": hole["form"],
        "equation": hole["equation"],
        "ok": judged["ok"] and judged["kind"] == "acting",
        "kind": judged["kind"],
        "reasons": judged["reasons"],
        "kari": judged.get("kari"),
        "lines": [line.__dict__ for line in lines],
        "script": format_script(lines),
        "wrote_world": False,
        "authority": False,
    }


def compose_holes(
    text: str,
    llm: Optional[Callable[[str], str]] = None,
    mode: str = "yukkuri",
) -> dict[str, Any]:
    """三つの穴を LLM に渡す。素材はアンカー。脚本は ?。"""
    base = convert(text, mode=mode, acting=False)
    material = base["material"]
    beats = base["beats"]
    actor = llm or stub_llm
    slots = {}
    rejected = []
    for name in SLOTS:
        hole = open_slot(name, material, beats)
        filled = fill_slot(hole, actor)
        slots[name] = filled
        if not filled["ok"]:
            rejected.append(name)
    script = []
    for name in SLOTS:
        script.append(f"【{HEADING[name]}】")
        script.append(slots[name]["script"])
        script.append("")
    return {
        "product": "ゆっくり実況台本メーカー",
        "form": FORM,
        "mode": mode,
        "material": material,
        "holes": slots,
        "rejected": rejected,
        "script": "\n".join(script).strip(),
        "world_written": False,
        "llm_authority": False,
        "ok": not rejected,
    }
