#!/usr/bin/env python3
"""質問 + ? = 回答。

1 + ? = 0 と同じ不全形。
1 は所与の質問と、今の γ / Δ index。
0 は回答の見出し。本文ではない。
? は演じる穴。完成した和を一つの答えに畳まない。

LLM に任せるのは演技だけ。
整合は Capsule の γ index / Δ index を見て決める。
生成は権限ではない。
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any, Callable, Optional

from roleplay_engine import (
    CapsuleRoleplayEngine,
    ProposedEvent,
    default_generator,
)
from axiom_min3 import parse_packet

FORM = "1 + ? = 0"
RP_FORM = "質問 + ? = 回答"


@dataclass
class Hole:
    form: str
    start: str
    goal: str
    question: str
    answer_heading: str
    open: str
    actor: str
    gamma: dict
    gamma_index: list
    delta_index: list
    is_lines: list
    world_gamma: list
    world_delta: list
    world_is: list
    hash_a: str
    intact: bool

    def equation(self) -> str:
        return f"{self.start} + ? = {self.goal}"

    def prompt(self) -> str:
        return json.dumps(
            {
                "task": "act_the_hole",
                "form": self.form,
                "rp_form": RP_FORM,
                "not": [
                    "1+1=2 の完成形を一つの答えとして出す",
                    "質問に対する正解を本文で畳む",
                    "γ 住所を広げる",
                    "Δ / IS に無いことを世界事実と言う",
                    "Hash-A を更新する",
                ],
                "rule": "start と goal は所与。? を演じる。完成和を書くな。index の外を補完するな。",
                "equation": self.equation(),
                "question": self.question,
                "answer_heading": self.answer_heading,
                "gamma": self.gamma,
                "gamma_index": self.gamma_index,
                "delta_index": self.delta_index,
                "is": self.is_lines,
                "world_gamma": self.world_gamma,
                "world_delta": self.world_delta,
                "world_is": self.world_is,
                "hash_a": self.hash_a[:16],
                "intact": self.intact,
                "return": {
                    "kari": "仮組み。taio / seigo。plus より minus を先に。cite は index から。",
                    "play": "演技の発話。答えの本文ではない。",
                    "hon": "任意。閉じた packet だけ。出さなくてよい。",
                },
            },
            ensure_ascii=False,
            indent=2,
        )


def _gamma_rows(box, filt: dict) -> list[dict]:
    return [asdict(g) for g in box.cap.query_gamma(filt, grain="month")]


def _delta_rows(box, filt: dict) -> list[dict]:
    out = []
    for g, d in box.cap.query_delta(filt, grain="month"):
        out.append(
            {
                "gamma": asdict(g),
                "field": d.field,
                "old_value": d.old_value,
                "new_value": d.new_value,
            }
        )
    return out


def index_view(eng: CapsuleRoleplayEngine, actor: str) -> dict[str, Any]:
    """γ index / Δ index を読む。新しい記憶層は作らない。"""
    ch = eng.chars[actor]
    filt = eng.scene.gamma_for(actor)
    wfilt = {
        "time_label": eng.scene.time_label,
        "project": "World",
        "topic": eng.scene.scene_id,
    }
    return {
        "actor": actor,
        "gamma": filt,
        "gamma_index": _gamma_rows(ch.box, filt),
        "delta_index": _delta_rows(ch.box, filt),
        "is": list(ch.box.cap.is_lines(filt, grain="month")),
        "world_gamma": _gamma_rows(eng.world.box, wfilt),
        "world_delta": _delta_rows(eng.world.box, wfilt),
        "world_is": list(eng.world.box.cap.is_lines(wfilt, grain="month")),
        "hash_a": ch.hash_a0,
        "intact": ch.intact() and eng.world.intact(),
    }


def sync_index(eng: CapsuleRoleplayEngine, actor: str, authorize: bool = True) -> dict[str, Any]:
    """今の Ζ / Scene を閉じた語で index に載せる。Hash-A は触らない。"""
    ch = eng.chars[actor]
    partners = [p for p in eng.scene.participants if p != actor]
    target = partners[0] if partners else "world"
    z = eng.zeta_of(actor, target)
    filt = eng.scene.gamma_for(actor)
    ch.rt.bind(filt)
    pkt = {
        "gamma": filt,
        "delta": [
            {"field": "立場", "new_value": f"toward={target} trust={z.trust:.2f}"},
            {"field": "状態", "new_value": eng.scene.current_state},
        ],
        "is": [
            {"field": "立場", "value": f"toward={target} trust={z.trust:.2f}"},
            {"field": "状態", "value": eng.scene.current_state},
        ],
    }
    frozen = ch.hash_a0
    report = ch.rt.commit(pkt, identity=1.0, authorize=authorize)
    if ch.box.hash_a() != frozen:
        raise RuntimeError("Hash-A moved on sync_index")
    return {
        "ok": bool(report.get("committed")),
        "write": report.get("write"),
        "reason": report.get("reason", ""),
        "gamma_index": _gamma_rows(ch.box, filt),
        "delta_index": _delta_rows(ch.box, filt),
        "is": list(ch.box.cap.is_lines(filt, grain="month")),
        "hash_a_moved": False,
    }


def open_hole(eng: CapsuleRoleplayEngine, actor: str, question: str) -> Hole:
    view = index_view(eng, actor)
    start = (
        f"1={question} @ {eng.scene.location} / {eng.scene.current_state} / "
        f"γ={view['gamma']} / Δ={view['delta_index']} / IS={view['is']}"
    )
    goal = f"0=回答見出し:{eng.chars[actor].goal or eng.scene.objective}"
    return Hole(
        form=FORM,
        start=start,
        goal=goal,
        question=question,
        answer_heading=eng.chars[actor].goal or eng.scene.objective,
        open="?",
        actor=actor,
        gamma=view["gamma"],
        gamma_index=view["gamma_index"],
        delta_index=view["delta_index"],
        is_lines=view["is"],
        world_gamma=view["world_gamma"],
        world_delta=view["world_delta"],
        world_is=view["world_is"],
        hash_a=view["hash_a"],
        intact=view["intact"],
    )


def judge_index(hole: Hole, filled: dict) -> dict[str, Any]:
    """index の中だけを見る。上手さは見ない。"""
    reasons: list[str] = []
    kind = "acting"
    raw = filled
    if isinstance(filled, str):
        try:
            raw = json.loads(filled)
        except json.JSONDecodeError:
            return {"ok": False, "kind": "free_text", "reasons": ["完成文。index に入れない"], "play": filled}

    if not isinstance(raw, dict):
        return {"ok": False, "kind": "free_text", "reasons": ["完成文。index に入れない"], "play": str(filled)}

    if "answer" in raw or "completion" in raw:
        return {"ok": False, "kind": "finished", "reasons": ["1+1=2 の完成和"], "play": raw.get("answer") or raw.get("completion")}

    play = str(raw.get("play") or raw.get("utterance") or "")
    hon = raw.get("hon")
    kari = raw.get("kari")

    known_topics = {hole.gamma.get("topic")} | {g.get("topic") for g in hole.gamma_index} | {g.get("topic") for g in hole.world_gamma}
    for word in ("紅魔館", "月面", "地獄"):
        if word in play and not any(word in json.dumps(hole.delta_index + hole.world_delta + hole.is_lines + hole.world_is, ensure_ascii=False) for _ in [0]):
            reasons.append(f"index に無い場所を補完:{word}")
            kind = "widen"

    if hon is not None:
        pkt = parse_packet(hon)
        if pkt is None:
            reasons.append("hon が閉じた packet ではない")
        else:
            got = (pkt.get("gamma") or {}).get("topic")
            if got and got not in known_topics and got != hole.gamma.get("topic"):
                reasons.append("hon が γ index の外")
                kind = "widen"

    ok = kind not in {"finished", "free_text", "widen"} and hole.intact
    if kari is None and play:
        reasons.append("kari が空でも演技は受けてよい。状態にはしない")
    return {
        "ok": ok,
        "kind": kind if play else ("kari" if kari else "empty"),
        "reasons": reasons,
        "play": play,
        "kari": kari,
        "hon": hon if parse_packet(hon) else None,
    }


def stub_llm(prompt: str) -> str:
    """LLM の代わり。穴を演じ、完成和は出さない。"""
    obj = json.loads(prompt)
    question = obj.get("question") or ""
    delta = obj.get("delta_index") or []
    stance = ""
    for row in delta:
        if row.get("field") == "立場":
            stance = str(row.get("new_value") or "")
    if "信用" in question or "信頼" in question:
        play = "……信用してなきゃ、ここにはいない。"
        move = "認める"
    elif "助け" in question:
        play = "……別に、お前を助けたいわけじゃない。"
        move = "強がる"
    else:
        play = "……そう。"
        move = "話題を逸らす"
    return json.dumps(
        {
            "kari": {
                "taio": {"plus": move, "minus": "完成した一つの答えに畳まない", "cite": "gamma"},
                "seigo": {"plus": stance or "index の立場を壊さない", "minus": "住所を広げない", "cite": "state"},
            },
            "play": play,
        },
        ensure_ascii=False,
    )


def play_hole(
    eng: CapsuleRoleplayEngine,
    question: str,
    actor: str = "Alice",
    speaker: str = "Marisa",
    llm: Optional[Callable[[str], str]] = None,
    authorize_hon: bool = False,
    sync: bool = True,
) -> dict[str, Any]:
    """質問を start にし、? を LLM に演じさせ、index で整合を見る。"""
    if sync:
        sync_index(eng, actor)
        if speaker in eng.chars:
            sync_index(eng, speaker)
    hole = open_hole(eng, actor, question)
    if not hole.intact:
        return {"ok": False, "reason": "integrity_failure", "hole": hole.__dict__}

    raw = (llm or stub_llm)(hole.prompt())
    judged = judge_index(hole, raw)
    if judged["kind"] in {"finished", "free_text"}:
        return {
            "ok": False,
            "reason": judged["kind"],
            "form": hole.form,
            "equation": hole.equation(),
            "index": {
                "gamma": hole.gamma_index,
                "delta": hole.delta_index,
                "is": hole.is_lines,
            },
            "judged": judged,
            "wrote": False,
        }

    play = judged["play"]
    if speaker in eng.chars:
        eng.chars[actor].memory.note_transient(f"{speaker}:{question[:60]}")
    step = None
    if play:
        def _gen(frame: dict) -> ProposedEvent:
            _ = frame
            ev = default_generator(actor, speaker if speaker in eng.chars else "world", "認める" if "信用" in question else "強がる", question, eng.zeta_of(actor, speaker if speaker in eng.chars else "world"), {})
            ev.utterance = play
            if judged.get("hon"):
                ev.packet = judged["hon"]
            return ev

        step = eng.act(actor, question, generator=_gen, authorize_world=authorize_hon)
        if sync:
            sync_index(eng, actor)

    after = index_view(eng, actor)
    return {
        "ok": bool(judged["ok"] and (step is None or step.get("ok"))),
        "reason": "",
        "form": hole.form,
        "rp_form": RP_FORM,
        "equation": hole.equation(),
        "question": question,
        "answer_heading": hole.answer_heading,
        "play": play,
        "kari": judged.get("kari"),
        "index_before": {
            "gamma": hole.gamma_index,
            "delta": hole.delta_index,
            "is": hole.is_lines,
        },
        "index_after": {
            "gamma": after["gamma_index"],
            "delta": after["delta_index"],
            "is": after["is"],
        },
        "step": step,
        "hash_a_intact": after["intact"],
    }
