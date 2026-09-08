#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from yukkuri_maker import convert

SAMPLE = "魔理沙が森でキノコを探してたら、霊夢に会って神社に行くことになった"
SCENARIO = """1. 魔理沙が森へ行く
2. キノコを探す
3. 神社へ向かう
4. 霊夢と会話する"""


def run() -> dict:
    a = convert(SAMPLE)
    print("=== sample ===")
    print(a["script"])
    print("score", a["score"])
    print("unknown", a["material"]["unknown"])
    b = convert(SCENARIO, mode="follow")
    print("=== scenario ===")
    print(b["script"])
    cases = [
        {"id": "chars", "ok": "魔理沙「" in a["script"] and "霊夢「" in a["script"]},
        {"id": "tokens", "ok": "キノコ" in a["script"] and "神社" in a["script"]},
        {"id": "split", "ok": a["score"]["source_lines"] > 0 and a["score"]["acted_lines"] > 0 and not a["score"]["world_written"]},
        {"id": "unknown", "ok": "神社へ行く理由は書かれていない" in a["material"]["unknown"]},
        {"id": "follow", "ok": len(b["beats"]) == 4},
    ]
    out = {"passed": all(c["ok"] for c in cases), "cases": cases}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return out


if __name__ == "__main__":
    dest = Path(__file__).resolve().parent / "yukkuri_result.json"
    out = run()
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    raise SystemExit(0 if out["passed"] else 1)
