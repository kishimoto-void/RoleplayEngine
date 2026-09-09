#!/usr/bin/env python3
from __future__ import annotations

import unittest

from roleplay_engine import make_demo_engine
from stage_marisa import follow
from x_guard import admit, guard, keep_user_act, quiet_tick


class TestXGuard(unittest.TestCase):
    def test_blocks_intruder(self):
        eng = make_demo_engine()
        self.assertFalse(admit(eng, "霊夢")["ok"])
        self.assertTrue(admit(eng, "Alice")["ok"])

    def test_calm_does_not_jump(self):
        eng = make_demo_engine()
        follow(eng, "ちょっと神社寄るぜ", jump=False)
        here = eng.scene.scene_id
        out = quiet_tick(eng, "縁側でお茶でもする")
        self.assertTrue(out["ok"])
        self.assertEqual(out["scene"], here)
        self.assertEqual(out["scene"], "hakurei-shrine")
        self.assertFalse(out["wrote_world"])
        self.assertIn(out["actor"], ("Alice", "Marisa"))

    def test_false_memory_flagged(self):
        eng = make_demo_engine()
        follow(eng, "ちょっと神社寄るぜ", jump=False)
        g = guard(eng, "昨日、紅魔館で聖杯を拾った")
        self.assertFalse(g["ok"])
        self.assertTrue(any("無い記憶" in r for r in g["reasons"]))

    def test_user_line_is_not_their_act_in_world(self):
        eng = make_demo_engine()
        out = keep_user_act(eng, "昨日、紅魔館で聖杯を拾った", "Marisa")
        self.assertFalse(out["wrote_world"])
        self.assertFalse(out["user_became_fact"])
        self.assertFalse(out["scene_moved"])


if __name__ == "__main__":
    unittest.main()
