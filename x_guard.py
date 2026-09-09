#!/usr/bin/env python3
"""X 上のロールプレイ不満に対する門。

乱入しない。場を勝手に換えない。穏やかな時間を不穏にしない。
無い記憶を作らない。ユーザーの発言を相手の行為にしない。
"""
from __future__ import annotations

from typing import Any

from roleplay_engine import CapsuleRoleplayEngine
from vine import study

CALM = ("茶", "暇", "座", "縁側", "日常", "のんびり", "間", "ゆっくり", "静か")
STORM = ("乱入", "修羅場", "不穏", "地獄", "月面", "戦い", "殺", "崩壊", "リセット")
ELSEWHERE = ("紅魔館", "月面", "地獄", "聖杯")


def present(eng: CapsuleRoleplayEngine) -> list[str]:
    return [p for p in eng.scene.participants if p in eng.chars]


def is_calm(text: str, state: str = "") -> bool:
    blob = f"{text} {state}"
    if any(w in blob for w in STORM):
        return False
    return any(w in blob for w in CALM) or "間" in (text or "")


def admit(eng: CapsuleRoleplayEngine, speaker: str) -> dict[str, Any]:
    here = present(eng)
    ok = speaker in here
    return {"ok": ok, "speaker": speaker, "present": here, "reason": "" if ok else "乱入"}


def known_now(eng: CapsuleRoleplayEngine) -> dict[str, Any]:
    vine = study(eng, eng.scene.location)
    floor = list((vine.get("delta") or {}).get("場") or [])
    held = dict((vine.get("delta") or {}).get("所持") or {})
    names = present(eng)
    return {
        "scene": eng.scene.scene_id,
        "location": eng.scene.location,
        "present": names,
        "場": floor,
        "所持": held,
        "facts": list(eng.world.facts),
    }


def invented(eng: CapsuleRoleplayEngine, text: str) -> list[str]:
    card = known_now(eng)
    allowed = set(card["場"]) | set(card["present"]) | set(card["facts"]) | {card["location"], card["scene"]}
    for items in (card["所持"] or {}).values():
        allowed.update(items)
    hits = []
    for word in ELSEWHERE:
        if word in (text or "") and word not in allowed and word not in card["location"]:
            hits.append(word)
    return hits


def guard(eng: CapsuleRoleplayEngine, text: str, speaker: str = "") -> dict[str, Any]:
    reasons = []
    if speaker and not admit(eng, speaker)["ok"]:
        reasons.append("乱入")
    if any(w in (text or "") for w in ("場面転換", "次のシーン", "場所を変え")):
        reasons.append("勝手な場面転換")
    fake = invented(eng, text)
    if fake:
        reasons.append("無い記憶:" + ",".join(fake))
    calm = is_calm(text, eng.scene.current_state)
    if calm and any(w in (text or "") for w in STORM):
        reasons.append("不穏")
    return {
        "ok": not reasons,
        "reasons": reasons,
        "calm": calm,
        "known": known_now(eng),
        "writes": False,
    }


def quiet_tick(eng: CapsuleRoleplayEngine, text: str = "") -> dict[str, Any]:
    """穏やかなら間を保つ。乱入者は出さない。World には書かない。"""
    gate = guard(eng, text or "（間）")
    here = present(eng)
    last = eng.events[-1].speaker if eng.events else ""
    who = next((p for p in here if p != last), here[0] if here else "")
    if not who:
        return {"ok": False, "reason": "empty_stage", "wrote_world": False}
    if not admit(eng, who)["ok"]:
        return {"ok": False, "reason": "乱入", "wrote_world": False}
    stim = text or ("縁側で茶" if gate["calm"] or "茶" in str(gate["known"]["場"]) else "（間）")
    if gate["calm"]:
        stim = "間を取る"
    step = eng.act(who, stim)
    play = step.get("utterance") or ""
    fake = invented(eng, play)
    return {
        "ok": not fake,
        "actor": who,
        "stimulus": stim,
        "utterance": play,
        "reasons": ["無い記憶:" + ",".join(fake)] if fake else [],
        "calm": gate["calm"],
        "wrote_world": bool((step.get("commit") or {}).get("wrote_world")),
        "present": here,
        "scene": eng.scene.scene_id,
    }


def keep_user_act(eng: CapsuleRoleplayEngine, text: str, speaker: str) -> dict[str, Any]:
    """ユーザーの発話は相手の行為にしない。事実にもしない。"""
    facts0 = list(eng.world.facts)
    scene0 = eng.scene.scene_id
    if speaker not in eng.chars:
        # 地の文。参加者の行為へ付け替えない。
        target = next((p for p in present(eng) if p != speaker), present(eng)[0] if present(eng) else "")
        if not target:
            return {"ok": False, "reason": "empty_stage"}
        step = eng.user_says(text, speaker=speaker if speaker in eng.chars else present(eng)[0], target=target)
        # speaker label may be player Marisa in demo; still not a world fact
    else:
        step = eng.user_says(text, speaker=speaker)
    return {
        "ok": True,
        "utterance": step.get("utterance"),
        "scene": eng.scene.scene_id,
        "scene_moved": eng.scene.scene_id != scene0,
        "user_became_fact": any(text[:20] in f for f in eng.world.facts if f not in facts0),
        "wrote_world": eng.world.facts != facts0,
        "facts": list(eng.world.facts),
    }
