#!/usr/bin/env python3
"""RoleplayEngine の短い実行口。

既定は stub 演算器。会話を支配しない。
--script は仕様どおりの短い場面を一通り通す。
"""
from __future__ import annotations

import argparse
import json

from roleplay_engine import make_demo_engine


SCRIPT = (
    ("Marisa", "手を貸してくれ"),
    ("Marisa", "お前、本当に俺を信用してるのか？"),
    ("Marisa", "昨日、紅魔館に行ったんだろ？"),
)


def show(step: dict) -> None:
    print(f"  ? {step['frame']['candidates']}")
    print(f"  {step['commit']['event']['speaker']}: {step['utterance']}")
    z = step["commit"]["zeta"]
    print(f"  trust={z['trust']:.2f} tension={z['tension']:.2f} world={step['commit']['wrote_world']}")


def run_script() -> dict:
    eng = make_demo_engine()
    print("Hash-A Alice ", eng.chars["Alice"].hash_a0[:16])
    print("Hash-A Marisa", eng.chars["Marisa"].hash_a0[:16])
    print("Scene", eng.scene.location, "/", eng.scene.current_state)
    log = []
    for speaker, text in SCRIPT:
        print()
        print(f"{speaker}: {text}")
        step = eng.user_says(text, speaker=speaker, target="Alice")
        show(step)
        log.append({"speaker": speaker, "text": text, "reply": step["utterance"], "move": step["chosen"]})
    print()
    print("claim without authorize")
    naked = eng.claim_world("Alice", "昨日、紅魔館に行ったんだ", authorize=False)
    print(" ", naked["write_reason"], "facts", eng.world.facts)
    print("claim with authorize")
    sealed = eng.claim_world("Alice", "昨日、紅魔館に行ったんだ", authorize=True)
    print(" ", sealed["wrote_world"], "facts", eng.world.facts)
    print("Hash-A intact", eng.chars["Alice"].intact(), eng.world.intact())
    return {"log": log, "facts": list(eng.world.facts), "intact": eng.chars["Alice"].intact()}


def run_once(text: str) -> None:
    eng = make_demo_engine()
    step = eng.user_says(text, speaker="Marisa", target="Alice")
    print(f"Marisa: {text}")
    show(step)


def main() -> None:
    p = argparse.ArgumentParser(description="RoleplayEngine")
    p.add_argument("text", nargs="*", help="Marisa 側の一言")
    p.add_argument("--script", action="store_true", help="短い場面を通す")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()
    if args.script or not args.text:
        out = run_script()
        if args.json:
            print(json.dumps(out, ensure_ascii=False, indent=2))
        return
    run_once(" ".join(args.text))


if __name__ == "__main__":
    main()
