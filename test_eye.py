#!/usr/bin/env python3
from __future__ import annotations

import unittest

from eye import compare, look
from roleplay_engine import make_demo_engine
from stage_marisa import follow


class TestEye(unittest.TestCase):
    def test_world_does_not_hold_kit(self):
        eng = make_demo_engine()
        follow(eng, "ちょっと神社寄るぜ", jump=False)
        view = look(eng, "茶", "World")
        self.assertEqual(view["delta"]["場"], ["茶"])
        self.assertEqual(view["delta"]["所持"], {})

    def test_alice_does_not_see_furnace_as_hers(self):
        eng = make_demo_engine()
        follow(eng, "ちょっと神社寄るぜ", jump=False)
        view = look(eng, "茶", "Alice")
        self.assertEqual(view["delta"]["所持"].get("Alice"), ["人形"])
        self.assertNotIn("Marisa", view["delta"]["所持"])
        self.assertNotIn("ミニ八卦炉", str(view["delta"]["所持"]))
        self.assertFalse(view["contaminated"])

    def test_same_seed_four_eyes(self):
        eng = make_demo_engine()
        follow(eng, "ちょっと神社寄るぜ", jump=False)
        out = compare(eng, "茶")
        self.assertTrue(out["same_gamma"])
        self.assertFalse(out["store"])
        self.assertIn("ミニ八卦炉", str(out["views"]["Marisa"]["delta"]["所持"]))
        self.assertNotIn("ミニ八卦炉", str(out["views"]["Alice"]["delta"]["所持"]))
        self.assertEqual(out["views"]["audience"]["delta"]["所持"], {})


if __name__ == "__main__":
    unittest.main()
