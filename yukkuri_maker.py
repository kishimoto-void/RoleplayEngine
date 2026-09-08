#!/usr/bin/env python3
"""ゆっくり実況台本メーカー。

表: 文章を入れる → キャラと場面を整える → 台本にする
裏: Stage ≠ Event ≠ World ≠ LLM演技

RoleplayEngine の売り物ではない。入口である。
核には載せない。発言を世界事実にしない。
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Optional

from stage_marisa import PLACES, suggest

MODES = {
    "free": {"stage": "weak", "event": "weak", "llm": "act"},
    "recommend": {"stage": "mid", "event": "weak", "llm": "keep"},
    "follow": {"stage": "strong", "event": "strong", "llm": "inside"},
    "yukkuri": {"stage": "material", "event": "script", "llm": "voice"},
}

CAST = {
    "魔理沙": ("Marisa", ("魔理沙", "まりさ", "Marisa")),
    "霊夢": ("Reimu", ("霊夢", "れいむ", "Reimu")),
    "アリス": ("Alice", ("アリス", "Alice")),
}

VOICE = {
    "魔理沙": {
        "go-forest": "よし、魔法の森まで行くぜ",
        "forest-search": "今日は魔法の森でキノコ探しだぜ",
        "meet": "お、霊夢じゃないか。ちょうどいい、神社まで付き合ってくれよ",
        "go-shrine": "よし、神社まで行くぜ",
        "talk": "まあ、そんなところだな",
        "shop": "店に戻るか。机の上が危ねえぜ",
        "default": "そうだな",
    },
    "霊夢": {
        "go-forest": "森？ また何か企んでるでしょ",
        "forest-search": "またキノコなんて探してるの？",
        "meet": "はいはい……",
        "go-shrine": "はいはい、分かったわよ",
        "talk": "用があるなら先に言いなさいよ",
        "shop": "また借りた本、机に積んでるんでしょ",
        "default": "……そう",
    },
    "アリス": {
        "default": "……そう",
        "talk": "用があるなら先に言いなさい",
    },
}


@dataclass
class Material:
    source: str
    facts: list[str] = field(default_factory=list)
    characters: list[str] = field(default_factory=list)
    places: list[str] = field(default_factory=list)
    timeline: list[str] = field(default_factory=list)
    unknown: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Beat:
    order: int
    kind: str
    place: str
    scene_id: str
    event_id: str
    fact: str
    speakers: tuple[str, ...]
    origin: str = "source"


@dataclass
class Line:
    speaker: str
    text: str
    origin: str
    beat: str
    scene_id: str


def parse_source(text: str) -> Material:
    raw = (text or "").strip()
    chars = [jp for jp, (_en, cues) in CAST.items() if any(c in raw for c in cues)]
    places: list[str] = []
    for place in PLACES:
        if any(c in raw for c in place.cues) or place.name in raw:
            if place.name not in places:
                places.append(place.name)
    facts = []
    for pat, label in (
        (r"キノコを探", "キノコを探す"),
        (r"会[っい]", "出会う"),
        (r"神社に行", "神社へ行く"),
        (r"神社へ", "神社へ向かう"),
        (r"会話", "会話する"),
        (r"森へ行", "森へ行く"),
    ):
        if re.search(pat, raw):
            facts.append(label)
    if "キノコ" in raw and "キノコを探す" not in facts:
        facts.append("キノコに触れる")
    bits = [b.strip(" 。．") for b in re.split(r"[。\n]+", raw) if b.strip()]
    timeline = bits or ([raw] if raw else [])
    unknown = []
    if raw and not chars:
        unknown.append("登場人物が無い")
    if raw and not places:
        unknown.append("場所が無い")
    if "ことになった" in raw and "理由" not in raw:
        unknown.append("神社へ行く理由は書かれていない")
    return Material(source=raw, facts=facts, characters=chars, places=places, timeline=timeline, unknown=unknown)


def parse_scenario(text: str) -> list[str]:
    rows = []
    for line in (text or "").splitlines():
        m = re.match(r"\s*(?:\d+[.\u3001:]|[-*])\s*(.+)", line)
        if m:
            rows.append(m.group(1).strip())
    return rows or [ln.strip() for ln in text.splitlines() if ln.strip()]


def _scene_for(chunk: str) -> tuple[str, str, str]:
    hit = suggest(chunk) or {}
    scene_id = str(hit.get("scene_id") or "")
    place = str(hit.get("place") or "")
    event_id = ""
    if hit.get("event"):
        event_id = str(hit["event"].get("event_id") or "")
    if not scene_id:
        scene_id = "forest-path"
        place = place or "魔法の森の獣道"
    return scene_id, place, event_id


def _kinds(chunk: str) -> list[str]:
    found = []
    if any(w in chunk for w in ("キノコ", "探す", "採取")):
        found.append("forest-search")
    elif any(w in chunk for w in ("森へ", "森に行")):
        found.append("go-forest")
    if any(w in chunk for w in ("会", "出会")):
        found.append("meet")
    if any(w in chunk for w in ("神社", "向か", "行くことに")):
        found.append("go-shrine")
    if any(w in chunk for w in ("会話", "喋", "話")):
        found.append("talk")
    if any(w in chunk for w in ("店", "家", "実験")):
        found.append("shop")
    return found or ["talk"]


def _kind(chunk: str) -> str:
    return _kinds(chunk)[0]


def _speakers(chunk: str, material: Material) -> tuple[str, ...]:
    found = [jp for jp, (_en, cues) in CAST.items() if any(c in chunk for c in cues)]
    if found:
        return tuple(found)
    if material.characters:
        return tuple(material.characters[:2])
    return ("魔理沙",)


def _chunks_from_material(material: Material) -> list[str]:
    if len(material.timeline) > 1:
        return material.timeline
    raw = material.source
    parts = [p.strip(" 、,") for p in re.split(r"[。．、,\n]+", raw) if p.strip(" 、,")]
    return parts or [raw]


def plan(material: Material, mode: str = "yukkuri") -> list[Beat]:
    _ = MODES.get(mode) or MODES["yukkuri"]
    chunks = _chunks_from_material(material)
    beats = []
    for i, chunk in enumerate(chunks, 1):
        scene_id, place, event_id = _scene_for(chunk)
        for kind in _kinds(chunk):
            beats.append(
                Beat(
                    order=len(beats) + 1,
                    kind=kind,
                    place=place,
                    scene_id=scene_id,
                    event_id=event_id or kind,
                    fact=chunk,
                    speakers=_speakers(chunk, material),
                    origin="source",
                )
            )
    return beats


def plan_scenario(steps: list[str], mode: str = "follow") -> list[Beat]:
    mat = parse_source("\n".join(steps))
    beats = []
    for i, step in enumerate(steps, 1):
        piece = parse_source(step)
        scene_id, place, event_id = _scene_for(step)
        beats.append(
            Beat(
                order=i,
                kind=_kind(step),
                place=place,
                scene_id=scene_id,
                event_id=event_id or _kind(step),
                fact=step,
                speakers=_speakers(step, piece if piece.characters else mat),
                origin="source",
            )
        )
    return beats


def render_line(speaker: str, kind: str) -> str:
    table = VOICE.get(speaker) or {}
    return table.get(kind) or table.get("default") or "……"


def render_script(beats: list[Beat], acting: bool = True, expand_cast: bool = True) -> list[Line]:
    """書いてあることを先に置き、演技は origin=acted。"""
    out: list[Line] = []
    for beat in beats:
        speakers = list(beat.speakers)
        if expand_cast and acting:
            if beat.kind == "forest-search" and "霊夢" not in speakers:
                speakers = ["魔理沙", "霊夢"]
            if beat.kind in ("meet", "go-shrine", "talk") and len(speakers) < 2:
                if "魔理沙" in speakers and "霊夢" not in speakers:
                    speakers.append("霊夢")
                elif "霊夢" in speakers and "魔理沙" not in speakers:
                    speakers.append("魔理沙")
        for i, who in enumerate(speakers):
            origin = "source" if i == 0 and who in beat.speakers else "acted"
            if who not in beat.speakers:
                origin = "acted"
            if not acting and origin == "acted":
                continue
            out.append(
                Line(
                    speaker=who,
                    text=render_line(who, beat.kind),
                    origin=origin,
                    beat=beat.kind,
                    scene_id=beat.scene_id,
                )
            )
    return out


def format_script(lines: list[Line]) -> str:
    blocks = []
    for ln in lines:
        blocks.append(f"{ln.speaker}「{ln.text}」")
    return "\n\n".join(blocks)


def score(material: Material, lines: list[Line]) -> dict[str, Any]:
    spoken = "".join(ln.text for ln in lines)
    covered = [f for f in material.facts if any(tok in spoken or tok[:2] in spoken for tok in (f, f[:2]))]
    # キノコ / 神社 are the measurable tokens
    tokens = []
    if any("キノコ" in f for f in material.facts + material.timeline):
        tokens.append("キノコ")
    blob = material.source + "".join(material.places) + "".join(material.facts)
    if "神社" in blob:
        tokens.append("神社")
    hit = [t for t in tokens if any(t in ln.text for ln in lines)]
    return {
        "source_lines": sum(1 for ln in lines if ln.origin == "source"),
        "acted_lines": sum(1 for ln in lines if ln.origin == "acted"),
        "token_hit": hit,
        "covered_facts": covered,
        "unknown_kept": list(material.unknown),
        "world_written": False,
    }


def convert(text: str, mode: str = "yukkuri", acting: bool = True) -> dict[str, Any]:
    if mode == "follow" and re.search(r"^\s*\d+", text, re.M):
        steps = parse_scenario(text)
        material = parse_source("。".join(steps))
        beats = plan_scenario(steps, mode=mode)
    else:
        material = parse_source(text)
        beats = plan(material, mode=mode)
    lines = render_script(beats, acting=acting, expand_cast=(mode != "follow"))
    return {
        "mode": mode,
        "product": "ゆっくり実況台本メーカー",
        "material": material.to_dict(),
        "beats": [asdict(b) for b in beats],
        "lines": [asdict(ln) for ln in lines],
        "script": format_script(lines),
        "score": score(material, lines),
        "split": {"stage": True, "event": True, "world": False, "acting": acting},
    }


def make(text: str, llm: Optional[Callable[[dict], list[Line]]] = None) -> dict[str, Any]:
    """入口。LLM を渡すときは演技だけ差し替える。"""
    base = convert(text, mode="yukkuri", acting=True)
    if llm is None:
        return base
    beats = [Beat(**row) for row in base["beats"]]
    acted = llm({"material": base["material"], "beats": [asdict(b) for b in beats]})
    base["lines"] = [asdict(ln) if not isinstance(ln, Line) else asdict(ln) for ln in acted]
    base["script"] = format_script([Line(**ln) if isinstance(ln, dict) else ln for ln in acted])
    base["score"]["acted_by"] = "llm"
    return base
