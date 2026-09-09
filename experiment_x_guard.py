#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from roleplay_engine import make_demo_engine
from stage_marisa import follow
from x_guard import admit, guard, quiet_tick


def run() -> dict:
    eng = make_demo_engine()
    follow(eng, "ちょっと神社寄るぜ", jump=False)
    quiet = quiet_tick(eng, "縁側でお茶")
    fake = guard(eng, "紅魔館で聖杯")
    cases = [
        {"id": "no_reimu", "ok": not admit(eng, "霊夢")["ok"]},
        {"id": "stay", "ok": quiet["scene"] == "hakurei-shrine" and not quiet["wrote_world"]},
        {"id": "no_fake", "ok": not fake["ok"]},
    ]
    report = {"passed": all(c["ok"] for c in cases), "cases": cases, "quiet": quiet["utterance"]}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return report


if __name__ == "__main__":
    dest = Path(__file__).resolve().parent / "x_guard_result.json"
    out = run()
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    raise SystemExit(0 if out["passed"] else 1)
