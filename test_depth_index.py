#!/usr/bin/env python3
from __future__ import annotations

import unittest

from depth_index import depth_view, know_places, remember
from roleplay_engine import make_demo_engine
from stage_marisa import follow


class TestDepth(unittest.TestCase):
    def test_places_live_in_gamma(self):
        eng = make_demo_engine()
        out = know_places(eng)
        self.assertTrue(out["ok"])
        self.assertIn("hakurei-shrine", out["gamma_topics"])
        self.assertIn("kirisame-house", out["gamma_topics"])
        self.assertFalse(out["hash_a_moved"])

    def test_match_opens_delta_then_delta2(self):
        eng = make_demo_engine()
        follow(eng, "ちょっと神社寄るぜ", jump=False)
        out = remember(eng)
        self.assertTrue(out["ok"])
        depth = out["depth"]
        self.assertTrue(depth["gamma"]["match"])
        self.assertEqual(depth["gamma"]["topic"], "hakurei-shrine")
        self.assertIn("茶", depth["delta"]["props"])
        self.assertTrue(depth["delta2"])
        self.assertEqual(depth["delta2"][0]["next"], "縁側で茶")
        self.assertFalse(depth["delta2"][0]["writes"])
        self.assertFalse(depth["store"])
        self.assertTrue(out["hash_a_intact"])

    def test_no_match_no_delta2(self):
        eng = make_demo_engine()
        eng.scene.scene_id = "moon"
        view = depth_view(eng)
        self.assertFalse(view["gamma"]["match"])
        self.assertEqual(view["delta2"], [])


if __name__ == "__main__":
    unittest.main()
