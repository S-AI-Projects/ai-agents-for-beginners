"""Automated Unit Tests for Bounded Conversation Memory with State Trace (R17-T044)

Lesson Alignment:
11-agentic-protocols (Agentic Protocols: Context & State Management)

Contract Checks:
1. Bounded capacity holding at most 3 records in arrival order.
2. Canonical scenario: Adding A, B, C, D retains ['B', 'C', 'D'].
3. Defensive copy immutability: External mutations never alter internal state.
4. Intermediate state trace: Records state snapshots after every discrete step.
5. Formal invariants: Capacity <= 3 holds across all execution steps.
"""

import unittest
try:
    from example import (
        BoundedConversationMemory,
        ConversationRecord,
        StateSnapshot,
        InvariantViolationError,
        simulate_canonical_scenario,
    )
except ImportError:
    from .example import (
        BoundedConversationMemory,
        ConversationRecord,
        StateSnapshot,
        InvariantViolationError,
        simulate_canonical_scenario,
    )


class TestBoundedConversationMemory(unittest.TestCase):
    """Unit test suite for bounded conversation memory, state tracing, and formal invariants."""

    def setUp(self):
        self.memory = BoundedConversationMemory(max_capacity=3)

    def test_canonical_scenario_a_b_c_d_retains_b_c_d(self):
        """Canonical requirement: Adding A, B, C, D retains ['B', 'C', 'D'] in arrival order."""
        self.memory.add("A")
        self.memory.add("B")
        self.memory.add("C")
        evicted = self.memory.add("D")

        self.assertEqual(evicted, "A")
        self.assertEqual(self.memory.get_records(), ["B", "C", "D"])
        self.assertEqual(len(self.memory), 3)

    def test_empty_initialization(self):
        """Initialized memory is empty and satisfies invariants."""
        self.assertEqual(len(self.memory), 0)
        self.assertEqual(self.memory.get_records(), [])
        self.assertTrue(self.memory.verify_invariants())

    def test_adding_under_capacity(self):
        """Adding fewer items than capacity preserves all items in arrival order."""
        self.memory.add("X")
        self.memory.add("Y")
        self.assertEqual(self.memory.get_records(), ["X", "Y"])
        self.assertEqual(len(self.memory), 2)
        self.assertTrue(self.memory.verify_invariants())

    def test_adding_exact_capacity(self):
        """Adding exactly capacity items retains all items without eviction."""
        evicted1 = self.memory.add("1")
        evicted2 = self.memory.add("2")
        evicted3 = self.memory.add("3")

        self.assertIsNone(evicted1)
        self.assertIsNone(evicted2)
        self.assertIsNone(evicted3)
        self.assertEqual(self.memory.get_records(), ["1", "2", "3"])
        self.assertEqual(len(self.memory), 3)

    def test_fifo_sliding_window_multiple_overflows(self):
        """Multiple sequential additions properly slide the window retaining the newest 3."""
        for item in ["A", "B", "C", "D", "E", "F"]:
            self.memory.add(item)

        self.assertEqual(self.memory.get_records(), ["D", "E", "F"])
        self.assertEqual(len(self.memory), 3)
        self.assertTrue(self.memory.verify_invariants())

    def test_defensive_copy_immutability_append(self):
        """Appending to the list returned by get_records() does not alter internal memory."""
        self.memory.add("A")
        self.memory.add("B")

        external_list = self.memory.get_records()
        external_list.append("EXTERNAL_INJECTION")

        self.assertEqual(self.memory.get_records(), ["A", "B"])
        self.assertNotIn("EXTERNAL_INJECTION", self.memory.get_records())

    def test_defensive_copy_immutability_pop_and_clear(self):
        """Popping or clearing the list returned by get_records() does not alter internal memory."""
        self.memory.add("A")
        self.memory.add("B")
        self.memory.add("C")

        external_list = self.memory.get_records()
        external_list.pop(0)
        external_list.clear()

        self.assertEqual(self.memory.get_records(), ["A", "B", "C"])
        self.assertEqual(len(self.memory), 3)

    def test_defensive_copy_immutability_nested_mutation(self):
        """Mutating nested dictionaries or objects in returned view does not alter internal memory."""
        mutable_record = {"id": 1, "text": "original"}
        self.memory.add(mutable_record)

        external_view = self.memory.get_records()
        external_view[0]["text"] = "TAMPERED"

        internal_view = self.memory.get_records()
        self.assertEqual(internal_view[0]["text"], "original")

    def test_intermediate_state_trace_records_every_step(self):
        """State trace records snapshots after INIT, each ADD, and CLEAR with complete metadata."""
        self.memory.add("A")
        self.memory.add("B")
        self.memory.add("C")
        self.memory.add("D")

        trace = self.memory.state_trace
        # Expect 5 snapshots: 1 INIT + 4 ADDs
        self.assertEqual(len(trace), 5)

        self.assertEqual(trace[0].action, "INIT")
        self.assertEqual(trace[0].current_size, 0)
        self.assertEqual(trace[0].memory_state, [])

        self.assertEqual(trace[1].action, "ADD")
        self.assertEqual(trace[1].item_added, "A")
        self.assertIsNone(trace[1].item_evicted)
        self.assertEqual(trace[1].memory_state, ["A"])

        # Fourth add (item D) caused eviction of A
        self.assertEqual(trace[4].action, "ADD")
        self.assertEqual(trace[4].item_added, "D")
        self.assertEqual(trace[4].item_evicted, "A")
        self.assertEqual(trace[4].memory_state, ["B", "C", "D"])
        self.assertEqual(trace[4].current_size, 3)

    def test_formal_capacity_invariant_at_all_steps(self):
        """Formal invariant check: capacity <= 3 is maintained at every single step."""
        for char in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            self.memory.add(char)

        trace = self.memory.state_trace
        for snapshot in trace:
            self.assertTrue(snapshot.invariant_capacity_holds)
            self.assertLessEqual(snapshot.current_size, 3)
            self.assertEqual(len(snapshot.memory_state), snapshot.current_size)

        self.assertTrue(self.memory.verify_invariants())

    def test_clear_operation_and_trace(self):
        """Clearing memory resets size to 0 and records CLEAR action in state trace."""
        self.memory.add("A")
        self.memory.add("B")
        self.memory.clear()

        self.assertEqual(len(self.memory), 0)
        self.assertEqual(self.memory.get_records(), [])

        last_snapshot = self.memory.state_trace[-1]
        self.assertEqual(last_snapshot.action, "CLEAR")
        self.assertEqual(last_snapshot.current_size, 0)
        self.assertEqual(last_snapshot.memory_state, [])
        self.assertTrue(self.memory.verify_invariants())

    def test_conversation_record_objects(self):
        """Memory handles structured immutable ConversationRecord objects."""
        rec1 = ConversationRecord(role="user", content="Hello agent")
        rec2 = ConversationRecord(role="assistant", content="How can I help?")
        rec3 = ConversationRecord(role="user", content="Book a flight")
        rec4 = ConversationRecord(role="assistant", content="Flight options found")

        self.memory.add(rec1)
        self.memory.add(rec2)
        self.memory.add(rec3)
        self.memory.add(rec4)

        retained = self.memory.get_records()
        self.assertEqual(len(retained), 3)
        self.assertEqual([r.content for r in retained], ["How can I help?", "Book a flight", "Flight options found"])

    def test_canonical_simulation_helper(self):
        """simulate_canonical_scenario helper returns expected validation dictionary."""
        sim = simulate_canonical_scenario()
        self.assertEqual(sim["final_records"], ["B", "C", "D"])
        self.assertEqual(sim["expected_records"], ["B", "C", "D"])
        self.assertTrue(sim["invariants_passed"])
        self.assertEqual(sim["trace_length"], 5)  # INIT + 4 ADDs


if __name__ == "__main__":
    unittest.main()
