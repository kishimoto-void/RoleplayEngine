#!/usr/bin/env python3
"""1 + ? = 0。穴を演じ、index で見る。"""
from __future__ import annotations

import json
import unittest

from hole_play import judge_index, open_hole, play_hole, stub_llm, sync_index
from roleplay_engine import make_demo_engine


class TestIndex(unittest.TestCase):
    def test_sync_writes_closed_words_only(self):
        eng = make_demo_engine()
        a0 = eng.chars["Alice"].hash_a0
        out = sync_index(eng, "Alice")
        self.assertTrue(out["ok"])
        self.assertTrue(out["gamma_index"])
        fields = {row["field"] for row in out["delta_index"]}
        self.assertEqual(fields, {"立場", "状態"})
        self.assertEqual(eng.chars["Alice"].hash_a0, a0)
        self.assertFalse(out["hash_a_moved"])


class TestHole(unittest.TestCase):
    def test_equation_is_incomplete(self):
        eng = make_demo_engine()
        sync_index(eng, "Alice")
        hole = open_hole(eng, "Alice", "お前、本当に俺を信用してるのか？")
        self.assertEqual(hole.form, "1 + ? = 0")
        self.assertEqual(hole.open, "?")
        self.assertIn("1=", hole.start)
        self.assertIn("0=回答見出し", hole.goal)
        self.assertNotIn("完成", hole.equation())

    def test_llm_acts_the_hole_not_the_sum(self):
        eng = make_demo_engine()
        out = play_hole(eng, "お前、本当に俺を信用してるのか？")
        self.assertTrue(out["ok"])
        self.assertEqual(out["form"], "1 + ? = 0")
        self.assertEqual(out["play"], "……信用してなきゃ、ここにはいない。")
        self.assertTrue(out["kari"])
        self.assertTrue(out["index_after"]["delta"])
        self.assertTrue(out["hash_a_intact"])

    def test_finished_sum_is_rejected(self):
        hole = open_hole(make_demo_engine(), "Alice", "信用してるのか？")
        judged = judge_index(hole, {"answer": "はい、信用しています。"})
        self.assertFalse(judged["ok"])
        self.assertEqual(judged["kind"], "finished")

    def test_free_text_is_not_index(self):
        hole = open_hole(make_demo_engine(), "Alice", "信用してるのか？")
        judged = judge_index(hole, "はい、信用しています。")
        self.assertFalse(judged["ok"])
        self.assertEqual(judged["kind"], "free_text")

    def test_widen_is_caught(self):
        eng = make_demo_engine()
        hole = open_hole(eng, "Alice", "どこにいる？")

        def bad(_prompt: str) -> str:
            return json.dumps({"play": "今は紅魔館にいる。", "kari": {}}, ensure_ascii=False)

        out = play_hole(eng, "どこにいる？", llm=bad, sync=True)
        self.assertIn("紅魔館", out["play"])
        # 演技は残せるが、index 判定は widen を記録する
        judged = judge_index(hole, bad(""))
        self.assertEqual(judged["kind"], "widen")


if __name__ == "__main__":
    unittest.main()
