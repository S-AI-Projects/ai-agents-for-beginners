#!/usr/bin/env python3
"""Bounded Conversation Memory — Scenario Assessment (R17-T020).

Demonstrates conversation memory management across agentic protocols:
- Stores at most 3 conversation records in arrival order (FIFO sliding window).
- Adding records A, B, C, D retains B, C, D (evicting the oldest record A).
- Defensive copying ensures mutating the returned list does not alter stored memory.
- Three Applied Scenario Questions:
  1. Predict an Output (predicts ['B', 'C', 'D'] on overflow).
  2. Diagnose a Failure (diagnoses defensive copy isolation preventing external mutation).
  3. Choose a Boundary Policy (FIFO sliding window for conversational continuity).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional


@dataclass(frozen=True)
class ConversationRecord:
    record_id: str
    content: str


class BoundedConversationMemory:
    """Bounded in-memory store maintaining up to max_capacity records."""

    def __init__(self, max_capacity: int = 3) -> None:
        self.max_capacity = max_capacity
        self._store: List[ConversationRecord] = []

    def add_record(self, record: ConversationRecord) -> None:
        self._store.append(record)
        if len(self._store) > self.max_capacity:
            # Evict oldest record (FIFO)
            self._store.pop(0)

    def add_by_id(self, record_id: str, content: str = "") -> None:
        self.add_record(ConversationRecord(record_id=record_id, content=content))

    def get_records(self) -> List[ConversationRecord]:
        """Returns a defensive copy of stored records in arrival order."""
        return list(self._store)

    def get_record_ids(self) -> List[str]:
        return [r.record_id for r in self._store]


@dataclass(frozen=True)
class AppliedQuestion:
    question_id: str
    prompt: str
    expected_answer: Any
    rationale: str
    check_fn: Callable[[], bool]


def check_q1_prediction() -> bool:
    mem = BoundedConversationMemory(max_capacity=3)
    for rid in ["A", "B", "C", "D"]:
        mem.add_by_id(rid)
    return mem.get_record_ids() == ["B", "C", "D"]


def check_q2_diagnosis() -> bool:
    mem = BoundedConversationMemory(max_capacity=3)
    mem.add_by_id("A")
    mem.add_by_id("B")
    exposed = mem.get_records()
    exposed.append(ConversationRecord("MUTATION", "corrupt"))
    exposed.clear()
    return mem.get_record_ids() == ["A", "B"]


def check_q3_policy() -> bool:
    mem = BoundedConversationMemory(max_capacity=3)
    for rid in ["A", "B", "C", "D"]:
        mem.add_by_id(rid)
    # Verifies sliding window retains recent messages
    return mem.get_record_ids() == ["B", "C", "D"]


APPLIED_QUESTIONS: List[AppliedQuestion] = [
    AppliedQuestion(
        question_id="Q1_PREDICT_OUTPUT",
        prompt="Adding records A, B, C, D to a bounded store of capacity 3 retains which records in arrival order?",
        expected_answer=["B", "C", "D"],
        rationale="Under a capacity of 3, inserting the 4th record 'D' evicts the oldest entry 'A', retaining ['B', 'C', 'D'].",
        check_fn=check_q1_prediction,
    ),
    AppliedQuestion(
        question_id="Q2_DIAGNOSE_MUTATION",
        prompt="Why does modifying the list returned by get_records() not corrupt internal agent memory?",
        expected_answer="DEFENSIVE_COPYING",
        rationale="get_records() returns an independent copy (list slice) of internal storage, preserving agent memory encapsulation.",
        check_fn=check_q2_diagnosis,
    ),
    AppliedQuestion(
        question_id="Q3_BOUNDARY_POLICY",
        prompt="Which eviction policy preserves the most relevant conversational context when message capacity is saturated?",
        expected_answer="FIFO_SLIDING_WINDOW",
        rationale="In multi-turn protocols, the most recent messages are required for current goal completion, making oldest-first eviction optimal.",
        check_fn=check_q3_policy,
    ),
]


def main() -> None:
    print("=== Bounded Conversation Memory Demonstration ===")
    memory = BoundedConversationMemory(max_capacity=3)

    for rid in ["A", "B", "C", "D"]:
        memory.add_by_id(rid, f"Message content for {rid}")
        print(f"Added {rid} -> Stored: {memory.get_record_ids()}")

    # Mutation test
    records = memory.get_records()
    records.clear()
    print("External clear() called on returned list.")
    print("Stored after external clear:", memory.get_record_ids())

    print("\n=== Applied Scenario Assessment Questions ===")
    for q in APPLIED_QUESTIONS:
        status = "PASS" if q.check_fn() else "FAIL"
        print(f"[{q.question_id}] {q.prompt}")
        print(f"  Expected: {q.expected_answer} | Validation: {status}")
        print(f"  Rationale: {q.rationale}\n")


if __name__ == "__main__":
    main()
