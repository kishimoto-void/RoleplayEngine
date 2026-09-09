#!/usr/bin/env python3
from __future__ import annotations

import unittest

from npc_cast import at_place, card, line_of
from stroll import Stroll


class TestCast(unittest.TestCase):
    def test_homes(self):
        self.assertEqual(card("Reimu")["home"], "hakurei-shrine")
        self.assertEqual(card("Marisa")["home"], "kirisame-house")
        self.assertEqual(card("Alice")["home"], "alice-house")
        self.assertEqual(card("Patchouli")["home"], "scarlet-mansion")
        self.assertFalse(card("Reimu")["hash_a"])

    def test_reimu_not_at_gate(self):
        names = [n.name for n in at_place("torii")]
        self.assertNotIn("霊夢", names)
        self.assertTrue(any(n.name == "霊夢" for n in at_place("engawa")))

    def test_approach_uses_cast_line(self):
        st = Stroll()
        st.move("sandou")
        st.move("keidai")
        st.move("engawa")
        after = st.approach("霊夢")
        self.assertEqual(after["eta"], line_of("Reimu", "wall"))
        self.assertFalse(after["wrote_world"])


if __name__ == "__main__":
    unittest.main()
