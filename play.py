#!/usr/bin/env python3
"""RoleplayEngine 実行口。

  python3 play.py --script
  python3 play.py --repl
  python3 play.py 助けてくれ

コマンド（repl）:
  /status  見える世界
  /tick    NPC が間を埋める
  /save p  続きを書く
  /load p  続きを戻す
  /enter x 許可された出口だけ
  /scenes  用意した場面
  /prepare id  場面を今の住所にする（用意）
  /go id   links / exits があるときだけ
  /hole q  質問 + ? = 回答。? を演じる
  /stage t 魔理沙の舞台手がかりで場面を換装
  /claim t 世界主張（印なしでは事実にならない）
  /who     参加者
"""
from __future__ import annotations

import argparse
import json

from roleplay_engine import make_demo_engine
from hole_play import play_hole
from stage_marisa import follow, mount, natural_turn
from index_stage import rig
from depth_index import play_delta2, remember


def show(step: dict) -> None:
    ev = step["commit"]["event"]
    z = step["commit"]["zeta"]
    print(f"  ? {step['frame']['candidates']}")
    print(f"  {ev['speaker']}: {step['utterance']}")
    print(f"  trust={z['trust']:.2f} tension={z['tension']:.2f} world={step['commit']['wrote_world']}")


def run_script() -> dict:
    eng = make_demo_engine()
    print("Hash-A Alice ", eng.chars["Alice"].hash_a0[:16])
    print("Hash-A Marisa", eng.chars["Marisa"].hash_a0[:16])
    print("Scene", eng.scene.location, "/", eng.scene.current_state)
    log = []
    for text in ("手を貸してくれ", "お前、本当に俺を信用してるのか？"):
        print()
        print(f"Marisa: {text}")
        step = eng.user_says(text, speaker="Marisa", target="Alice")
        show(step)
        log.append(step["utterance"])
    print()
    print("tick")
    t = eng.tick()
    show(t)
    print()
    print("repeat guard")
    a = eng.user_says("助けてくれ", speaker="Marisa", target="Alice")
    b = eng.user_says("助けてくれ", speaker="Marisa", target="Alice")
    print(" ", a["utterance"])
    print(" ", b["utterance"])
    print()
    print("enter 取引")
    print(" ", eng.enter("取引", location="森の奥の空き地", scene_id="forest-deal"))
    print("status relations", eng.status()["relations"])
    print("intact", eng.status()["intact"])
    return {"log": log, "intact": eng.chars["Alice"].intact()}


def repl() -> None:
    eng = make_demo_engine()
    mount(eng)
    print("RoleplayEngine. /status /tick /save /load /enter /scenes /prepare /go /hole /stage /claim /who")
    print("地の文は Marisa の発話として通す。")
    while True:
        try:
            raw = input("> ").rstrip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if not raw:
            continue
        if raw in ("/q", "/quit"):
            return
        if raw == "/status":
            print(json.dumps(eng.status(), ensure_ascii=False, indent=2))
            continue
        if raw == "/rig":
            print(json.dumps(rig(eng), ensure_ascii=False, indent=2))
            continue
        if raw == "/depth":
            print(json.dumps(remember(eng)["depth"], ensure_ascii=False, indent=2))
            continue
        if raw == "/next":
            out = play_delta2(eng)
            print(out.get("actor"), out.get("next"), out.get("utterance"), "world", out.get("wrote_world"))
            continue
        if raw == "/who":
            print(eng.scene.participants, "player", eng.player)
            continue
        if raw == "/tick":
            show(eng.tick())
            continue
        if raw.startswith("/save "):
            print("wrote", eng.save(raw.split(" ", 1)[1]))
            continue
        if raw.startswith("/load "):
            print(eng.load(raw.split(" ", 1)[1]))
            continue
        if raw.startswith("/enter "):
            print(eng.enter(raw.split(" ", 1)[1]))
            continue
        if raw == "/scenes":
            print(json.dumps(eng.scenes(), ensure_ascii=False, indent=2))
            continue
        if raw.startswith("/prepare "):
            print(json.dumps(eng.prepare(raw.split(" ", 1)[1], jump=True), ensure_ascii=False, indent=2))
            continue
        if raw.startswith("/go "):
            print(json.dumps(eng.prepare(raw.split(" ", 1)[1], jump=False), ensure_ascii=False, indent=2))
            continue
        if raw.startswith("/hole "):
            out = play_hole(eng, raw.split(" ", 1)[1])
            print(out["form"], out["equation"][:120])
            print(" play", out.get("play"))
            print(" Δ", out.get("index_after", {}).get("delta"))
            continue
        if raw.startswith("/stage "):
            print(json.dumps(follow(eng, raw.split(" ", 1)[1], jump=False), ensure_ascii=False, indent=2))
            continue
        if raw.startswith("/claim "):
            print(eng.claim_world("Alice", raw.split(" ", 1)[1], authorize=False))
            continue
        turned = natural_turn(eng, raw, speaker=eng.player, jump=False)
        print(" scene", turned["scene"], turned["location"], turned["stage"].get("reason") or turned["stage"].get("ok"))
        step = turned["step"]
        print(f"  {eng.player}: {raw}")
        print(f"  reply {step['utterance']}")


def main() -> None:
    p = argparse.ArgumentParser(description="RoleplayEngine")
    p.add_argument("text", nargs="*")
    p.add_argument("--script", action="store_true")
    p.add_argument("--repl", action="store_true")
    args = p.parse_args()
    if args.repl:
        repl()
        return
    if args.script or not args.text:
        run_script()
        return
    eng = make_demo_engine()
    show(eng.user_says(" ".join(args.text), speaker="Marisa", target="Alice"))


if __name__ == "__main__":
    main()
