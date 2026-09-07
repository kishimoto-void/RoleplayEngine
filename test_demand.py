#!/usr/bin/env python3
"""需要の高い面。核は触らない。"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from roleplay_engine import make_demo_engine


class TestStatus(unittest.TestCase):
    def test_status_does_not_dump_full_history(self):
        eng = make_demo_engine()
        st = eng.status()
        self.assertIn("scene", st)
        self.assertIn("relations", st)
        self.assertTrue(st["intact"]["Alice"])
        self.assertEqual(st["hash_a"]["Alice"], eng.chars["Alice"].hash_a0)
        self.assertNotIn("control_prompt", st)


class TestSaveLoad(unittest.TestCase):
    def test_roundtrip_keeps_zeta_and_hash_a(self):
        eng = make_demo_engine()
        a0 = eng.chars["Alice"].hash_a0
        eng.user_says("お前、本当に俺を信用してるのか？", speaker="Marisa", target="Alice")
        trust = eng.zeta_of("Alice", "Marisa").trust
        self.assertAlmostEqual(trust, 0.51)
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "session.json"
            eng.save(path)
            other = make_demo_engine()
            out = other.load(path)
        self.assertTrue(out["ok"])
        self.assertAlmostEqual(other.zeta_of("Alice", "Marisa").trust, 0.51)
        self.assertEqual(other.chars["Alice"].hash_a0, a0)
        self.assertTrue(other.chars["Alice"].intact())
        self.assertEqual(other.events[-1].utterance, "……信用してなきゃ、ここにはいない。")

    def test_reject_foreign_hash_a(self):
        eng = make_demo_engine()
        snap = eng.snapshot()
        snap["hash_a"]["Alice"] = "0" * 64
        other = make_demo_engine()
        out = other.restore(snap)
        self.assertFalse(out["ok"])
        self.assertEqual(out["reason"], "hash_a_mismatch")
        self.assertAlmostEqual(other.zeta_of("Alice", "Marisa").trust, 0.42)


class TestTickAndRepeat(unittest.TestCase):
    def test_tick_without_user(self):
        eng = make_demo_engine()
        first = eng.user_says("助けてくれ", speaker="Marisa", target="Alice")
        self.assertEqual(first["commit"]["event"]["speaker"], "Alice")
        second = eng.tick()
        self.assertTrue(second["ok"])
        self.assertNotEqual(second["commit"]["event"]["speaker"], "Alice")
        self.assertEqual(second["commit"]["event"]["speaker"], "Marisa")
        self.assertTrue(eng.chars["Marisa"].intact())
        self.assertNotIn("助けたいわけじゃない", second["utterance"])

    def test_same_stimulus_does_not_clone_line(self):
        eng = make_demo_engine()
        a = eng.user_says("助けてくれ", speaker="Marisa", target="Alice")
        b = eng.user_says("助けてくれ", speaker="Marisa", target="Alice")
        self.assertEqual(a["utterance"], "……別に、お前を助けたいわけじゃない。")
        self.assertNotEqual(b["utterance"], a["utterance"])


class TestSceneExit(unittest.TestCase):
    def test_unknown_exit_is_rejected(self):
        out = make_demo_engine().enter("紅魔館")
        self.assertFalse(out["ok"])
        self.assertEqual(out["reason"], "no_exit")

    def test_listed_exit_rebinds_without_moving_hash_a(self):
        eng = make_demo_engine()
        a0 = eng.chars["Alice"].hash_a0
        out = eng.enter("取引", location="森の奥の空き地", scene_id="forest-deal")
        self.assertTrue(out["ok"])
        self.assertEqual(eng.scene.scene_id, "forest-deal")
        self.assertEqual(eng.world.rt.filt["topic"], "forest-deal")
        self.assertEqual(eng.chars["Alice"].hash_a0, a0)
        self.assertTrue(eng.chars["Alice"].intact())


if __name__ == "__main__":
    unittest.main()
