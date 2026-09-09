#!/usr/bin/env python3
from __future__ import annotations

import unittest

from rack import RackCapsule
from stroll import Stroll


class TestRack(unittest.TestCase):
    def test_no_new_person_capsule(self):
        rack = RackCapsule()
        self.assertFalse(rack.put("immutable", "核を足す")["ok"])
        self.assertTrue(rack.put("trace", "また明日来るよ", place="engawa")["ok"])
        self.assertFalse(rack.put("trace", "x")["wrote_world"])

    def test_sleep_drops_foam_keeps_trace(self):
        rack = RackCapsule()
        rack.put("transient", "今日寒いな")
        rack.put("trace", "また明日来るよ", place="engawa")
        rack.sleep()
        self.assertEqual(rack.of("transient"), [])
        self.assertEqual(rack.traces_at("engawa"), ["また明日来るよ"])
        self.assertEqual(rack.traces_at("torii"), [])

    def test_stroll_uses_rack(self):
        st = Stroll()
        st.move("sandou")
        st.move("keidai")
        st.move("engawa")
        st.mark("また明日来るよ")
        st.sleep()
        st.move("sandou")
        st.move("keidai")
        st.move("engawa")
        self.assertIn("また明日来るよ", st.look()["delta"]["跡"])


if __name__ == "__main__":
    unittest.main()
