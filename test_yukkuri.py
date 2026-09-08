#!/usr/bin/env python3
from __future__ import annotations

import unittest

from yukkuri_maker import convert, parse_scenario, parse_source


SAMPLE = "魔理沙が森でキノコを探してたら、霊夢に会って神社に行くことになった"
SCENARIO = """1. 魔理沙が森へ行く
2. キノコを探す
3. 神社へ向かう
4. 霊夢と会話する"""


class TestParse(unittest.TestCase):
    def test_splits_material(self):
        m = parse_source(SAMPLE)
        self.assertIn("魔理沙", m.characters)
        self.assertIn("霊夢", m.characters)
        self.assertTrue(any("森" in p or "神社" in p for p in m.places))
        self.assertIn("神社へ行く理由は書かれていない", m.unknown)

    def test_scenario_rows(self):
        self.assertEqual(len(parse_scenario(SCENARIO)), 4)


class TestConvert(unittest.TestCase):
    def test_sample_script_looks_like_yukkuri(self):
        out = convert(SAMPLE)
        script = out["script"]
        self.assertIn("魔理沙「", script)
        self.assertIn("霊夢「", script)
        self.assertIn("キノコ", script)
        self.assertIn("神社", script)
        self.assertFalse(out["score"]["world_written"])
        self.assertGreater(out["score"]["acted_lines"], 0)
        self.assertGreater(out["score"]["source_lines"], 0)

    def test_no_acting_keeps_written_only(self):
        out = convert(SAMPLE, acting=False)
        self.assertEqual(out["score"]["acted_lines"], 0)

    def test_follow_mode_keeps_step_order(self):
        out = convert(SCENARIO, mode="follow")
        kinds = [b["kind"] for b in out["beats"]]
        self.assertEqual(kinds[0], "go-forest")
        self.assertIn("forest-search", kinds)
        self.assertIn("go-shrine", kinds)


if __name__ == "__main__":
    unittest.main()
