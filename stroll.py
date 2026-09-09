#!/usr/bin/env python3
"""散歩。攻略しない。観測する。

歩く → 見る → 気づく → 近づく → 見える Δ → Δ2 → η
何も起きない時間も残す。発言は世界事実にしない。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from npc_cast import at_place, line_of


@dataclass(frozen=True)
class Thing:
    name: str
    kind: str
    need: int = 0
    note: str = ""


@dataclass(frozen=True)
class Node:
    nid: str
    name: str
    ahead: tuple[str, ...]
    back: tuple[str, ...]
    things: tuple[Thing, ...]
    empty: str = "誰もいない"
    clock_hint: str = ""


SHRINE: dict[str, Node] = {
    "torii": Node(
        "torii",
        "鳥居",
        ("sandou",),
        (),
        (Thing("鳥居", "place"), Thing("石段", "place")),
        empty="参道の奥はまだ遠い",
    ),
    "sandou": Node(
        "sandou",
        "参道",
        ("keidai",),
        ("torii",),
        (Thing("参道", "place"), Thing("木漏れ日", "weather")),
        empty="風が通るだけだ",
    ),
    "keidai": Node(
        "keidai",
        "境内",
        ("engawa",),
        ("sandou",),
        (Thing("境内", "place"), Thing("賽銭箱", "prop"), Thing("本殿", "place", need=1)),
        empty="誰もいない",
    ),
    "engawa": Node(
        "engawa",
        "縁側",
        (),
        ("keidai",),
        (
            Thing("縁側", "place"),
            Thing("茶", "prop"),
            Thing("霊夢", "person", need=1, note="縁側の奥"),
        ),
        empty="縁側に茶がある",
    ),
}


def _clock(mins: int) -> str:
    h, m = divmod(10 * 60 + mins, 60)
    return f"{h:02d}:{m:02d}"


@dataclass
class Stroll:
    route: str = "hakurei-shrine"
    pos: str = "torii"
    facing: str = "ahead"
    elapsed: int = 0
    near: set[str] = field(default_factory=set)
    seen: list[str] = field(default_factory=list)
    log: list[dict] = field(default_factory=list)
    facts: list[str] = field(default_factory=list)

    def node(self) -> Node:
        return SHRINE[self.pos]

    def visible(self) -> list[dict[str, Any]]:
        here = self.node()
        out = []
        for th in here.things:
            if th.need <= 0 or th.name in self.near:
                out.append({"name": th.name, "kind": th.kind, "note": th.note, "distance": 0 if th.need == 0 or th.name in self.near else 1})
            else:
                out.append({"name": th.name, "kind": "hint", "note": "奥に気配", "distance": 1})
        if self.facing == "ahead" and here.ahead:
            nxt = SHRINE[here.ahead[0]]
            out.append({"name": nxt.name, "kind": "ahead", "note": "まだ遠い", "distance": 2})
        return out

    def delta(self) -> dict[str, list[str]]:
        vis = self.visible()
        near = [v for v in vis if v["distance"] == 0]
        return {
            "場": [v["name"] for v in near if v["kind"] in {"place", "prop"}],
            "人": [v["name"] for v in near if v["kind"] == "person"],
            "気配": [v["name"] for v in vis if v["kind"] in {"hint", "ahead"}],
        }

    def delta2(self) -> list[dict[str, Any]]:
        d = self.delta()
        links = []
        if "霊夢" in d["人"] and "茶" in d["場"]:
            links.append({"from": "霊夢", "to": "茶", "next": "縁側の茶", "writes": False})
        if not links and not d["人"]:
            links.append({"from": self.node().name, "to": "", "next": "間", "writes": False})
        return links

    def eta(self, newly: list[str]) -> str:
        if "霊夢" in newly:
            return line_of("Reimu", "wall")
        if "茶" in newly and "霊夢" not in self.delta()["人"]:
            return line_of("Reimu", "idle")
        if not newly:
            return self.node().empty
        return ""

    def _step(self, kind: str, extra: Any = None) -> dict[str, Any]:
        before = set(self.delta()["人"] + self.delta()["場"])
        if extra:
            extra()
        after = self.delta()
        newly = [x for x in after["人"] + after["場"] if x not in before]
        line = self.eta(newly)
        row = {
            "ok": True,
            "kind": kind,
            "time": _clock(self.elapsed),
            "pos": self.pos,
            "place": self.node().name,
            "facing": self.facing,
            "visible": self.visible(),
            "delta": after,
            "delta2": self.delta2(),
            "eta": line,
            "empty": not after["人"] and kind != "approach",
            "wrote_world": False,
            "facts": list(self.facts),
        }
        self.log.append(row)
        if line:
            self.seen.append(line)
        return row

    def look(self) -> dict[str, Any]:
        self.elapsed += 2
        return self._step("look")

    def move(self, dest: str = "") -> dict[str, Any]:
        here = self.node()
        if dest in ("back", "leave"):
            return self.leave()
        if not dest:
            dest = here.ahead[0] if self.facing != "back" and here.ahead else (here.back[0] if here.back else "")
        if dest in here.ahead or dest in here.back:
            self.pos = dest
            self.facing = "ahead" if dest in here.ahead else "back"
            self.near.clear()
            self.elapsed += 3
            return self._step("move")
        return {"ok": False, "reason": "no_path", "from": self.pos, "want": dest, "ahead": list(here.ahead), "back": list(here.back)}

    def approach(self, name: str) -> dict[str, Any]:
        here = self.node()
        hit = next((th for th in here.things if th.name == name or name in (th.note,)), None)
        if hit is None:
            return {"ok": False, "reason": "not_here", "pos": self.pos}
        self.elapsed += 2

        def extra() -> None:
            self.near.add(hit.name)

        return self._step("approach", extra)

    def leave(self) -> dict[str, Any]:
        here = self.node()
        if not here.back:
            return {"ok": False, "reason": "gate", "pos": self.pos}
        self.pos = here.back[0]
        self.facing = "back"
        self.near.clear()
        self.elapsed += 3
        return self._step("leave")

    def wait(self) -> dict[str, Any]:
        self.elapsed += 3
        row = self._step("wait")
        row["eta"] = row["eta"] or "風が吹く"
        if not row["eta"]:
            row["eta"] = "風が吹く"
        if row["delta"]["人"]:
            row["empty"] = False
        else:
            row["empty"] = True
            if "風が吹く" not in row["eta"]:
                row["eta"] = "風が吹く。何も起きない。"
        return row


def walk_script() -> list[dict[str, Any]]:
    st = Stroll()
    out = [st.look()]
    out.append(st.move("sandou"))
    out.append(st.move("keidai"))
    out.append(st.wait())
    out.append(st.move("engawa"))
    out.append(st.look())
    out.append(st.approach("霊夢"))
    return out
