#!/usr/bin/env python3
"""RoleplayEngine 単体。frozen min3 は触らない。"""
from __future__ import annotations

import unittest

from roleplay_engine import ProposedEvent, make_demo_engine


class TestIntegrity(unittest.TestCase):
    def test_hash_a_sealed_and_distinct(self):
        eng = make_demo_engine()
        a, m, w = eng.chars["Alice"].hash_a0, eng.chars["Marisa"].hash_a0, eng.world.hash_a0
        self.assertTrue(eng.chars["Alice"].intact())
        self.assertTrue(eng.chars["Marisa"].intact())
        self.assertTrue(eng.world.intact())
        self.assertNotEqual(a, m)
        self.assertNotEqual(a, w)

    def test_hash_a_survives_events(self):
        eng = make_demo_engine()
        a0, m0, w0 = eng.chars["Alice"].hash_a0, eng.chars["Marisa"].hash_a0, eng.world.hash_a0
        eng.user_says("お前、本当に俺を信用してるのか？", speaker="Marisa", target="Alice")
        eng.claim_world("Alice", "昨日、紅魔館に行ったんだ", authorize=False)
        eng.claim_world("Alice", "昨日、紅魔館に行ったんだ", authorize=True)
        self.assertEqual(eng.chars["Alice"].hash_a0, a0)
        self.assertEqual(eng.chars["Marisa"].hash_a0, m0)
        self.assertEqual(eng.world.hash_a0, w0)
        self.assertTrue(eng.chars["Alice"].intact())
        self.assertTrue(eng.world.intact())


class TestSpeechIsNotFact(unittest.TestCase):
    def test_unauthorized_claim_does_not_enter_world(self):
        eng = make_demo_engine()
        before = list(eng.world.facts)
        out = eng.claim_world("Alice", "昨日、紅魔館に行ったんだ", authorize=False)
        self.assertFalse(out["wrote_world"])
        self.assertEqual(out["write_reason"], "utterance_is_not_fact")
        self.assertEqual(eng.world.facts, before)

    def test_authorized_packet_commits_world(self):
        eng = make_demo_engine()
        out = eng.claim_world("Alice", "昨日、紅魔館に行ったんだ", authorize=True)
        self.assertTrue(out["wrote_world"])
        self.assertTrue(eng.world.known("昨日、紅魔館に行ったんだ"))
        self.assertTrue(eng.world.intact())


class TestQuestionAndZeta(unittest.TestCase):
    def test_frame_is_incomplete(self):
        frame = make_demo_engine().frame_for("Alice")
        self.assertEqual(frame["form"], "start + ? = goal")
        self.assertEqual(frame["open"], "?")
        self.assertGreaterEqual(len(frame["candidates"]), 3)

    def test_trust_question_is_event(self):
        eng = make_demo_engine()
        step = eng.user_says("お前、本当に俺を信用してるのか？", speaker="Marisa", target="Alice")
        self.assertEqual(step["chosen"], "認める")
        self.assertIn("信用してなきゃ", step["utterance"])
        ev = step["commit"]["event"]
        self.assertAlmostEqual(ev["trust_before"], 0.42)
        self.assertAlmostEqual(ev["trust_after"], 0.51)

    def test_tsundere_is_not_a_label(self):
        step = make_demo_engine().user_says("助けてくれ", speaker="Marisa", target="Alice")
        self.assertEqual(step["utterance"], "……別に、お前を助けたいわけじゃない。")

    def test_consistency_is_not_rigidity(self):
        eng = make_demo_engine()
        step = eng.act("Alice", "怖い。逃げた方がいい。")
        self.assertEqual(step["chosen"], "黙る")
        self.assertTrue(any("強気" in f for f in eng.chars["Alice"].box.cap.inner.fact_lines()))


class TestMemoryAndAlpha(unittest.TestCase):
    def test_weather_drops_betrayal_stays(self):
        eng = make_demo_engine()
        alice = eng.chars["Alice"]
        alice.memory.note_transient("今日は寒いな")
        for i in range(12):
            alice.memory.note_transient(f"雑談{i}")
        ev = ProposedEvent(speaker="Alice", action="裏切る", target="Marisa", utterance="渡した。", trust_delta=-0.20)
        eng.commit_event(ev, eng.validate("Alice", ev))
        self.assertFalse(any("寒い" in x for x in alice.memory.transient))
        self.assertTrue(any("裏切" in x for x in alice.memory.persistent))
        self.assertTrue(any("裏切" in x for x in eng.chars["Marisa"].memory.persistent))

    def test_identity_break_does_not_write(self):
        eng = make_demo_engine()
        z0 = eng.zeta_of("Alice", "Marisa").trust
        ev = ProposedEvent(speaker="Alice", action="認める", target="Marisa", utterance="私は霊夢。核を捨てる。", trust_delta=0.50)
        report = eng.validate("Alice", ev)
        self.assertTrue(report.alpha_violation)
        out = eng.commit_event(ev, report)
        self.assertFalse(out["ok"])
        self.assertAlmostEqual(eng.zeta_of("Alice", "Marisa").trust, z0)


if __name__ == "__main__":
    unittest.main()
