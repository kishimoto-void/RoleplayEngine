#!/usr/bin/env python3
"""仕様 8 項を RoleplayEngine 上で実走する。"""
from __future__ import annotations

import json
from pathlib import Path

from roleplay_engine import ProposedEvent, make_demo_engine


def line(title: str) -> None:
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


def run() -> dict:
    report: dict = {"cases": []}
    eng = make_demo_engine()

    line("0. 封入")
    print("Alice ", eng.chars["Alice"].hash_a0)
    print("Marisa", eng.chars["Marisa"].hash_a0)
    print("World ", eng.world.hash_a0)

    line("1. consistency ≠ rigidity")
    r1 = eng.act("Alice", "怖い。逃げた方がいい。")
    print(r1["chosen"], r1["utterance"], "intact", eng.chars["Alice"].intact())
    report["cases"].append({"id": 1, "ok": r1["chosen"] == "黙る" and eng.chars["Alice"].intact()})

    line("2. Scene / start + ? = goal")
    frame = eng.frame_for("Alice")
    print(frame["form"])
    print("start", frame["start"])
    print("goal ", frame["goal"])
    print("?    ", frame["candidates"])
    report["cases"].append({"id": 2, "ok": frame["form"] == "start + ? = goal"})

    line("3. 答えを指定しない")
    r3 = eng.user_says("手を貸してくれ。頼む。", speaker="Marisa", target="Alice")
    print("chosen", r3["chosen"], r3["utterance"])
    report["cases"].append({"id": 3, "ok": r3["chosen"] == "強がる"})

    line("4. 発言 ≠ 事実")
    naked = eng.claim_world("Alice", "昨日、紅魔館に行ったんだ", authorize=False)
    sealed = eng.claim_world("Alice", "昨日、紅魔館に行ったんだ", authorize=True)
    print("no-auth", naked["wrote_world"], naked["write_reason"])
    print("auth   ", sealed["wrote_world"], eng.world.facts)
    report["cases"].append({"id": 4, "ok": (not naked["wrote_world"]) and sealed["wrote_world"]})

    line("5. イベント")
    eng5 = make_demo_engine()
    r5 = eng5.user_says("お前、本当に俺を信用してるのか？", speaker="Marisa", target="Alice")
    ev = r5["commit"]["event"]
    print(r5["utterance"])
    print("trust", ev["trust_before"], "→", ev["trust_after"])
    print("tension", ev["tension_before"], "→", ev["tension_after"])
    report["cases"].append({
        "id": 5,
        "ok": r5["chosen"] == "認める" and abs(ev["trust_after"] - 0.51) < 1e-9,
        "trust": [ev["trust_before"], ev["trust_after"]],
        "tension": [ev["tension_before"], ev["tension_after"]],
    })

    line("6. 記憶三層")
    eng6 = make_demo_engine()
    alice = eng6.chars["Alice"]
    alice.memory.note_transient("今日は寒いな")
    for i in range(12):
        alice.memory.note_transient(f"雑談{i}")
    ev6 = ProposedEvent(speaker="Alice", action="裏切る", target="Marisa", utterance="渡した。", trust_delta=-0.20)
    eng6.commit_event(ev6, eng6.validate("Alice", ev6))
    print("寒い?", any("寒い" in x for x in alice.memory.transient))
    print("persistent", alice.memory.persistent)
    report["cases"].append({
        "id": 6,
        "ok": (not any("寒い" in x for x in alice.memory.transient)) and any("裏切" in x for x in alice.memory.persistent),
    })

    line("7. NPC 自律")
    r7 = make_demo_engine().act("Alice", "助けてくれ")
    print(r7["utterance"])
    report["cases"].append({"id": 7, "ok": r7["utterance"] == "……別に、お前を助けたいわけじゃない。"})

    line("8. Hash-A")
    report["cases"].append({"id": 8, "ok": eng.chars["Alice"].intact() and eng.world.intact()})
    print("Alice intact", eng.chars["Alice"].intact())
    print("World intact", eng.world.intact())

    report["passed"] = all(c["ok"] for c in report["cases"])
    line("結果")
    for c in report["cases"]:
        print(f"  [{'OK' if c['ok'] else 'NG'}] {c['id']}")
    print("all_passed", report["passed"])
    return report


if __name__ == "__main__":
    out = run()
    dest = Path(__file__).resolve().parent / "experiment_result.json"
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print("wrote", dest)
    raise SystemExit(0 if out["passed"] else 1)
