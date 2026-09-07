#!/usr/bin/env python3
"""η を Capsule に移さない。

絶対基準（アンカー）は Capsule が持つ。
1 + ? = 0 は穴の契約。
η は LLM の演技・判断・言語化。真実を決めない。
min3 の Eta.pull は偏差の計測のまま。書き込みを決めない。
"""
from __future__ import annotations

from typing import Any, Callable

from hole_play import Hole, index_view, judge_index, open_hole, play_hole, stub_llm, sync_index
from roleplay_engine import CapsuleRoleplayEngine


def anchor_of(eng: CapsuleRoleplayEngine, actor: str) -> dict[str, Any]:
    """LLM の裁量外。観察から書かない。"""
    ch = eng.chars[actor]
    view = index_view(eng, actor)
    inn = ch.box.cap.inner
    return {
        "alpha": list(inn.alpha.rules),
        "beta": {
            "name": inn.beta.name,
            "tone": inn.beta.tone,
            "center": inn.beta.center,
            "values": list(inn.beta.values),
        },
        "hash_a": ch.hash_a0,
        "intact": ch.intact(),
        "gamma": view["gamma"],
        "gamma_index": view["gamma_index"],
        "delta_index": view["delta_index"],
        "is": view["is"],
        "memory": {
            "immutable": list(ch.memory.immutable),
            "persistent": list(ch.memory.persistent),
        },
        "eta_pull": ch.box.cap.eta.pull,
        "eta_writes": False,
    }


def eta_act(hole: Hole, llm: Callable[[str], str] = stub_llm) -> dict[str, Any]:
    """演者。Capsule に書かない。"""
    raw = llm(hole.prompt())
    return {"raw": raw, "wrote": False, "authority": False}


def playable_from_anchor(hole: Hole, raw: Any) -> dict[str, Any]:
    """これは今のアンカーから演じられる ? か。"""
    judged = judge_index(hole, raw)
    yes = bool(judged.get("ok"))
    return {
        "verdict": "YES" if yes else "NO",
        "kind": judged.get("kind"),
        "reasons": judged.get("reasons") or [],
        "play": judged.get("play") or "",
        "kari": judged.get("kari"),
        "decides_truth": False,
    }


def observe_eta(eng: CapsuleRoleplayEngine, actor: str, play: str) -> dict[str, Any]:
    """偏差を測るだけ。採用も拒否も、この値では決めない。"""
    ch = eng.chars[actor]
    beta = ch.box.cap.inner.beta
    tone = 0.9 if any(tok in play for tok in ("……", "だぜ", "だな")) else 0.4
    identity = 0.0 if any(p in play for p in ("私は霊夢", "核を捨て")) else 1.0
    values = 0.7
    before = ch.box.cap.eta.pull
    ch.box.cap.eta.step(tone, identity, values)
    return {
        "pull_before": before,
        "pull_after": ch.box.cap.eta.pull,
        "high": ch.box.cap.eta.high(),
        "used_for_write": False,
    }


def run_turn(
    eng: CapsuleRoleplayEngine,
    question: str,
    actor: str = "Alice",
    llm: Callable[[str], str] = stub_llm,
) -> dict[str, Any]:
    """アンカー参照 → ηが?を演じる → Capsule が整合を見る。"""
    sync_index(eng, actor)
    hole = open_hole(eng, actor, question)
    anchor = anchor_of(eng, actor)
    acted = eta_act(hole, llm)
    gate = playable_from_anchor(hole, acted["raw"])
    adopted = False
    step = None
    if gate["verdict"] == "YES":
        step = play_hole(eng, question, actor=actor, llm=lambda _p: acted["raw"], sync=False)
        adopted = bool(step.get("ok"))
    eta = observe_eta(eng, actor, gate["play"])
    return {
        "form": hole.form,
        "anchor_hash_a": anchor["hash_a"][:16],
        "anchor_gamma": anchor["gamma"],
        "eta_authority": False,
        "verdict": gate["verdict"],
        "kind": gate["kind"],
        "play": gate["play"],
        "adopted": adopted,
        "eta": eta,
        "hash_a_intact": eng.chars[actor].intact(),
        "reasons": gate["reasons"],
    }
