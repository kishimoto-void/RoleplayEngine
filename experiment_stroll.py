#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from stroll import walk_script


def run() -> dict:
    log = walk_script()
    for row in log:
        print(row["time"], row["kind"], row["place"], row["delta"], row["eta"])
    people = [row["delta"]["人"] for row in log]
    cases = [
        {"id": "starts_empty", "ok": "霊夢" not in people[0]},
        {"id": "empty_ok", "ok": any(r["kind"] == "wait" and r["empty"] for r in log)},
        {"id": "meet_late", "ok": "霊夢" in people[-1]},
        {"id": "no_world", "ok": all(not r.get("wrote_world") for r in log)},
    ]
    report = {"passed": all(c["ok"] for c in cases), "cases": cases}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return report


if __name__ == "__main__":
    dest = Path(__file__).resolve().parent / "stroll_result.json"
    out = run()
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    raise SystemExit(0 if out["passed"] else 1)
