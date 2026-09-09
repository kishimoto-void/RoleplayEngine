#!/usr/bin/env python3
"""ラックカプセル。人格を増やさない。棚だけを持つ。

immutable  核の参照。ここに本文を足さない
persistent 閉じた語の最新
trace      場所の足跡。World 事実ではない
transient  直近の泡。日を跨いだら落ちてよい

Δ2 は置かない。Hash-A に入れない。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

BINS = ("immutable", "persistent", "trace", "transient")


@dataclass
class Slip:
    bin: str
    text: str
    place: str = ""
    who: str = ""
    day: int = 0
    world: bool = False


@dataclass
class RackCapsule:
    name: str = "rack"
    slips: list[Slip] = field(default_factory=list)
    day: int = 0

    def put(self, bin: str, text: str, place: str = "", who: str = "", day: int | None = None) -> dict[str, Any]:
        if bin not in BINS:
            return {"ok": False, "reason": "no_bin", "have": list(BINS)}
        if bin == "immutable":
            return {"ok": False, "reason": "immutable_is_ref_only"}
        slip = Slip(bin=bin, text=text, place=place, who=who, day=self.day if day is None else day, world=False)
        self.slips.append(slip)
        return {"ok": True, "bin": bin, "wrote_world": False, "hash_a": False}

    def of(self, bin: str, place: str = "") -> list[Slip]:
        rows = [s for s in self.slips if s.bin == bin]
        if place:
            rows = [s for s in rows if s.place == place]
        return rows

    def pull(self, seed: str, place: str = "") -> dict[str, Any]:
        """芋づる。種に当たった棚だけ。他の場所を混ぜない。"""
        hits = [s for s in self.slips if seed and seed in s.text]
        if place:
            hits = [h for h in hits if h.place == place or not h.place]
        by = {b: [h.text for h in hits if h.bin == b] for b in BINS}
        return {
            "seed": seed,
            "place": place,
            "bins": by,
            "delta2": [],
            "wrote_world": False,
        }

    def sleep(self) -> dict[str, Any]:
        self.day += 1
        kept = []
        dropped = 0
        for s in self.slips:
            if s.bin == "transient":
                dropped += 1
                continue
            kept.append(s)
        self.slips = kept
        return {"ok": True, "day": self.day, "dropped_transient": dropped, "wrote_world": False}

    def traces_at(self, place: str) -> list[str]:
        return [s.text for s in self.slips if s.bin == "trace" and s.place == place and s.day < self.day]

    def snapshot(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "day": self.day,
            "slips": [s.__dict__ for s in self.slips],
            "hash_a": False,
        }
