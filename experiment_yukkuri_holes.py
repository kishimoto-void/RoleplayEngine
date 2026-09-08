#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from yukkuri_holes import compose_holes, judge_slot


def run() -> dict:
    sample = "魔理沙が森でキノコを探してたら、霊夢に会って神社に行くことになった"
    out = compose_holes(sample)
    print(out["script"])
    print("rejected", out["rejected"], "world", out["world_written"])
    fin = judge_slot({"answer": "完成した一つの脚本"})
    cases = [
        {"id": "three", "ok": set(out["holes"]) == {"start", "body", "end"}},
        {"id": "form", "ok": all(h["form"] == "1 + ? = 0" for h in out["holes"].values())},
        {"id": "script", "ok": "キノコ" in out["script"] and "神社" in out["script"]},
        {"id": "no_world", "ok": not out["world_written"] and not out["llm_authority"]},
        {"id": "reject_sum", "ok": fin["kind"] == "finished"},
    ]
    report = {"passed": all(c["ok"] for c in cases), "cases": cases}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return report


if __name__ == "__main__":
    dest = Path(__file__).resolve().parent / "yukkuri_holes_result.json"
    out = run()
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    raise SystemExit(0 if out["passed"] else 1)
