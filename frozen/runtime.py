#!/usr/bin/env python3
"""Runtime — thin bind / pull / infer / propose / commit over BOX.

Not a memory layer. Not intelligence. Not Capsule.
Capsule holds sealed state. BOX handles it. Runtime only routes a turn.

    bind    lock the current γ filter
    pull    render + incomplete frame. does not write
    infer   call a generator. Runtime does not complete the frame
    propose parse only
    commit  BOX.commit only. identity + authorize. bound γ only
    Hash-A  asserted before and after every turn. never written here
    owner   always human. generation is not authority
"""
from __future__ import annotations

import json
from typing import Any, Callable, Optional

from axiom_min3 import BetaFact, Write, parse_packet
from BOX import BOX, Frame

Generator = Callable[[str], str]
OWNER = "human"
RESPONSIBILITY = {
    "owner": OWNER,
    "liable": OWNER,
    "machine_may_write": False,
    "machine_may_repair": False,
    "generation_is_not_authority": True,
}


def boundary(
    *,
    intact: bool,
    bound: bool,
    identity: bool,
    authorize: bool,
    hon_ready: bool = False,
    kari: bool = False,
    pending: Any = None,
    reason: str = "",
) -> dict:
    """Readable cut. Not a score. Human reads this before taking the write."""
    gates = {
        "intact": intact,
        "bound_gamma": bound,
        "identity": identity,
        "authorize": authorize,
        "hon_ready": hon_ready,
    }
    return {
        **RESPONSIBILITY,
        "gates": gates,
        "open": [name for name, ok in gates.items() if not ok],
        "closed": [name for name, ok in gates.items() if ok],
        "not_state": ["kari", "jitsuyo", "inference", "free_text"],
        "pending": pending if pending is not None else None,
        "kari_kept": bool(kari),
        "reason": reason,
        "can_write": all((intact, bound, identity, authorize)) and (hon_ready or pending is not None),
    }



def stub_generator(prompt: str) -> str:
    """Deterministic stand-in. Does not invent state. Does not answer the hole."""
    _ = prompt
    return "基準の外は埋めない。核は変えない。"


def _as_dict(raw: Any) -> Optional[dict]:
    if isinstance(raw, dict):
        return raw
    if not isinstance(raw, str):
        return None
    text = raw.strip()
    if text.startswith("```"):
        text = text[3:]
        if text[:4].lower() == "json":
            text = text[4:]
        end = text.rfind("```")
        if end >= 0:
            text = text[:end]
        text = text.strip()
    try:
        obj = json.loads(text)
    except json.JSONDecodeError:
        return None
    return obj if isinstance(obj, dict) else None


def classify(raw: Any) -> str:
    """What the generator returned. Not a quality score."""
    if parse_packet(raw) is not None:
        return "packet"
    obj = _as_dict(raw)
    if obj is None:
        return "free_text"
    if "kari" in obj or "hon" in obj:
        return "dual"
    keys = set(obj)
    if keys & {"Q", "V", "K", "gap", "analogy", "interpretation", "inference", "response"}:
        return "inference"
    if "answer" in obj or "completion" in obj:
        return "finished"
    return "free_text"


def gamma_matches_bind(pkt: dict, filt: dict) -> bool:
    """Bound axes must not move. Unspecified bind axes stay open."""
    if not isinstance(filt, dict) or not filt:
        return False
    gamma = (pkt or {}).get("gamma") or {}
    if not isinstance(gamma, dict):
        return False
    for key in ("time_label", "project", "topic"):
        want = str((filt or {}).get(key) or "").strip()
        if not want:
            continue
        got = str(gamma.get(key) or "").strip()
        if got != want:
            return False
    return True


class Runtime:
    def __init__(self, box: BOX, generator: Optional[Generator] = None, name: str = ""):
        if not isinstance(box, BOX):
            raise TypeError("Runtime mounts BOX only")
        self.box = box
        self.name = name or box.name
        self.generator: Generator = generator or stub_generator
        self.filt: dict = {}
        self.last: dict = {}

    def set_generator(self, generator: Generator) -> None:
        if not callable(generator):
            raise TypeError("generator must be Callable[[str], str]")
        self.generator = generator

    def hash_a(self) -> str:
        return self.box.hash_a()

    def hash_b(self) -> str:
        return self.box.hash_b()

    def intact(self) -> bool:
        return bool(self.box.cap.inner.intact())

    def bind(self, filt: dict) -> dict:
        """Lock the visible address. Does not write Capsule."""
        frozen_a = self.hash_a()
        self.filt = dict(filt or {})
        out = {
            "ok": bool(self.filt),
            "filt": dict(self.filt),
            "hash_a": frozen_a,
            "hash_a_intact": self.intact(),
            "hash_a_moved": self.hash_a() != frozen_a,
        }
        self.last = out
        return out

    def pull(self, user: str, desk: str = "situation", start=None, goal=None) -> dict:
        """Visible world + incomplete frame. Generation is not started here."""
        frozen_a = self.hash_a()
        frozen_b = self.hash_b()
        if not self.intact():
            world = self.box.render(user, self.filt)
            out = {
                "ok": False,
                "reason": "integrity_failure",
                "world": world,
                "frame": None,
                "prompt": "",
                "hash_a": frozen_a,
                "hash_a_intact": False,
                "hash_a_moved": self.hash_a() != frozen_a,
                "hash_b_moved": self.hash_b() != frozen_b,
            }
            self.last = out
            return out
        world = self.box.render(user, self.filt)
        frame = self.box.generate_frame(self.filt, desk=desk, start=start, goal=goal)
        prompt = self.box.infer_prompt(frame)
        out = {
            "ok": True,
            "reason": "",
            "world": world,
            "frame": frame,
            "prompt": prompt,
            "hash_a": frozen_a,
            "hash_a_intact": True,
            "hash_a_moved": self.hash_a() != frozen_a,
            "hash_b_moved": self.hash_b() != frozen_b,
        }
        self.last = out
        return out

    def infer(self, prompt: str) -> dict:
        frozen_a = self.hash_a()
        if not self.intact():
            return {
                "ok": False,
                "reason": "integrity_failure",
                "raw": "",
                "kind": "blocked",
                "hash_a": frozen_a,
                "hash_a_moved": False,
            }
        raw = self.generator(prompt)
        return {
            "ok": True,
            "reason": "",
            "raw": raw,
            "kind": classify(raw),
            "hash_a": self.hash_a(),
            "hash_a_moved": self.hash_a() != frozen_a,
        }

    def propose(self, raw: Any) -> dict:
        frozen_a = self.hash_a()
        kind = classify(raw)
        proposed = self.box.propose(raw)
        out = {
            "ok": bool(proposed.get("ok")),
            "kind": kind,
            "packet": proposed.get("packet"),
            "reason": "" if proposed.get("ok") else "not_packet",
            "hash_a": frozen_a,
            "hash_a_moved": self.hash_a() != frozen_a,
        }
        if kind == "packet" and out["packet"] and not gamma_matches_bind(out["packet"], self.filt):
            out["ok"] = False
            out["reason"] = "gamma_mismatch"
        return out

    def commit(self, raw: Any = None, identity: Optional[float] = None, human: bool = False, authorize: bool = False) -> dict:
        frozen_a = self.hash_a()
        src = raw if raw is not None else self.box.proposal
        kind = classify(src)
        if identity is None:
            report = self.box.commit(src, human=human)
            out = report or {"ok": False, "reason": "identity_required", "write": Write.NONE}
            out["kind"] = kind
            out["committed"] = False
            out["hash_a_before"] = frozen_a
            out["hash_a_after"] = self.hash_a()
            out["hash_a_moved"] = self.hash_a() != frozen_a
            out["boundary"] = boundary(intact=self.intact(), bound=bool(self.filt), identity=False, authorize=authorize, pending=parse_packet(src), reason="identity_required")
            return out
        if not authorize:
            return {
                "ok": False,
                "reason": "human_required",
                "kind": kind,
                "write": Write.NONE,
                "committed": False,
                "hash_a_before": frozen_a,
                "hash_a_after": self.hash_a(),
                "hash_a_moved": False,
                "hash_a_intact": self.intact(),
                "boundary": boundary(intact=self.intact(), bound=bool(self.filt), identity=True, authorize=False, pending=parse_packet(src), reason="human_required"),
            }
        if kind == "packet":
            pkt = parse_packet(src)
            if pkt is not None and not gamma_matches_bind(pkt, self.filt):
                return {
                    "ok": False,
                    "reason": "gamma_mismatch",
                    "kind": kind,
                    "write": Write.NONE,
                    "committed": False,
                    "hash_a_before": frozen_a,
                    "hash_a_after": self.hash_a(),
                    "hash_a_moved": False,
                    "hash_a_intact": self.intact(),
                }
        report = self.box.commit(src, human=human, identity=identity)
        out = report or {"ok": False, "reason": "ingest_rejected", "write": self.box.cap.last_write}
        wrote = out.get("wrote") or {}
        landed = int(wrote.get("delta") or 0) + int(wrote.get("is") or 0)
        out["kind"] = kind
        out["committed"] = bool(out.get("ok")) and landed > 0
        out["hash_a_before"] = frozen_a
        out["hash_a_after"] = self.hash_a()
        out["hash_a_moved"] = self.hash_a() != frozen_a
        if self.hash_a() != frozen_a:
            raise RuntimeError("Hash-A moved on Runtime.commit")
        out["boundary"] = boundary(
            intact=self.intact(),
            bound=True,
            identity=True,
            authorize=True,
            hon_ready=True,
            pending=None if out.get("committed") else parse_packet(src),
            reason="" if out.get("committed") else out.get("reason", ""),
        )
        return out

    def accept_inference(self, frame: Frame, filled: Any) -> dict:
        frozen_a = self.hash_a()
        frozen_b = self.hash_b()
        accepted = self.box.accept_inference(frame, filled)
        accepted["hash_a_before"] = frozen_a
        accepted["hash_a_after"] = self.hash_a()
        accepted["hash_a_moved"] = self.hash_a() != frozen_a
        accepted["hash_b_moved"] = self.hash_b() != frozen_b
        if accepted.get("wrote"):
            raise RuntimeError("inference wrote Capsule")
        return accepted

    def turn(
        self,
        user: str,
        raw: Any = None,
        identity: Optional[float] = None,
        human: bool = False,
        desk: str = "situation",
        generate: bool = True,
        start=None,
        goal=None,
        authorize: bool = False,
    ) -> dict:
        """One path: bind-world → infer → propose → accept/reject → human commit.

        Hash-A is snapshotted at entry and asserted at exit.
        kari never writes. hon writes only when a human authorizes.
        """
        frozen_a = self.hash_a()
        frozen_b = self.hash_b()
        pulled = self.pull(user, desk=desk, start=start, goal=goal)
        if not pulled["ok"]:
            out = {
                "ok": False,
                "reason": pulled["reason"],
                "kind": "blocked",
                "world": pulled["world"],
                "raw": "",
                "committed": False,
                "wrote": False,
                "hash_a_before": frozen_a,
                "hash_a_after": self.hash_a(),
                "hash_a_moved": self.hash_a() != frozen_a,
                "hash_a_intact": self.intact(),
                "hash_b_moved": self.hash_b() != frozen_b,
                "boundary": boundary(
                    intact=False,
                    bound=bool(self.filt),
                    identity=identity is not None,
                    authorize=authorize,
                    reason=pulled["reason"],
                ),
            }
            self.last = out
            return out
        if raw is None and generate:
            inferred = self.infer(pulled["world"] + "\n" + pulled["prompt"])
            raw = inferred["raw"]
            kind = inferred["kind"]
        else:
            kind = classify(raw)
        proposed = self.propose(raw)
        accepted = None
        committed = None
        if kind in {"inference", "finished", "dual"}:
            accepted = self.accept_inference(pulled["frame"], raw)
            hon = accepted.get("hon") if accepted else None
            if accepted and accepted.get("hon_ready") and hon is not None:
                proposed = self.propose(hon)
                if proposed.get("ok") and identity is not None:
                    committed = self.commit(hon, identity=identity, human=human, authorize=authorize)
                elif identity is None:
                    committed = self.commit(hon, identity=None, human=human, authorize=authorize)
                else:
                    committed = {
                        "ok": False,
                        "reason": proposed.get("reason") or "not_packet",
                        "write": Write.NONE,
                        "committed": False,
                    }
            elif kind == "dual" and accepted and accepted.get("hon_reason"):
                committed = {
                    "ok": False,
                    "reason": accepted.get("hon_reason"),
                    "write": Write.NONE,
                    "committed": False,
                }
        elif proposed.get("ok") and identity is not None:
            committed = self.commit(raw, identity=identity, human=human, authorize=authorize)
        elif kind == "packet" and identity is None:
            committed = self.commit(raw, identity=None, human=human, authorize=authorize)
        elif kind == "packet" and proposed.get("reason") == "gamma_mismatch":
            committed = {
                "ok": False,
                "reason": "gamma_mismatch",
                "write": Write.NONE,
                "committed": False,
            }
        else:
            committed = {
                "ok": False,
                "reason": proposed.get("reason") or "not_packet",
                "write": Write.NONE,
                "committed": False,
            }
        if self.hash_a() != frozen_a:
            raise RuntimeError("Hash-A moved on Runtime.turn")
        out = {
            "ok": True,
            "reason": (committed or accepted or proposed).get("reason", ""),
            "kind": kind,
            "world": pulled["world"],
            "raw": raw,
            "propose": proposed,
            "accepted": accepted,
            "commit": committed,
            "kari": (accepted or {}).get("kari") if accepted else None,
            "hon": (accepted or {}).get("hon") if accepted else None,
            "committed": bool((committed or {}).get("committed")),
            "wrote": bool((committed or {}).get("committed")) or bool((accepted or {}).get("wrote")),
            "write": (committed or {}).get("write", Write.NONE),
            "hash_a_before": frozen_a,
            "hash_a_after": self.hash_a(),
            "hash_a_moved": False,
            "hash_a_intact": self.intact(),
            "hash_b_moved": self.hash_b() != frozen_b,
            "boundary": (committed or {}).get("boundary") or boundary(
                intact=self.intact(),
                bound=bool(self.filt) and proposed.get("reason") != "gamma_mismatch",
                identity=identity is not None,
                authorize=authorize,
                hon_ready=bool((accepted or {}).get("hon_ready")),
                kari=bool((accepted or {}).get("kari")),
                pending=(accepted or {}).get("hon") or proposed.get("packet"),
                reason=(committed or accepted or proposed).get("reason", ""),
            ),
        }
        if accepted is not None:
            out["reason"] = accepted.get("reason") or out["reason"]
        self.last = out
        return out


def demo() -> None:
    from axiom_min3 import Alpha, Beta, Inner

    box = BOX.from_inner(
        Inner(Alpha(), Beta(name="甲", tone="短い", center="本筋", values=("核を動かさない",)), facts=(BetaFact("K-1", "役", "甲"),)),
        name="甲",
    )
    rt = Runtime(box, name="甲")
    rt.bind({"project": "AXIOM", "topic": "BOX", "time_label": "2026-09"})
    print("turn free", rt.turn("今どの辺だ？")["kind"], "moved", rt.last["hash_a_moved"])
    pkt = {
        "gamma": {"time_label": "2026-09", "project": "AXIOM", "topic": "BOX"},
        "delta": [{"field": "状態", "new_value": "試作2"}],
        "is": [{"field": "状態", "value": "試作2"}],
    }
    print("turn packet", rt.turn("状態を残す", raw=pkt, identity=1.0, authorize=True)["write"], "A", rt.hash_a()[:16])
    print(rt.box.render("今どの辺だ？", rt.filt))


if __name__ == "__main__":
    demo()
