#!/usr/bin/env python3
"""用意した場面。核は触らない。"""
from __future__ import annotations

import unittest

from roleplay_engine import SceneBook, make_demo_engine


class TestSceneBook(unittest.TestCase):
    def test_loads_prepared_files(self):
        book = SceneBook.default()
        self.assertIn("forest-gate", book.ids())
        self.assertIn("alice-house", book.ids())
        self.assertIn("scarlet-mansion", book.ids())

    def test_write_and_read_card(self):
        import tempfile
        from pathlib import Path

        eng = make_demo_engine()
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "alice-house.json"
            eng.book.save_one("alice-house", path)
            raw = path.read_text(encoding="utf-8")
            self.assertIn("七色の人形遣いの家", raw)
            other = SceneBook.from_dir(td)
            self.assertEqual(other.get("alice-house").scene.location, "七色の人形遣いの家")


class TestPrepare(unittest.TestCase):
    def test_prepare_changes_address_not_facts(self):
        eng = make_demo_engine()
        facts0 = list(eng.world.facts)
        a0 = eng.chars["Alice"].hash_a0
        out = eng.prepare("alice-house")
        self.assertTrue(out["ok"])
        self.assertEqual(eng.scene.location, "七色の人形遣いの家")
        self.assertEqual(eng.world.rt.filt["topic"], "alice-house")
        self.assertEqual(eng.world.facts, facts0)
        self.assertEqual(eng.chars["Alice"].hash_a0, a0)
        self.assertTrue(out["hash_a_intact"])
        frame = eng.frame_for("Alice")
        self.assertIn("七色の人形遣いの家", frame["start"])

    def test_jump_false_blocks_unlinked_mansion(self):
        eng = make_demo_engine()
        out = eng.prepare("scarlet-mansion", jump=False)
        self.assertFalse(out["ok"])
        self.assertEqual(out["reason"], "no_route")
        self.assertEqual(eng.scene.scene_id, "forest-gate")

    def test_jump_true_can_stage_mansion_without_making_it_a_fact(self):
        eng = make_demo_engine()
        out = eng.prepare("scarlet-mansion", jump=True)
        self.assertTrue(out["ok"])
        self.assertEqual(eng.scene.scene_id, "scarlet-mansion")
        self.assertFalse(any("紅魔館" in f for f in eng.world.facts))
        claim = eng.claim_world("Alice", "昨日、紅魔館に行ったんだ", authorize=False)
        self.assertFalse(claim["wrote_world"])

    def test_unknown_scene(self):
        out = make_demo_engine().prepare("moon")
        self.assertFalse(out["ok"])
        self.assertEqual(out["reason"], "unknown_scene")

    def test_linked_prepare_without_jump(self):
        eng = make_demo_engine()
        out = eng.prepare("forest-deal", jump=False)
        self.assertTrue(out["ok"])
        self.assertEqual(eng.scene.location, "森の奥の空き地")


if __name__ == "__main__":
    unittest.main()
