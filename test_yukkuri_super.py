#!/usr/bin/env python3
from __future__ import annotations

import unittest

from yukkuri_holes import fill_slot, open_slot
from yukkuri_super import pasteable, super_make, title_of


SAMPLE = "魔理沙が森でキノコを探してたら、霊夢に会って神社に行くことになった"


class TestSuper(unittest.TestCase):
    def test_pasteable_has_title_and_ending(self):
        out = super_make(SAMPLE)
        self.assertIn("【タイトル】", out["script"])
        self.assertIn("ゆっくりしていってね", out["script"])
        self.assertIn("【不明／埋めない】", out["script"])
        self.assertFalse(out["panel"]["world_written"])
        self.assertFalse(out["panel"]["llm_authority"])
        self.assertTrue(out["ok"])

    def test_title_from_material(self):
        self.assertIn("キノコ", title_of({"facts": ["キノコを探す", "神社へ行く"], "places": ["博麗神社"]}))

    def test_export(self):
        from pathlib import Path
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "script.txt"
            out = super_make(SAMPLE, out=path)
            self.assertTrue(path.exists())
            self.assertIn("魔理沙「", path.read_text(encoding="utf-8"))
            self.assertEqual(out["export"], str(path))

    def test_retry_recovers_from_finished_sum(self):
        hole = open_slot("start", {"facts": ["キノコを探す"]}, [])
        n = {"i": 0}

        def flaky(_prompt: str) -> str:
            n["i"] += 1
            if n["i"] == 1:
                return '{"answer": "完成脚本"}'
            return '{"play": [{"speaker": "魔理沙", "text": "今日は森だぜ"}]}'

        filled = fill_slot(hole, flaky, retries=1)
        self.assertTrue(filled["ok"])
        self.assertEqual(n["i"], 2)


if __name__ == "__main__":
    unittest.main()
