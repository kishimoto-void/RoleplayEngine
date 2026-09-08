#!/usr/bin/env python3
"""ゆっくり実況台本メーカーの口。"""
from __future__ import annotations

import argparse
import json

from yukkuri_maker import convert


def main() -> None:
    p = argparse.ArgumentParser(description="ゆっくり実況台本メーカー")
    p.add_argument("text", nargs="*")
    p.add_argument("--mode", default="yukkuri", choices=("free", "recommend", "follow", "yukkuri"))
    p.add_argument("--json", action="store_true")
    p.add_argument("--no-acting", action="store_true")
    args = p.parse_args()
    text = " ".join(args.text).strip()
    if not text:
        text = "魔理沙が森でキノコを探してたら、霊夢に会って神社に行くことになった"
    out = convert(text, mode=args.mode, acting=not args.no_acting)
    if args.json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return
    print(out["product"], "/", out["mode"])
    print("素材", out["material"]["facts"], out["material"]["places"])
    print("不明", out["material"]["unknown"])
    print()
    print(out["script"])
    print()
    print("内訳 source", out["score"]["source_lines"], "acted", out["score"]["acted_lines"], "world", out["score"]["world_written"])


if __name__ == "__main__":
    main()
