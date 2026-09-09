#!/usr/bin/env python3
from __future__ import annotations

import unittest

from gravity import analyze, get, lean, peak, set_weight
from npc_cast import line_of
from voice_stock import pick


class TestGravity(unittest.TestCase):
    def tearDown(self) -> None:
        set_weight("Marisa", now=0.15, comfort=0.05, curiosity=0.35, possession=0.25, duty=0.05, face=0.15)
        set_weight("Reimu", now=0.40, comfort=0.30, curiosity=0.10, possession=0.05, duty=0.10, face=0.05)

    def test_default_peaks(self):
        self.assertEqual(peak("Reimu"), "now")
        self.assertEqual(peak("Marisa"), "curiosity")
        self.assertEqual(analyze("Reimu")["store"], False)

    def test_shift_changes_lean(self):
        set_weight("Marisa", curiosity=0.05, possession=0.05, now=0.70, comfort=0.20)
        self.assertEqual(lean("Marisa", ""), "idle")
        set_weight("Marisa", curiosity=0.70, possession=0.20, now=0.05)
        self.assertEqual(lean("Marisa", ""), "craft")

    def test_pick_follows_weight(self):
        set_weight("Marisa", curiosity=0.8, possession=0.2)
        out = pick("Marisa", "今日はどうだ", "")
        self.assertEqual(out["pattern"], "craft")


if __name__ == "__main__":
    unittest.main()
