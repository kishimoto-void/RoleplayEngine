#!/usr/bin/env python3
from __future__ import annotations

import unittest

from stroll import Stroll, walk_script


class TestStroll(unittest.TestCase):
    def test_reimu_not_at_gate(self):
        st = Stroll()
        view = st.look()
        self.assertEqual(view["pos"], "torii")
        self.assertNotIn("霊夢", view["delta"]["人"])
        self.assertTrue(view["empty"] or "霊夢" not in view["delta"]["人"])

    def test_empty_time_at_grounds(self):
        st = Stroll()
        st.move("sandou")
        st.move("keidai")
        quiet = st.wait()
        self.assertEqual(quiet["pos"], "keidai")
        self.assertNotIn("霊夢", quiet["delta"]["人"])
        self.assertTrue(quiet["empty"])
        self.assertFalse(quiet["wrote_world"])

    def test_approach_makes_encounter(self):
        st = Stroll()
        st.move("sandou")
        st.move("keidai")
        st.move("engawa")
        before = st.look()
        self.assertNotIn("霊夢", before["delta"]["人"])
        self.assertIn("茶", before["delta"]["場"])
        after = st.approach("霊夢")
        self.assertIn("霊夢", after["delta"]["人"])
        self.assertTrue(after["delta2"])
        self.assertIn("あら", after["eta"])
        self.assertFalse(after["wrote_world"])
        self.assertEqual(st.facts, [])

    def test_yesterday_stays_on_the_porch(self):
        st = Stroll()
        st.move("sandou")
        st.move("keidai")
        st.move("engawa")
        first = st.approach("霊夢")
        st.mark("また明日来るよ")
        self.assertNotIn("また明日来るよ", first["delta"].get("跡") or [])
        st.sleep()
        st.move("sandou")
        st.move("keidai")
        st.move("engawa")
        seen = st.look()
        self.assertIn("また明日来るよ", seen["delta"]["跡"])
        again = st.approach("霊夢")
        self.assertIn("来たな", again["eta"])
        self.assertFalse(again["wrote_world"])
        self.assertEqual(st.facts, [])


if __name__ == "__main__":
    unittest.main()
