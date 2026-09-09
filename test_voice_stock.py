#!/usr/bin/env python3
from __future__ import annotations

import unittest

from voice_stock import SOURCE, STOCK, pattern_of, pick
from roleplay_engine import make_demo_engine


class TestStock(unittest.TestCase):
    def test_three_patterns_from_beta(self):
        for name in ("Alice", "Marisa"):
            self.assertEqual(set(STOCK[name]), {"idle", "craft", "wall"})
            self.assertTrue(SOURCE[name]["tone"])
            self.assertTrue(SOURCE[name]["center"])

    def test_stimulus_picks_pattern(self):
        self.assertEqual(pattern_of("縁側で茶"), "idle")
        self.assertEqual(pattern_of("キノコを探す"), "craft")
        self.assertEqual(pattern_of("信用してるのか"), "wall")

    def test_engine_uses_stock(self):
        eng = make_demo_engine()
        idle = eng.act("Marisa", "縁側で茶")
        craft = make_demo_engine().act("Marisa", "キノコを探す")
        wall = make_demo_engine().act("Alice", "助けてくれ")
        self.assertIn("ぜ", idle["utterance"] + "だな")
        self.assertTrue(idle["utterance"])
        self.assertIn("キノコ", craft["utterance"] + "本")
        self.assertIn("助けたいわけじゃない", wall["utterance"])


if __name__ == "__main__":
    unittest.main()
