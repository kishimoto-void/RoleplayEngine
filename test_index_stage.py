#!/usr/bin/env python3
from __future__ import annotations

import unittest

from index_stage import props_for, read_cast, read_stage, rig
from roleplay_engine import make_demo_engine
from stage_marisa import follow, mount


class TestRig(unittest.TestCase):
    def test_gamma_is_stage(self):
        eng = make_demo_engine()
        mount(eng)
        out = rig(eng)
        self.assertTrue(out["ok"])
        self.assertTrue(out["hash_a_intact"])
        self.assertEqual(out["stage"]["scene_id"], "forest-gate")
        self.assertTrue(out["stage"]["gamma_index"])
        self.assertEqual(out["stage"]["gamma_index"][0]["topic"], "forest-gate")

    def test_delta_holds_cast_and_props(self):
        eng = make_demo_engine()
        follow(eng, "ちょっと神社寄るぜ", jump=False)
        out = rig(eng)
        self.assertEqual(out["stage"]["scene_id"], "hakurei-shrine")
        names = {c["name"] for c in out["cast"]["characters"] if c["立場"]}
        self.assertIn("Marisa", names)
        self.assertIn("茶", out["cast"]["props"])
        self.assertIn("箒", out["cast"]["props"])
        self.assertFalse(any("茶" in f for f in out["world_facts"]))

    def test_speech_does_not_invent_prop(self):
        eng = make_demo_engine()
        rig(eng)
        before = list(read_cast(eng)["props"])
        eng.user_says("昨日、紅魔館で聖杯を拾った", speaker="Marisa", target="Alice")
        after = read_cast(eng)["props"]
        self.assertEqual(before, after)
        self.assertNotIn("聖杯", after)

    def test_kit_without_scene(self):
        self.assertIn("箒", props_for("forest-path", ["Marisa"]))
        self.assertIn("人形", props_for("alice-house", ["Alice"]))


if __name__ == "__main__":
    unittest.main()
