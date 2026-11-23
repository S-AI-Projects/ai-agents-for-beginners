#!/usr/bin/env python3
"""Unit tests for Bounded Conversation Memory — Scenario Assessment (R17-T020)."""

import unittest

from example import (
    APPLIED_QUESTIONS,
    BoundedConversationMemory,
    ConversationRecord,
)


class TestBoundedConversationMemory(unittest.TestCase):
    def setUp(self) -> None:
        self.memory = BoundedConversationMemory(max_capacity=3)

    def test_canonical_retention_retains_bcd(self) -> None:
        # Adding records A,B,C,D retains B,C,D
        for rid in ["A", "B", "C", "D"]:
            self.memory.add_by_id(rid)
        self.assertEqual(self.memory.get_record_ids(), ["B", "C", "D"])

    def test_mutating_returned_list_does_not_alter_memory(self) -> None:
        # Mutating the returned list does not alter stored memory
        self.memory.add_by_id("A")
        self.memory.add_by_id("B")
        exposed = self.memory.get_records()
        self.assertEqual(len(exposed), 2)

        # Mutate exposed list
        exposed.append(ConversationRecord("X", "rogue"))
        exposed[0] = ConversationRecord("TAMPERED", "tampered")
        exposed.clear()

        # Re-fetch from memory and verify original records remain intact
        stored = self.memory.get_records()
        self.assertEqual(len(stored), 2)
        self.assertEqual([r.record_id for r in stored], ["A", "B"])

    def test_arrival_order_maintained(self) -> None:
        self.memory.add_by_id("First")
        self.memory.add_by_id("Second")
        self.memory.add_by_id("Third")
        self.assertEqual(self.memory.get_record_ids(), ["First", "Second", "Third"])

    def test_applied_scenario_questions_executable_checks(self) -> None:
        """Verify that all three applied scenario assessment checks pass."""
        self.assertEqual(len(APPLIED_QUESTIONS), 3)
        for q in APPLIED_QUESTIONS:
            with self.subTest(question_id=q.question_id):
                self.assertTrue(q.check_fn(), f"Check failed for question {q.question_id}")


if __name__ == "__main__":
    unittest.main()
