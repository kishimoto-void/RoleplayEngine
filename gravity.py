#!/usr/bin/env python3
"""思考の重心。性格ラベルではない。

次の反応をどちらへ引くかの重み。
Hash-A には入れない。設定してよい。
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

AXES = ("now", "comfort", "curiosity", "possession", "duty", "face")

# Grok 的に読むと、思考は「正しさ」より「何が面白いか／今ここ」に寄る。
# キャラはその寄りの位置が違う。
DEFAULT = {
    "Reimu": {"now": 0.40, "comfort": 0.30, "curiosity": 0.10, "possession": 0.05, "duty": 0.10, "face": 0.05},
    "Marisa": {"now": 0.15, "comfort": 0.05, "curiosity": 0.35, "possession": 0.25, "duty": 0.05, "face": 0.15},
    "Alice": {"now": 0.10, "comfort": 0.15, "curiosity": 0.15, "possession": 0.25, "duty": 0.10, "face": 0.25},
    "Patchouli": {"now": 0.05, "comfort": 0.25, "curiosity": 0.30, "possession": 0.15, "duty": 0.20, "face": 0.05},
    "Grok": {"now": 0.20, "comfort": 0.05, "curiosity": 0.45, "possession": 0.05, "duty": 0.05, "face": 0.20},
}

PULL = {
    "idle": ("now", "comfort"),
    "craft": ("curiosity", "possession"),
    "wall": ("face", "duty"),
}

_STATE: dict[str, dict[str, float]] = {k: dict(v) for k, v in DEFAULT.items()}
_PATH = Path(__file__).resolve().parent / "gravity.json"


def _norm(row: dict[str, float]) -> dict[str, float]:
    out = {a: max(0.0, float(row.get(a, 0.0))) for a in AXES}
    s = sum(out.values()) or 1.0
    return {a: round(out[a] / s, 4) for a in AXES}


def get(name: str) -> dict[str, float]:
    key = name if name in _STATE else {"霊夢": "Reimu", "魔理沙": "Marisa", "アリス": "Alice", "パチュリー": "Patchouli"}.get(name, name)
    if key not in _STATE:
        _STATE[key] = _norm({"curiosity": 1.0})
    return dict(_STATE[key])


def set_weight(name: str, **weights: float) -> dict[str, float]:
    key = name if name in _STATE or name in DEFAULT else {"霊夢": "Reimu", "魔理沙": "Marisa", "アリス": "Alice", "パチュリー": "Patchouli"}.get(name, name)
    cur = dict(_STATE.get(key) or DEFAULT.get(key) or {a: 0.0 for a in AXES})
    cur.update({k: float(v) for k, v in weights.items() if k in AXES})
    _STATE[key] = _norm(cur)
    return dict(_STATE[key])


def peak(name: str) -> str:
    row = get(name)
    return max(row, key=row.get)


def score(name: str, pattern: str) -> float:
    row = get(name)
    return round(sum(row[a] for a in PULL[pattern]), 4)


def lean(name: str, stimulus: str = "", move: str = "") -> str:
    raw = stimulus or ""
    bump = {"idle": 0.0, "craft": 0.0, "wall": 0.0}
    if any(w in raw for w in ("茶", "縁側", "暇", "間", "座", "日和")):
        bump["idle"] += 0.25
    if any(w in raw for w in ("キノコ", "本", "箒", "実験", "人形", "蒐集")):
        bump["craft"] += 0.25
    if any(w in raw for w in ("信用", "助け", "触", "壁", "招")):
        bump["wall"] += 0.25
    if move in ("話題を逸らす", "黙る"):
        bump["idle"] += 0.10
    if move in ("取引を持ちかける",):
        bump["craft"] += 0.10
    if move in ("強がる", "認める", "拒絶する"):
        bump["wall"] += 0.10
    ranked = sorted(
        ("idle", "craft", "wall"),
        key=lambda p: score(name, p) + bump[p],
        reverse=True,
    )
    return ranked[0]


def analyze(name: str) -> dict[str, Any]:
    row = get(name)
    top = peak(name)
    note = {
        "now": "今ここ。先の事件を作らない。",
        "comfort": "楽な場に留まる。動かない時間を捨てない。",
        "curiosity": "面白そうな物へ寄る。物語より発見。",
        "possession": "手元の物と蒐集。触られると壁が出る。",
        "duty": "役割を先に置く。巫女・蔵書・自制。",
        "face": "見られ方。強気や負けずを先に出す。",
    }
    return {
        "name": name,
        "weights": row,
        "peak": top,
        "read": note[top],
        "pull": {p: score(name, p) for p in PULL},
        "store": False,
    }


def save(path: str | Path = _PATH) -> Path:
    dest = Path(path)
    import json

    dest.write_text(
        __import__("json").dumps({k: get(k) for k in _STATE}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return dest


def load(path: str | Path = _PATH) -> dict[str, dict[str, float]]:
    dest = Path(path)
    if not dest.exists():
        return {k: get(k) for k in _STATE}
    import json

    raw = json.loads(dest.read_text(encoding="utf-8"))
    for name, row in (raw or {}).items():
        if isinstance(row, dict):
            set_weight(name, **row)
    return {k: get(k) for k in _STATE}
