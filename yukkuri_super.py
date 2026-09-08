#!/usr/bin/env python3
"""SuperGrok 向けの表側。

貼れる台本にする。穴は残す。
タイトルと挨拶とオチは演技。素材の不明は残す。
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Optional

from yukkuri_holes import FORM, HEADING, SLOTS, compose_holes, stub_llm


def title_of(material: dict[str, Any]) -> str:
    facts = list(material.get("facts") or [])
    places = list(material.get("places") or [])
    blob = " ".join(facts + places)
    if "キノコ" in blob and "神社" in blob:
        return "森でキノコ探してたら神社行きになった件"
    if places:
        return f"{places[0]}で起きた件"
    return "素材から作った件"


def pasteable(bundle: dict[str, Any]) -> str:
    material = bundle["material"]
    title = title_of(material)
    lines = [
        f"【タイトル】{title}",
        "",
        "霊夢「ゆっくりしていってね！」",
        "",
    ]
    for name in SLOTS:
        slot = bundle["holes"][name]
        lines.append(f"【{HEADING[name]}】")
        lines.append(slot.get("script") or "")
        lines.append("")
    unknown = material.get("unknown") or []
    if unknown:
        lines.append("【不明／埋めない】")
        for u in unknown:
            lines.append(f"- {u}")
        lines.append("")
    lines.append("霊夢「今日はここまで。ゆっくりしていってね！」")
    return "\n".join(lines).strip() + "\n"


def panel(bundle: dict[str, Any]) -> dict[str, Any]:
    holes = bundle.get("holes") or {}
    return {
        "form": FORM,
        "title": title_of(bundle.get("material") or {}),
        "facts": list((bundle.get("material") or {}).get("facts") or []),
        "unknown": list((bundle.get("material") or {}).get("unknown") or []),
        "slots_ok": {name: bool(holes.get(name, {}).get("ok")) for name in SLOTS},
        "rejected": list(bundle.get("rejected") or []),
        "world_written": False,
        "llm_authority": False,
    }


def export_script(text: str, path: str | Path) -> Path:
    dest = Path(path)
    dest.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")
    return dest


def super_make(
    text: str,
    llm: Optional[Callable[[str], str]] = None,
    out: str | Path | None = None,
    mode: str = "yukkuri",
) -> dict[str, Any]:
    bundle = compose_holes(text, llm=llm or stub_llm, mode=mode)
    script = pasteable(bundle)
    wrote = None
    if out:
        wrote = str(export_script(script, out))
    return {
        **bundle,
        "product": "ゆっくり実況台本メーカー / SuperGrok",
        "script": script,
        "panel": panel(bundle),
        "export": wrote,
    }
