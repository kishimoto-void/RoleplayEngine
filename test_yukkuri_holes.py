#!/usr/bin/env python3
from __future__ import annotations

import json
import unittest

from yukkuri_holes import compose_holes, judge_slot, open_slot, stub_llm


SAMPLE = "魔理沙が森でキノコを探してたら、霊夢に会って神社に行くことになった"


class TestHoles(unittest.TestCase):
    def test_three_slots_are_holes(self):
        hole = open_slot("start", {"facts": ["キノコを探す"]}, [])
        self.assertEqual(hole["form"], "1 + ? = 0")
        self.assertEqual(hole["open"], "?")
        self.assertIn("0=見出し:スタート", hole["goal"])

    def test_finished_sum_rejected(self):
        judged = judge_slot({"answer": "これが完成した脚本です"})
        self.assertFalse(judged["ok"])
        self.assertEqual(judged["kind"], "finished")

    def test_llm_fills_all_three(self):
        out = compose_holes(SAMPLE, llm=stub_llm)
        self.assertTrue(out["ok"])
        self.assertEqual(set(out["holes"]), {"start", "body", "end"})
        self.assertIn("【スタート】", out["script"])
        self.assertIn("【本編】", out["script"])
        self.assertIn("【帰結】", out["script"])
        self.assertIn("キノコ", out["holes"]["start"]["script"])
        self.assertFalse(out["world_written"])
        self.assertFalse(out["llm_authority"])
        self.assertIn("神社へ行く理由は書かれていない", out["material"]["unknown"])


if __name__ == "__main__":
    unittest.main()
