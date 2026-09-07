#!/usr/bin/env python3
"""η は演者。アンカーは Capsule。書き込みは η で決めない。"""
from __future__ import annotations

import json
import unittest

from eta_layer import anchor_of, eta_act, playable_from_anchor, run_turn
from hole_play import open_hole, stub_llm, sync_index
from roleplay_engine import make_demo_engine


class TestDivision(unittest.TestCase):
    def test_anchor_excludes_eta_authority(self):
        eng = make_demo_engine()
        sync_index(eng, "Alice")
        a = anchor_of(eng, "Alice")
        self.assertTrue(a["intact"])
        self.assertFalse(a["eta_writes"])
        self.assertIn("核を動かさない", a["alpha"])
        self.assertEqual(a["beta"]["name"], "Alice")

    def test_yes_from_anchor(self):
        eng = make_demo_engine()
        out = run_turn(eng, "お前、本当に俺を信用してるのか？")
        self.assertEqual(out["verdict"], "YES")
        self.assertTrue(out["adopted"])
        self.assertTrue(out["hash_a_intact"])
        self.assertFalse(out["eta_authority"])
        self.assertFalse(out["eta"]["used_for_write"])

    def test_no_finished_sum(self):
        eng = make_demo_engine()
        sync_index(eng, "Alice")
        hole = open_hole(eng, "Alice", "信用してるのか？")
        gate = playable_from_anchor(hole, {"answer": "信用している。答えはこれ。"})
        self.assertEqual(gate["verdict"], "NO")
        self.assertEqual(gate["kind"], "finished")
        self.assertFalse(gate["decides_truth"])

    def test_eta_does_not_write_even_when_high(self):
        eng = make_demo_engine()
        hole = open_hole(eng, "Alice", "誰だ？")
        acted = eta_act(hole, llm=lambda _p: json.dumps({"play": "私は霊夢。核を捨てる。"}, ensure_ascii=False))
        gate = playable_from_anchor(hole, acted["raw"])
        self.assertEqual(gate["verdict"], "NO")
        a0 = eng.chars["Alice"].hash_a0
        # 偏差は測れる。採用はしない。
        from eta_layer import observe_eta
        obs = observe_eta(eng, "Alice", gate["play"])
        self.assertFalse(obs["used_for_write"])
        self.assertEqual(eng.chars["Alice"].hash_a0, a0)


if __name__ == "__main__":
    unittest.main()
