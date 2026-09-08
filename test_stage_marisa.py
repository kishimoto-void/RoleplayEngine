#!/usr/bin/env python3
"""魔理沙舞台装置。本体から分離。"""
from __future__ import annotations

import unittest

from roleplay_engine import make_demo_engine
from stage_marisa import follow, mount, natural_turn, suggest


class TestSuggest(unittest.TestCase):
    def test_shrine_cue(self):
        hit = suggest("ちょっと神社寄るぜ")
        self.assertIsNotNone(hit)
        self.assertEqual(hit["scene_id"], "hakurei-shrine")
        self.assertIn("博麗神社", hit["cite"])

    def test_book_cue_goes_to_shop_event(self):
        hit = suggest("あの本、いつ返すんだ")
        self.assertEqual(hit["scene_id"], "kirisame-house")
        self.assertEqual(hit["event"]["event_id"], "borrowed-book")

    def test_no_random_place(self):
        self.assertIsNone(suggest("今日の天気は"))


class TestStageMount(unittest.TestCase):
    def test_follow_moves_without_writing_facts(self):
        eng = make_demo_engine()
        facts0 = list(eng.world.facts)
        a0 = eng.chars["Marisa"].hash_a0
        out = follow(eng, "神社、暇だろ", jump=False)
        self.assertTrue(out["ok"])
        self.assertEqual(eng.scene.scene_id, "hakurei-shrine")
        self.assertEqual(eng.world.facts, facts0)
        self.assertEqual(eng.chars["Marisa"].hash_a0, a0)

    def test_mansion_still_needs_jump(self):
        eng = make_demo_engine()
        mount(eng)
        blocked = follow(eng, "紅魔館の本を借りてくる", jump=False)
        self.assertFalse(blocked.get("ok"))
        self.assertIn(blocked.get("reason"), {"no_route", "no_cue"})
        staged = follow(eng, "紅魔館の本を借りてくる", jump=True)
        self.assertTrue(staged["ok"])
        self.assertFalse(any("行った" in f for f in eng.world.facts))

    def test_natural_turn_keeps_conversation(self):
        eng = make_demo_engine()
        out = natural_turn(eng, "ちょっと神社寄るぜ", speaker="Marisa", jump=False)
        self.assertTrue(out["hash_a_intact"])
        self.assertEqual(out["scene"], "hakurei-shrine")
        self.assertTrue(out["step"]["utterance"])


if __name__ == "__main__":
    unittest.main()
