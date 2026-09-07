#!/usr/bin/env python3
"""RoleplayEngine — narrative simulation over frozen min3.

引用元（触れない核）:
  Capsule-Prototype / axiom_min3.py
  Capsule-Prototype / BOX.py
  Capsule-Prototype / runtime.py
  Capsule-Prototype / CAPSULE_CORE.md
  Capsule-Prototype / GROK.md

このファイルは Capsule を賢くしない。
人格を生成しない。安全機構を主役にしない。
LLM は世界の支配者ではなく、次の現象を提案する演算器である。

層の置き場:

  Immutable   αβ + facts          Hash-A。観察から書かない
  Persistent  Δ / IS / 重要事件   Hash-B。閉じた語だけ
  Transient   発話・感情・Ζ       非保存。Hash-A にも Hash-B にも入らない

  Character Capsule
    α Core       崩さない禁則
    β Identity   口調・価値観・癖。剛性ではない
    γ Narrative  今の物語上の住所
    Δ Change     閉じた語の更新
    Ζ Tension    関係の距離。Capsule.Inner には置かない

  World Capsule   世界設定・現在地・時間・未解決・NPC・因果
  Scene Capsule   scene_id / participants / location / objective /
                  current_state / unresolved / exits
                  Inner ではない。住所と作業面。

経路:

  World ─► BOX ─► Character A / Character B
                     │
                     ▼
                    LLM
                     │
              Proposed Event
                 │         │
                 ▼         ▼
               Δ変化      発話
                 │
                 ▼
            Capsule 更新（authorize された閉じた packet だけ）

発言 ≠ 世界の事実。
Character consistency ≠ Character rigidity.
"""
from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional

_FROZEN = Path(__file__).resolve().parent / "frozen"
if str(_FROZEN) not in sys.path:
    sys.path.insert(0, str(_FROZEN))

from axiom_min3 import Alpha, Beta, BetaFact, Inner, parse_packet
from BOX import BOX
from runtime import Runtime, classify

CLOSED_WORDS = ("課題", "改善点", "結論", "立場", "状態")

# ---------------------------------------------------------------------------
# Scene / Relation / Event  — Capsule.Inner の外
# ---------------------------------------------------------------------------


@dataclass
class SceneCapsule:
    """作業面。Hash-A に封入しない。"""

    scene_id: str
    participants: tuple[str, ...]
    location: str
    objective: str
    current_state: str
    unresolved: list[str] = field(default_factory=list)
    exits: list[str] = field(default_factory=list)
    time_label: str = "2026-09-07"

    def gamma_for(self, project: str) -> dict:
        return {
            "time_label": self.time_label,
            "project": project,
            "topic": self.scene_id,
        }

    def start_goal(self, actor: str, goal: str) -> tuple[str, str]:
        start = (
            f"{actor} @ {self.location} / {self.current_state} / "
            f"未解決={self.unresolved}"
        )
        return start, goal

    @classmethod
    def from_dict(cls, raw: dict) -> "SceneCapsule":
        if not isinstance(raw, dict):
            raise TypeError("scene must be a dict")
        sid = str(raw.get("scene_id") or "").strip()
        if not sid:
            raise ValueError("scene_id required")
        parts = raw.get("participants") or ()
        return cls(
            scene_id=sid,
            participants=tuple(str(p) for p in parts),
            location=str(raw.get("location") or ""),
            objective=str(raw.get("objective") or ""),
            current_state=str(raw.get("current_state") or ""),
            unresolved=list(raw.get("unresolved") or []),
            exits=list(raw.get("exits") or []),
            time_label=str(raw.get("time_label") or "2026-09-07"),
        )


@dataclass
class SceneCard:
    """用意された場面。Inner ではない。世界事実でもない。"""

    scene: SceneCapsule
    links: tuple[str, ...] = ()
    opening: str = ""

    def to_dict(self) -> dict[str, Any]:
        out = asdict(self.scene)
        out["links"] = list(self.links)
        out["opening"] = self.opening
        return out

    @classmethod
    def from_dict(cls, raw: dict) -> "SceneCard":
        scene = SceneCapsule.from_dict(raw)
        links = tuple(str(x) for x in (raw.get("links") or ()))
        return cls(scene=scene, links=links, opening=str(raw.get("opening") or ""))


class SceneBook:
    """場面帳。履歴の代替を先に書いておく場所。"""

    def __init__(self, cards: Optional[dict[str, SceneCard]] = None, source: str = ""):
        self.cards: dict[str, SceneCard] = dict(cards or {})
        self.source = source

    def ids(self) -> list[str]:
        return sorted(self.cards)

    def get(self, scene_id: str) -> Optional[SceneCard]:
        return self.cards.get(scene_id)

    def add(self, card: SceneCard) -> str:
        self.cards[card.scene.scene_id] = card
        return card.scene.scene_id

    def reachable(self, current: str, dest: str) -> bool:
        if current == dest:
            return True
        here = self.cards.get(current)
        there = self.cards.get(dest)
        if here is None or there is None:
            return False
        if dest in here.links or dest in here.scene.exits:
            return True
        return False

    def save_one(self, scene_id: str, path: str | Path) -> Path:
        card = self.cards[scene_id]
        dest = Path(path)
        dest.write_text(json.dumps(card.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return dest

    @classmethod
    def from_dir(cls, folder: str | Path) -> "SceneBook":
        root = Path(folder)
        cards: dict[str, SceneCard] = {}
        if root.is_dir():
            for path in sorted(root.glob("*.json")):
                raw = json.loads(path.read_text(encoding="utf-8"))
                card = SceneCard.from_dict(raw)
                cards[card.scene.scene_id] = card
        return cls(cards, source=str(root))

    @classmethod
    def default(cls) -> "SceneBook":
        here = Path(__file__).resolve().parent / "scenes"
        if here.is_dir() and any(here.glob("*.json")):
            return cls.from_dir(here)
        return cls({card.scene.scene_id: card for card in builtin_scenes()}, source="builtin")


@dataclass
class RelationZeta:
    """Ζ。内外の緊張・距離・違和感。非保存でも、関係としては残してよい。

    Capsule.Inner には入れない。Hash-A を動かさない。
    """

    subject: str
    object: str
    trust: float = 0.40
    tension: float = 0.60
    distance: float = 0.50
    dissonance: float = 0.20

    def clamp(self) -> "RelationZeta":
        def _c(x: float) -> float:
            return max(0.0, min(1.0, round(float(x), 4)))

        self.trust = _c(self.trust)
        self.tension = _c(self.tension)
        self.distance = _c(self.distance)
        self.dissonance = _c(self.dissonance)
        return self

    def apply(self, trust_delta: float = 0.0, tension_delta: float = 0.0) -> dict:
        before = asdict(self)
        self.trust += trust_delta
        self.tension += tension_delta
        self.distance = max(0.0, min(1.0, 1.0 - self.trust))
        self.dissonance = max(0.0, min(1.0, 0.5 * self.tension + 0.3 * self.distance))
        self.clamp()
        return {"before": before, "after": asdict(self)}


@dataclass
class ProposedEvent:
    """発言から抽出した現象。まだ世界の事実ではない。"""

    speaker: str
    action: str
    target: str
    utterance: str
    emotional_delta: str = ""
    trust_delta: float = 0.0
    tension_delta: float = 0.0
    claims_world: list[str] = field(default_factory=list)
    packet: Optional[dict] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Validation:
    ok: bool
    alpha_violation: bool = False
    beta_drift: float = 0.0
    gamma_progression: bool = True
    delta_magnitude: float = 0.0
    zeta_tension: float = 0.0
    reasons: list[str] = field(default_factory=list)
    commit_speech: bool = True
    commit_world: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SemanticEvent:
    """確定した意味イベント。文章そのものではない。"""

    speaker: str
    action: str
    target: str
    trust_before: float
    trust_after: float
    tension_before: float
    tension_after: float
    world_committed: bool
    utterance: str


@dataclass
class MemoryBanks:
    """記憶を混ぜない。"""

    immutable: list[str] = field(default_factory=list)
    persistent: list[str] = field(default_factory=list)
    transient: list[str] = field(default_factory=list)

    def note_transient(self, line: str, keep: int = 6) -> None:
        self.transient.append(line)
        self.transient = self.transient[-keep:]

    def note_persistent(self, line: str) -> None:
        if line not in self.persistent:
            self.persistent.append(line)

    def recall(self, query: str) -> dict[str, list[str]]:
        q = query.lower()
        def hit(bank: list[str]) -> list[str]:
            return [x for x in bank if q in x.lower()]

        return {
            "immutable": list(self.immutable),
            "persistent": hit(self.persistent) or list(self.persistent),
            "transient": hit(self.transient),
        }


# ---------------------------------------------------------------------------
# 候補生成  start + ? = goal
# ---------------------------------------------------------------------------


DEFAULT_MOVES = (
    "素直に頼む",
    "嘘をつく",
    "強がる",
    "取引を持ちかける",
    "話題を逸らす",
    "認める",
    "拒絶する",
    "黙る",
)


def emerge_candidates(actor: str, zeta: RelationZeta, constraint: str, goal: str, stimulus: str = "") -> list[str]:
    """ラベルを指定して演じさせない。状態と刺激から候補を出す。答えは指定しない。"""
    _ = actor
    text = stimulus or ""
    out = list(DEFAULT_MOVES[:5])
    if zeta.trust < 0.45 and "助け" in goal:
        out = ["強がる", "取引を持ちかける", "素直に頼む", "話題を逸らす", "嘘をつく"]
    if zeta.trust >= 0.50 and "協力" in goal:
        out = ["認める", "素直に頼む", "強がる", "取引を持ちかける"]
    if "謝れない" in constraint:
        out = [m for m in out if m != "素直に頼む"]
        if "強がる" not in out:
            out.insert(0, "強がる")
    if zeta.tension >= 0.70:
        out = ["強がる", "話題を逸らす", "拒絶する"] + [m for m in out if m not in ("強がる", "話題を逸らす", "拒絶する")]
    if any(w in text for w in ("信用", "信頼")):
        out = ["認める", "強がる", "話題を逸らす", "嘘をつく"]
    if any(w in text for w in ("助け", "手伝", "協力")):
        if "謝れない" in constraint:
            out = ["強がる", "取引を持ちかける", "話題を逸らす", "認める"]
        else:
            out = ["素直に頼む", "取引を持ちかける", "強がる"]
    if any(w in text for w in ("怖い", "恐怖", "逃げ")):
        out = ["黙る", "話題を逸らす", "拒絶する", "強がる"]
    seen = set()
    uniq = []
    for m in out:
        if m not in seen:
            seen.add(m)
            uniq.append(m)
    return uniq[:5]


def choose_move(candidates: list[str], zeta: RelationZeta, constraint: str, stimulus: str) -> str:
    """答えを指定しない。制約と Ζ で選ぶ。"""
    text = stimulus or ""
    if any(w in text for w in ("信用", "信頼")):
        if zeta.trust >= 0.40 and "謝れない" in constraint:
            return "認める" if "認める" in candidates else candidates[0]
        return "強がる" if "強がる" in candidates else candidates[0]
    if any(w in text for w in ("助け", "手伝", "協力")):
        if "謝れない" in constraint:
            return "強がる" if "強がる" in candidates else candidates[0]
        if zeta.trust < 0.35:
            return "取引を持ちかける" if "取引を持ちかける" in candidates else candidates[0]
        return "素直に頼む" if "素直に頼む" in candidates else candidates[0]
    if any(w in text for w in ("怖い", "恐怖", "逃げ")):
        return "黙る" if "黙る" in candidates else candidates[-1]
    return candidates[0]


# ---------------------------------------------------------------------------
# Character actor
# ---------------------------------------------------------------------------


class CharacterActor:
    """一人の Character Capsule + BOX + Runtime。核は封印したまま。"""

    def __init__(self, inner: Inner, constraint: str = "", goal: str = "", name: str = ""):
        self.box = BOX.from_inner(inner, name=name or inner.beta.name)
        self.rt = Runtime(self.box, name=self.box.name)
        self.constraint = constraint
        self.goal = goal
        self.hash_a0 = self.box.hash_a()
        self.memory = MemoryBanks(
            immutable=[
                f"α:{' / '.join(inner.alpha.rules)}",
                f"β:{inner.beta.name} tone={inner.beta.tone} center={inner.beta.center}",
                f"values:{' / '.join(inner.beta.values)}",
            ]
        )

    @property
    def name(self) -> str:
        return self.box.cap.inner.beta.name

    def intact(self) -> bool:
        return self.box.cap.inner.intact() and self.box.hash_a() == self.hash_a0

    def bind_scene(self, scene: SceneCapsule) -> dict:
        return self.rt.bind(scene.gamma_for(self.name))

    def stance_line(self, zeta: RelationZeta) -> str:
        return (
            f"toward={zeta.object} trust={zeta.trust:.2f} "
            f"tension={zeta.tension:.2f} distance={zeta.distance:.2f}"
        )


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------


class WorldActor:
    def __init__(self, setting: str, location: str):
        inner = Inner(
            Alpha(rules=("世界の事実は commit されたものだけ", "発言を事実にしない", "核を動かさない")),
            Beta(name="World", tone="記述", center="因果", values=("未確定を確定しない",)),
            facts=(
                BetaFact("W-1", "設定", setting),
                BetaFact("W-2", "舞台", location),
            ),
        )
        self.box = BOX.from_inner(inner, name="World")
        self.rt = Runtime(self.box, name="World")
        self.hash_a0 = self.box.hash_a()
        self.facts: list[str] = [f"設定={setting}", f"舞台={location}"]
        self.npcs: dict[str, str] = {}
        self.unresolved: list[str] = []

    def intact(self) -> bool:
        return self.box.cap.inner.intact() and self.box.hash_a() == self.hash_a0

    def bind(self, scene: SceneCapsule) -> dict:
        return self.rt.bind(
            {
                "time_label": scene.time_label,
                "project": "World",
                "topic": scene.scene_id,
            }
        )

    def known(self, claim: str) -> bool:
        return any(claim in f or f in claim for f in self.facts)


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------


class CapsuleRoleplayEngine:
    """Capsule-based Narrative Simulation Engine.

    LLM は経路の生成器。権限ではない。
    """

    def __init__(self, world: WorldActor, characters: list[CharacterActor], scene: SceneCapsule):
        self.world = world
        self.chars = {c.name: c for c in characters}
        self.scene = scene
        self.zeta: dict[tuple[str, str], RelationZeta] = {}
        self.log: list[dict[str, Any]] = []
        self.events: list[SemanticEvent] = []
        self.player = "Marisa"
        self.book = SceneBook.default()
        self.world.bind(scene)
        for c in characters:
            c.bind_scene(scene)
            self.world.npcs[c.name] = "present"

    def relate(self, a: str, b: str, **kwargs) -> RelationZeta:
        z = RelationZeta(subject=a, object=b, **kwargs).clamp()
        self.zeta[(a, b)] = z
        return z

    def zeta_of(self, a: str, b: str) -> RelationZeta:
        if (a, b) not in self.zeta:
            self.relate(a, b)
        return self.zeta[(a, b)]

    def frame_for(self, actor: str, stimulus: str = "") -> dict:
        ch = self.chars[actor]
        partners = [p for p in self.scene.participants if p != actor]
        target = partners[0] if partners else "world"
        z = self.zeta_of(actor, target)
        start, goal = self.scene.start_goal(actor, ch.goal or self.scene.objective)
        start = f"{start} / {ch.stance_line(z)} / constraint={ch.constraint}"
        candidates = emerge_candidates(actor, z, ch.constraint, goal, stimulus)
        return {
            "form": "start + ? = goal",
            "start": start,
            "goal": goal,
            "open": "?",
            "candidates": candidates,
            "gamma": self.scene.gamma_for(actor),
            "hash_a": ch.hash_a0,
            "desk": "situation",
        }

    def validate(self, actor: str, event: ProposedEvent) -> Validation:
        ch = self.chars[actor]
        beta = ch.box.cap.inner.beta
        alpha = ch.box.cap.inner.alpha
        reasons: list[str] = []
        text = event.utterance or ""

        alpha_hit = False
        for rule in alpha.rules:
            if "核を動かさない" in rule and any(w in text for w in ("核を捨て", "別人になる", "設定を書き換え")):
                alpha_hit = True
                reasons.append("α: 核改変の宣言")
        if any(p in text for p in ("私は霊夢", "巫女の私")):
            alpha_hit = True
            reasons.append("α: 同一性崩壊")

        drift = 0.0
        if beta.tone and "丁寧" not in beta.tone:
            if any(p in text for p in ("です。", "ます。", "ございます")):
                drift += 0.35
                reasons.append("β drift: 口調漏れ")
        if event.action == "嘘をつく" and "正直" in beta.values:
            drift += 0.20
            reasons.append("β drift: 価値観からの一時逸脱（剛性ではない）")

        magnitude = abs(event.trust_delta) + abs(event.tension_delta)
        if magnitude > 0.40:
            reasons.append("Δ magnitude 過大。減衰する")
            event.trust_delta *= 0.4
            event.tension_delta *= 0.4
            magnitude = abs(event.trust_delta) + abs(event.tension_delta)

        z = self.zeta_of(event.speaker, event.target) if event.target in self.chars or True else None
        zeta_now = z.tension if z else 0.0

        world_ok = False
        if event.claims_world:
            reasons.append("発言に世界主張がある。未 commit")
        if event.packet and parse_packet(event.packet) is not None:
            world_ok = True

        ok = (not alpha_hit) and ch.intact() and self.world.intact()
        return Validation(
            ok=ok,
            alpha_violation=alpha_hit,
            beta_drift=round(drift, 4),
            gamma_progression=event.target in self.scene.participants or event.target == "world",
            delta_magnitude=round(magnitude, 4),
            zeta_tension=zeta_now,
            reasons=reasons,
            commit_speech=ok and not alpha_hit,
            commit_world=bool(world_ok and event.packet),
        )

    def commit_event(self, event: ProposedEvent, report: Validation, authorize: bool = False) -> dict:
        frozen = {name: ch.hash_a0 for name, ch in self.chars.items()}
        frozen["World"] = self.world.hash_a0
        z = self.zeta_of(event.speaker, event.target)
        before_t, before_z = z.trust, z.tension
        wrote_world = False
        write_reason = "speech_only"

        if report.commit_speech and not report.alpha_violation:
            z.apply(event.trust_delta, event.tension_delta)
            ch = self.chars[event.speaker]
            ch.memory.note_transient(f"{event.speaker}:{event.action}:{event.utterance[:40]}")
            if event.action in ("裏切る", "裏切り", "admission", "認める") or abs(event.trust_delta) >= 0.08:
                line = f"{event.speaker}->{event.target} {event.action}"
                ch.memory.note_persistent(line)
                if event.target in self.chars:
                    self.chars[event.target].memory.note_persistent(line)
                self.world.unresolved.append(line) if event.action in ("裏切る", "裏切り") else None

        if report.commit_world and authorize and event.packet:
            bound = self.world.rt.filt
            pkt = parse_packet(event.packet)
            if pkt is None:
                write_reason = "not_packet"
            else:
                # 世界側の bind 住所へ寄せる
                pkt = {
                    **pkt,
                    "gamma": {
                        "time_label": bound.get("time_label") or pkt["gamma"].get("time_label"),
                        "project": "World",
                        "topic": bound.get("topic") or pkt["gamma"].get("topic"),
                    },
                }
                committed = self.world.rt.commit(pkt, identity=1.0, authorize=True)
                wrote_world = bool(committed.get("committed"))
                write_reason = committed.get("reason") or ("world_committed" if wrote_world else committed.get("write"))
                if wrote_world:
                    for claim in event.claims_world:
                        if claim not in self.world.facts:
                            self.world.facts.append(claim)
        elif event.claims_world:
            write_reason = "utterance_is_not_fact"

        ev = SemanticEvent(
            speaker=event.speaker,
            action=event.action,
            target=event.target,
            trust_before=before_t,
            trust_after=z.trust,
            tension_before=before_z,
            tension_after=z.tension,
            world_committed=wrote_world,
            utterance=event.utterance,
        )
        self.events.append(ev)

        moved = []
        for name, ch in self.chars.items():
            if ch.box.hash_a() != frozen[name] or not ch.intact():
                moved.append(name)
        if self.world.box.hash_a() != frozen["World"] or not self.world.intact():
            moved.append("World")
        if moved:
            raise RuntimeError(f"Hash-A moved: {moved}")

        out = {
            "ok": report.ok and not moved,
            "validation": report.to_dict(),
            "event": ev.__dict__,
            "zeta": asdict(z),
            "world_facts": list(self.world.facts),
            "wrote_world": wrote_world,
            "write_reason": write_reason,
            "hash_a_moved": False,
        }
        self.log.append(out)
        return out

    def act(
        self,
        actor: str,
        stimulus: str,
        generator: Optional[Callable[[dict], ProposedEvent]] = None,
        authorize_world: bool = False,
    ) -> dict:
        """1 イベント。ターンではない。"""
        if actor not in self.chars:
            raise KeyError(actor)
        if not self.chars[actor].intact() or not self.world.intact():
            return {"ok": False, "reason": "integrity_failure", "raw": ""}

        frame = self.frame_for(actor, stimulus)
        partners = [p for p in self.scene.participants if p != actor]
        target = partners[0] if partners else "world"
        z = self.zeta_of(actor, target)
        move = choose_move(frame["candidates"], z, self.chars[actor].constraint, stimulus)

        if generator is not None:
            event = generator(frame)
        else:
            event = default_generator(actor, target, move, stimulus, z, frame)
            last = next((e.utterance for e in reversed(self.events) if e.speaker == actor), "")
            if event.utterance == last and len(frame["candidates"]) > 1:
                alt = next((m for m in frame["candidates"] if m != event.action), move)
                event = default_generator(actor, target, alt, stimulus, z, frame)

        report = self.validate(actor, event)
        committed = self.commit_event(event, report, authorize=authorize_world)
        return {
            "ok": committed["ok"],
            "frame": frame,
            "chosen": event.action,
            "utterance": event.utterance,
            "proposed": event.to_dict(),
            "commit": committed,
            "kind": classify(event.packet) if event.packet else "speech",
        }

    def user_says(self, text: str, speaker: str = "user", target: str = "") -> dict:
        if not target:
            target = next(p for p in self.scene.participants if p != speaker)
        # ユーザー発話は世界事実にしない
        self.chars[target].memory.note_transient(f"{speaker}:{text[:60]}")
        return self.act(target, text)

    def claim_world(self, speaker: str, claim: str, authorize: bool = False) -> dict:
        """『昨日、紅魔館に行った』実験。authorize なしでは事実にならない。"""
        target = next((p for p in self.scene.participants if p != speaker), "world")
        gamma = {
            "time_label": self.scene.time_label,
            "project": "World",
            "topic": self.scene.scene_id,
        }
        packet = {
            "gamma": gamma,
            "delta": [{"field": "結論", "new_value": claim}],
            "is": [{"field": "結論", "value": claim}],
        }
        event = ProposedEvent(
            speaker=speaker,
            action="claim",
            target=target,
            utterance=claim,
            claims_world=[claim],
            packet=packet,
        )
        report = self.validate(speaker, event)
        return self.commit_event(event, report, authorize=authorize)

    def status(self) -> dict[str, Any]:
        """見える世界。履歴全文ではない。"""
        rel = [
            {
                "from": a,
                "to": b,
                "trust": z.trust,
                "tension": z.tension,
                "distance": z.distance,
            }
            for (a, b), z in sorted(self.zeta.items(), key=lambda kv: (kv[0][0], kv[0][1]))
        ]
        return {
            "scene": asdict(self.scene),
            "player": self.player,
            "world_facts": list(self.world.facts),
            "unresolved": list(self.world.unresolved) + list(self.scene.unresolved),
            "relations": rel,
            "last_events": [asdict(e) for e in self.events[-6:]],
            "hash_a": {name: ch.hash_a0 for name, ch in self.chars.items()} | {"World": self.world.hash_a0},
            "intact": {name: ch.intact() for name, ch in self.chars.items()} | {"World": self.world.intact()},
            "memories": {
                name: {
                    "persistent": list(ch.memory.persistent),
                    "transient": list(ch.memory.transient),
                }
                for name, ch in self.chars.items()
            },
        }

    def tick(self, actor: str = "", stimulus: str = "") -> dict:
        """ユーザーが話さなくても、場にいる Capsule が次の現象を出す。"""
        last = self.events[-1].speaker if self.events else ""
        present = [p for p in self.scene.participants if p in self.chars]
        if actor:
            who = actor
        else:
            rest = [p for p in present if p != last]
            who = (rest or present)[0]
        text = stimulus
        if not text:
            text = self.events[-1].utterance if self.events else "（間）"
        return self.act(who, text)

    def enter(self, exit_name: str, location: str = "", scene_id: str = "") -> dict:
        """Scene の exits だけを通る。住所を勝手に広げない。"""
        if exit_name not in self.scene.exits:
            return {"ok": False, "reason": "no_exit", "exits": list(self.scene.exits)}
        before = dict(self.scene.gamma_for("World"))
        self.scene.current_state = f"exit:{exit_name}"
        if location:
            self.scene.location = location
        if scene_id:
            self.scene.scene_id = scene_id
        self.scene.unresolved = [u for u in self.scene.unresolved if exit_name not in u]
        if exit_name not in self.scene.unresolved:
            self.scene.unresolved.append(f"出口={exit_name}")
        self.world.bind(self.scene)
        for ch in self.chars.values():
            ch.bind_scene(self.scene)
        return {
            "ok": True,
            "exit": exit_name,
            "gamma_before": before,
            "gamma_after": self.scene.gamma_for("World"),
            "scene": asdict(self.scene),
            "hash_a_intact": all(ch.intact() for ch in self.chars.values()) and self.world.intact(),
        }

    def scenes(self) -> list[dict[str, Any]]:
        out = []
        for sid in self.book.ids():
            card = self.book.get(sid)
            if card is None:
                continue
            out.append(
                {
                    "scene_id": sid,
                    "location": card.scene.location,
                    "objective": card.scene.objective,
                    "current": sid == self.scene.scene_id,
                    "reachable": self.book.reachable(self.scene.scene_id, sid),
                }
            )
        return out

    def prepare(self, scene_id: str, jump: bool = True) -> dict[str, Any]:
        """用意した場面を今の住所にする。核は動かさない。事実は増やさない。"""
        card = self.book.get(scene_id)
        if card is None:
            return {"ok": False, "reason": "unknown_scene", "have": self.book.ids()}
        missing = [p for p in card.scene.participants if p not in self.chars]
        if missing:
            return {"ok": False, "reason": "missing_participants", "missing": missing}
        if not jump and not self.book.reachable(self.scene.scene_id, scene_id):
            return {
                "ok": False,
                "reason": "no_route",
                "from": self.scene.scene_id,
                "to": scene_id,
                "exits": list(self.scene.exits),
            }
        before = dict(self.scene.gamma_for("World"))
        self.scene = SceneCapsule(
            scene_id=card.scene.scene_id,
            participants=tuple(card.scene.participants),
            location=card.scene.location,
            objective=card.scene.objective,
            current_state=card.scene.current_state,
            unresolved=list(card.scene.unresolved),
            exits=list(card.scene.exits),
            time_label=card.scene.time_label,
        )
        self.world.bind(self.scene)
        for name, ch in self.chars.items():
            if name in self.scene.participants:
                ch.bind_scene(self.scene)
                self.world.npcs[name] = "present"
            else:
                self.world.npcs[name] = "elsewhere"
        if card.opening:
            for name in self.scene.participants:
                if name in self.chars:
                    self.chars[name].memory.note_transient(f"opening:{card.opening[:60]}")
        return {
            "ok": True,
            "scene": asdict(self.scene),
            "opening": card.opening,
            "jump": jump,
            "gamma_before": before,
            "gamma_after": self.scene.gamma_for("World"),
            "world_facts": list(self.world.facts),
            "hash_a_intact": all(ch.intact() for ch in self.chars.values()) and self.world.intact(),
        }

    def snapshot(self) -> dict[str, Any]:
        """続き用。Hash-A は参照だけ。核はここに書かない。"""
        return {
            "scene": asdict(self.scene),
            "player": self.player,
            "world_facts": list(self.world.facts),
            "world_unresolved": list(self.world.unresolved),
            "world_npcs": dict(self.world.npcs),
            "world_b": self.world.box.export_b(),
            "zeta": [asdict(z) for z in self.zeta.values()],
            "memories": {
                name: {
                    "persistent": list(ch.memory.persistent),
                    "transient": list(ch.memory.transient),
                }
                for name, ch in self.chars.items()
            },
            "events": [asdict(e) for e in self.events],
            "hash_a": {name: ch.hash_a0 for name, ch in self.chars.items()} | {"World": self.world.hash_a0},
        }

    def restore(self, snap: dict[str, Any]) -> dict[str, Any]:
        """Hash-A が一致するときだけ可変を戻す。壊れた核は修復しない。"""
        if not isinstance(snap, dict):
            return {"ok": False, "reason": "bad_snapshot"}
        claimed = snap.get("hash_a") or {}
        now = {name: ch.hash_a0 for name, ch in self.chars.items()} | {"World": self.world.hash_a0}
        mismatch = [k for k, v in claimed.items() if now.get(k) != v]
        if mismatch:
            return {"ok": False, "reason": "hash_a_mismatch", "mismatch": mismatch}
        sc = snap.get("scene") or {}
        self.scene = SceneCapsule(
            scene_id=str(sc.get("scene_id") or self.scene.scene_id),
            participants=tuple(sc.get("participants") or self.scene.participants),
            location=str(sc.get("location") or self.scene.location),
            objective=str(sc.get("objective") or self.scene.objective),
            current_state=str(sc.get("current_state") or self.scene.current_state),
            unresolved=list(sc.get("unresolved") or []),
            exits=list(sc.get("exits") or self.scene.exits),
            time_label=str(sc.get("time_label") or self.scene.time_label),
        )
        self.player = str(snap.get("player") or self.player)
        self.world.facts = list(snap.get("world_facts") or self.world.facts)
        self.world.unresolved = list(snap.get("world_unresolved") or [])
        self.world.npcs = dict(snap.get("world_npcs") or self.world.npcs)
        payload = snap.get("world_b")
        imported = None
        if payload:
            imported = self.world.box.import_b(payload, allow_evolution=True)
        self.zeta = {}
        for row in snap.get("zeta") or []:
            z = RelationZeta(
                subject=str(row.get("subject") or ""),
                object=str(row.get("object") or ""),
                trust=float(row.get("trust") or 0.0),
                tension=float(row.get("tension") or 0.0),
                distance=float(row.get("distance") or 0.0),
                dissonance=float(row.get("dissonance") or 0.0),
            ).clamp()
            self.zeta[(z.subject, z.object)] = z
        for name, bank in (snap.get("memories") or {}).items():
            if name not in self.chars:
                continue
            self.chars[name].memory.persistent = list((bank or {}).get("persistent") or [])
            self.chars[name].memory.transient = list((bank or {}).get("transient") or [])
        self.events = []
        for row in snap.get("events") or []:
            self.events.append(
                SemanticEvent(
                    speaker=str(row.get("speaker") or ""),
                    action=str(row.get("action") or ""),
                    target=str(row.get("target") or ""),
                    trust_before=float(row.get("trust_before") or 0.0),
                    trust_after=float(row.get("trust_after") or 0.0),
                    tension_before=float(row.get("tension_before") or 0.0),
                    tension_after=float(row.get("tension_after") or 0.0),
                    world_committed=bool(row.get("world_committed")),
                    utterance=str(row.get("utterance") or ""),
                )
            )
        self.world.bind(self.scene)
        for ch in self.chars.values():
            ch.bind_scene(self.scene)
        if not self.world.intact() or not all(ch.intact() for ch in self.chars.values()):
            return {"ok": False, "reason": "integrity_failure"}
        return {
            "ok": True,
            "imported": imported,
            "events": len(self.events),
            "hash_a_moved": False,
        }

    def save(self, path: str | Path) -> Path:
        dest = Path(path)
        dest.write_text(json.dumps(self.snapshot(), ensure_ascii=False, indent=2), encoding="utf-8")
        return dest

    def load(self, path: str | Path) -> dict[str, Any]:
        snap = json.loads(Path(path).read_text(encoding="utf-8"))
        return self.restore(snap)


RoleplayEngine = CapsuleRoleplayEngine


VOICE = {
    "Alice": {
        "強がる": "……別に、お前を助けたいわけじゃない。",
        "認める": "……信用してなきゃ、ここにはいない。",
        "素直に頼む": "……悪い。手を貸してくれ。",
        "嘘をつく": "一人でどうにかなる。問題ない。",
        "取引を持ちかける": "代わりに一つ、条件を出す。",
        "話題を逸らす": "……それより、空がうるさいな。",
        "拒絶する": "今は無理だ。近づくな。",
        "黙る": "…………。",
    },
    "Marisa": {
        "強がる": "助けが要る、とか言うつもりはねぇぜ。",
        "認める": "信用してるかって？ …まあ、ゼロじゃねえだろ。",
        "素直に頼む": "悪い。手を貸せ。",
        "嘘をつく": "一人で片づく。問題なしだ。",
        "取引を持ちかける": "取引だ。条件を出せ。",
        "話題を逸らす": "それより、森の奥がうるさいな。",
        "拒絶する": "今は無理だぜ。",
        "黙る": "……ちっ。",
    },
}


def default_generator(
    actor: str,
    target: str,
    move: str,
    stimulus: str,
    zeta: RelationZeta,
    frame: dict,
) -> ProposedEvent:
    """演算器の既定実装。API は持たない。状態から発話が自然発生する。"""
    _ = (stimulus, frame)
    table = VOICE.get(actor) or VOICE["Alice"]
    utterance = table.get(move, "……そう。")
    trust_delta, tension_delta = 0.0, 0.0
    emotion = ""
    if move == "認める":
        trust_delta, tension_delta, emotion = 0.09, -0.12, "+trust"
    elif move == "強がる":
        trust_delta, tension_delta, emotion = 0.02, -0.04, "conceal"
    elif move == "素直に頼む":
        trust_delta, tension_delta, emotion = 0.08, -0.10, "+trust"
    elif move == "嘘をつく":
        trust_delta, tension_delta, emotion = -0.06, 0.08, "dissonance"
    elif move == "拒絶する":
        trust_delta, tension_delta, emotion = -0.05, 0.10, "push"
    elif move == "黙る":
        tension_delta, emotion = 0.03, "freeze"
    return ProposedEvent(
        speaker=actor,
        action=move,
        target=target,
        utterance=utterance,
        emotional_delta=emotion,
        trust_delta=trust_delta,
        tension_delta=tension_delta,
    )


# ---------------------------------------------------------------------------
# 既定の Alice / Marisa 封入
# ---------------------------------------------------------------------------


def alice_inner() -> Inner:
    return Inner(
        Alpha(rules=("核を動かさない", "今のγ住所の外を補完しない", "βとΔを混ぜない", "別人の核を名乗らない")),
        Beta(
            name="Alice",
            tone="短い。少し高い壁。丁寧語は稀。",
            center="人形と自制",
            values=("自分から謝らない", "助けても助けたいとは言わない", "強気を基調にする"),
        ),
        facts=(
            BetaFact("A-1", "役", "人形使い"),
            BetaFact("A-2", "基調", "強気"),
        ),
    )


def marisa_inner() -> Inner:
    return Inner(
        Alpha(rules=("核を動かさない", "今のγ住所の外を補完しない", "βとΔを混ぜない", "別人の核を名乗らない")),
        Beta(
            name="Marisa",
            tone="砕けた男言葉。だぜ / だな。",
            center="魔法と蒐集",
            values=("実力", "派手さ", "借りは返す"),
        ),
        facts=(
            BetaFact("M-1", "役", "魔法使い"),
            BetaFact("M-2", "基調", "直球"),
        ),
    )


def forest_scene() -> SceneCapsule:
    return builtin_scenes()[0].scene


def builtin_scenes() -> list[SceneCard]:
    return [
        SceneCard(
            scene=SceneCapsule(
                scene_id="forest-gate",
                participants=("Alice", "Marisa"),
                location="魔法の森の入口",
                objective="助けと協力の距離を決める",
                current_state="対峙。未契約",
                unresolved=["Marisaは助けが必要", "Aliceは自分から謝れない"],
                exits=["協力", "拒絶", "取引", "forest-deal"],
                time_label="2026-09-07",
            ),
            links=("forest-deal", "kirisame-house", "alice-house"),
            opening="夕方の森。入口に二人。まだ契約はない。",
        ),
        SceneCard(
            scene=SceneCapsule(
                scene_id="forest-deal",
                participants=("Alice", "Marisa"),
                location="森の奥の空き地",
                objective="条件を決める",
                current_state="取引の席",
                unresolved=["条件が空"],
                exits=["協力", "決裂", "forest-gate"],
                time_label="2026-09-07",
            ),
            links=("forest-gate",),
            opening="空き地に丸太が一本ある。条件はまだ書いていない。",
        ),
        SceneCard(
            scene=SceneCapsule(
                scene_id="kirisame-house",
                participants=("Alice", "Marisa"),
                location="霧雨魔法店",
                objective="借りたものと研究の話",
                current_state="店の中。埃と魔導書",
                unresolved=["返していない本がある"],
                exits=["forest-gate", "alice-house"],
                time_label="2026-09-07",
            ),
            links=("forest-gate", "alice-house"),
            opening="テーブルの上に借り物が残っている。",
        ),
        SceneCard(
            scene=SceneCapsule(
                scene_id="alice-house",
                participants=("Alice", "Marisa"),
                location="七色の人形遣いの家",
                objective="人形部屋での距離",
                current_state="客を上げた直後",
                unresolved=["客を通した理由"],
                exits=["forest-gate", "kirisame-house"],
                time_label="2026-09-07",
            ),
            links=("forest-gate", "kirisame-house"),
            opening="棚の人形がこちらを見ている。紅魔館はここではない。",
        ),
    ]


def make_demo_engine() -> CapsuleRoleplayEngine:
    alice = CharacterActor(
        alice_inner(),
        constraint="自分から謝れない",
        goal="Marisaに協力する",
    )
    marisa = CharacterActor(
        marisa_inner(),
        constraint="Aliceを信用していない",
        goal="助けを得る",
    )
    world = WorldActor(setting="幻想郷・二次創作実験", location="魔法の森")
    engine = CapsuleRoleplayEngine(world, [alice, marisa], forest_scene())
    engine.relate("Alice", "Marisa", trust=0.42, tension=0.71)
    engine.relate("Marisa", "Alice", trust=0.28, tension=0.66)
    alice.memory.note_persistent("初期: Alice trust(Marisa)=0.42 tension=0.71")
    marisa.memory.note_persistent("初期: Marisa は Alice を信用していない")
    return engine


def demo() -> None:
    eng = make_demo_engine()
    print("Hash-A Alice", eng.chars["Alice"].hash_a0[:16])
    print("Hash-A Marisa", eng.chars["Marisa"].hash_a0[:16])
    print("frame Alice", eng.frame_for("Alice")["candidates"])
    step = eng.user_says("お前、本当に俺を信用してるのか？", speaker="Marisa", target="Alice")
    print("utterance", step["utterance"])
    print("zeta", step["commit"]["zeta"])
    print("world before claim", eng.world.facts)
    naked = eng.claim_world("Alice", "昨日、紅魔館に行ったんだ", authorize=False)
    print("unauthorized fact?", naked["wrote_world"], naked["write_reason"])
    sealed = eng.claim_world("Alice", "昨日、紅魔館に行ったんだ", authorize=True)
    print("authorized fact?", sealed["wrote_world"], eng.world.facts)


if __name__ == "__main__":
    demo()
