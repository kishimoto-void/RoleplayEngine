#!/usr/bin/env python3
"""質問 + ? = 回答 を、γ / Δ index の上で実走する。"""
from __future__ import annotations

import json
from pathlib import Path

from hole_play import judge_index, open_hole, play_hole, stub_llm, sync_index
from roleplay_engine import make_demo_engine


def run() -> dict:
    eng = make_demo_engine()
    cases = []

    print("sync Alice")
    s = sync_index(eng, "Alice")
    print(" gamma", s["gamma_index"])
    print(" delta", s["delta_index"])
    cases.append({"id": "sync", "ok": s["ok"] and s["gamma_index"] and not s["hash_a_moved"]})

    hole = open_hole(eng, "Alice", "お前、本当に俺を信用してるのか？")
    print("form", hole.form)
    print("eq  ", hole.equation()[:160], "...")
    cases.append({"id": "form", "ok": hole.form == "1 + ? = 0" and hole.open == "?"})

    print("reject finished")
    fin = judge_index(hole, {"answer": "信用している。これが答え。"})
    print(" ", fin)
    cases.append({"id": "finished", "ok": fin["kind"] == "finished" and not fin["ok"]})

    print("llm acts ?")
    out = play_hole(eng, "お前、本当に俺を信用してるのか？", llm=stub_llm)
    print(" play", out["play"])
    print(" kari", out["kari"])
    print(" Δ after", out["index_after"]["delta"])
    cases.append({
        "id": "act",
        "ok": out["ok"] and out["play"].startswith("……信用してなきゃ") and out["hash_a_intact"],
    })

    print("index still closed words")
    fields = {row["field"] for row in out["index_after"]["delta"]}
    cases.append({"id": "closed", "ok": fields <= {"立場", "状態", "課題", "改善点", "結論"}})

    report = {"passed": all(c["ok"] for c in cases), "cases": cases}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return report


if __name__ == "__main__":
    dest = Path(__file__).resolve().parent / "hole_result.json"
    out = run()
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    raise SystemExit(0 if out["passed"] else 1)
