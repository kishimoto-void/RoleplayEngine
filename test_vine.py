#!/usr/bin/env python3
from __future__ import annotations

import unittest

from roleplay_engine import make_demo_engine
from stage_marisa import follow
from vine import study


class TestVine(unittest.TestCase):
    def test_tea_does_not_pull_grimoire(self):
        eng = make_demo_engine()
        follow(eng, "ちょっと神社寄るぜ", jump=False)
        vine = study(eng, "茶")
        self.assertEqual(vine["kind"], "prop")
        self.assertEqual(vine["gamma"]["topic"], "hakurei-shrine")
        self.assertEqual(vine["delta"]["場"], ["茶"])
        blob = str(vine["delta"])
        self.assertNotIn("魔導書", blob)
        self.assertFalse(vine["contaminated"])

    def test_shop_does_not_pull_tea(self):
        eng = make_demo_engine()
        vine = study(eng, "霧雨魔法店")
        self.assertEqual(vine["gamma"]["topic"], "kirisame-house")
        self.assertIn("魔導書", vine["delta"]["場"])
        self.assertNotIn("茶", vine["delta"]["場"])
        self.assertFalse(vine["contaminated"])

    def test_person_does_not_take_other_kit(self):
        eng = make_demo_engine()
        follow(eng, "ちょっと神社寄るぜ", jump=False)
        vine = study(eng, "Alice")
        self.assertEqual(vine["delta"]["所持"].get("Alice"), ["人形"])
        self.assertNotIn("Marisa", vine["delta"]["所持"])
        self.assertNotIn("ミニ八卦炉", str(vine["delta"]["所持"]))

    def test_unknown_seed_is_off_vine(self):
        eng = make_demo_engine()
        vine = study(eng, "聖杯")
        self.assertEqual(vine["kind"], "unknown")
        self.assertIn("聖杯", vine["off_vine"])


if __name__ == "__main__":
    unittest.main()
