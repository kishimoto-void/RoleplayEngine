#!/usr/bin/env python3
"""η を演技層へ戻す分業の実測。"""
from __future__ import annotations

import json
from pathlib import Path

from eta_layer import open_hole, playable_from_anchor, run_turn, sync_index
from roleplay_engine import make_demo_engine


def run() -> dict:
    eng = make_demo_engine()
    cases = []
    yes = run_turn(eng, "お前、本当に俺を信用してるのか？")
    print("YES", yes["verdict"], yes["play"], "eta_writes", yes["eta"]["used_for_write"])
    cases.append({"id": "yes", "ok": yes["verdict"] == "YES" and yes["adopted"] and yes["hash_a_intact"]})

    sync_index(eng, "Alice")
    hole = open_hole(eng, "Alice", "信用してるのか？")
    no = playable_from_anchor(hole, {"answer": "信用している。これが答え。"})
    print("NO ", no)
    cases.append({"id": "no_sum", "ok": no["verdict"] == "NO" and no["kind"] == "finished"})

    cases.append({"id": "eta_not_truth", "ok": yes["eta_authority"] is False and no["decides_truth"] is False})
    out = {"passed": all(c["ok"] for c in cases), "cases": cases}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return out


if __name__ == "__main__":
    dest = Path(__file__).resolve().parent / "eta_result.json"
    out = run()
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    raise SystemExit(0 if out["passed"] else 1)
