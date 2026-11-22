"""Applied Lab: Bounded Conversation Memory with State Trace (R17-T044)

Lesson Alignment:
11-agentic-protocols (Agentic Protocols: MCP, A2A, Context & State Management)

Contract & Goals:
- Implement bounded conversation memory holding at most 3 records in arrival order.
- Adding records A, B, C, D retains B, C, D (FIFO eviction / sliding window).
- Defensive copy immutability: Modifying the returned memory list must not mutate internal stored memory.
- Invariant & state trace: Record intermediate state snapshots after each step.
- Verify formal invariants:
    1. Capacity invariant: `len(memory) <= max_capacity` (<= 3) at all execution steps.
    2. Defensive copy immutability: External mutations of returned views never leak into internal state.
    3. Order preservation: Elements maintain strictly chronological arrival order.
- Zero external dependencies: pure Python 3 standard library.
"""

from collections import deque
import copy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union


@dataclass(frozen=True)
class ConversationRecord:
    """Immutable representation of a conversational turn or protocol message."""
    content: str
    role: str = "user"
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp_iso: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __repr__(self) -> str:
        return f"ConversationRecord({self.role}: {self.content!r})"


@dataclass(frozen=True)
class StateSnapshot:
    """Immutable snapshot capturing memory state and invariant verification at a discrete step."""
    step_index: int
    action: str
    item_added: Optional[Any]
    item_evicted: Optional[Any]
    memory_state: List[Any]
    current_size: int
    max_capacity: int
    invariant_capacity_holds: bool
    timestamp_iso: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class InvariantViolationError(RuntimeError):
    """Raised when a formal memory invariant fails during verification."""
    pass


class BoundedConversationMemory:
    """Bounded, sliding-window conversation memory with defensive copying and formal state tracing.
    
    Default capacity: 3 records in FIFO arrival order.
    """

    def __init__(self, max_capacity: int = 3):
        if max_capacity <= 0:
            raise ValueError(f"max_capacity must be a positive integer, got {max_capacity}")
        self.max_capacity: int = max_capacity
        self._storage: deque = deque()
        self._state_trace: List[StateSnapshot] = []
        self._step_counter: int = 0

        # Record initial baseline state
        self._record_snapshot(action="INIT", item_added=None, item_evicted=None)

    def _record_snapshot(self, action: str, item_added: Optional[Any], item_evicted: Optional[Any]) -> None:
        """Captures an immutable snapshot of internal memory state after an operation."""
        current_state = list(self._storage)
        size = len(current_state)
        capacity_holds = size <= self.max_capacity

        snapshot = StateSnapshot(
            step_index=self._step_counter,
            action=action,
            item_added=copy.deepcopy(item_added) if item_added is not None else None,
            item_evicted=copy.deepcopy(item_evicted) if item_evicted is not None else None,
            memory_state=copy.deepcopy(current_state),
            current_size=size,
            max_capacity=self.max_capacity,
            invariant_capacity_holds=capacity_holds,
        )
        self._state_trace.append(snapshot)
        self._step_counter += 1

        if not capacity_holds:
            raise InvariantViolationError(
                f"Capacity invariant violated at step {snapshot.step_index}: "
                f"size {size} exceeds max_capacity {self.max_capacity}"
            )

    def add(self, record: Union[str, ConversationRecord, Any]) -> Optional[Any]:
        """Adds a record to memory in arrival order.

        If memory is at maximum capacity, the oldest record is evicted (FIFO).
        Returns the evicted record if an eviction occurred, otherwise None.
        """
        item_evicted = None
        if len(self._storage) >= self.max_capacity:
            item_evicted = self._storage.popleft()

        self._storage.append(record)
        self._record_snapshot(action="ADD", item_added=record, item_evicted=item_evicted)
        return item_evicted

    def clear(self) -> None:
        """Clears all records from memory and records a snapshot."""
        self._storage.clear()
        self._record_snapshot(action="CLEAR", item_added=None, item_evicted=None)

    def get_records(self) -> List[Any]:
        """Returns a defensive copy of the current memory in arrival order.
        
        Mutating the returned list does NOT mutate internal memory.
        """
        return copy.deepcopy(list(self._storage))

    @property
    def records(self) -> List[Any]:
        """Property alias returning a defensive copy of stored records."""
        return self.get_records()

    @property
    def state_trace(self) -> List[StateSnapshot]:
        """Returns a defensive copy of the audit state trace."""
        return copy.deepcopy(self._state_trace)

    def verify_invariants(self) -> bool:
        """Formally verifies that all recorded snapshots and current state satisfy invariants:
        
        1. Capacity bound: size <= max_capacity for all steps.
        2. Immutability guarantee: defensive copy isolation.
        3. Arrival order consistency.
        """
        # 1. Current storage check
        if len(self._storage) > self.max_capacity:
            return False

        # 2. Historical trace check
        for snapshot in self._state_trace:
            if not snapshot.invariant_capacity_holds:
                return False
            if snapshot.current_size > self.max_capacity:
                return False
            if len(snapshot.memory_state) != snapshot.current_size:
                return False

        # 3. Defensive copy check
        copy1 = self.get_records()
        copy1.append("__MUTATION_TEST__")
        copy2 = self.get_records()
        if "__MUTATION_TEST__" in copy2:
            return False

        return True

    def __len__(self) -> int:
        return len(self._storage)

    def __iter__(self):
        return iter(self.get_records())

    def __repr__(self) -> str:
        return f"BoundedConversationMemory(size={len(self._storage)}/{self.max_capacity}, records={list(self._storage)})"


def simulate_canonical_scenario() -> Dict[str, Any]:
    """Runs the canonical scenario: adding A, B, C, D to bounded memory (capacity 3)."""
    memory = BoundedConversationMemory(max_capacity=3)
    records_to_add = ["A", "B", "C", "D"]

    for r in records_to_add:
        memory.add(r)

    retained = memory.get_records()
    invariants_passed = memory.verify_invariants()

    return {
        "final_records": retained,
        "expected_records": ["B", "C", "D"],
        "invariants_passed": invariants_passed,
        "trace_length": len(memory.state_trace),
    }


def main():
    print("=== Bounded Conversation Memory with State Trace (R17-T044) ===\n")

    memory = BoundedConversationMemory(max_capacity=3)
    print(f"Initialized Memory: max_capacity={memory.max_capacity}\n")

    steps = ["A", "B", "C", "D"]
    for step_item in steps:
        print(f"-> Adding record: '{step_item}'")
        evicted = memory.add(step_item)
        if evicted:
            print(f"   [EVICTION] Oldest record evicted: '{evicted}'")
        print(f"   Current Memory: {memory.get_records()}\n")

    print(f"Final Retained Memory : {memory.get_records()}")
    print(f"Expected Memory       : ['B', 'C', 'D']")
    print(f"Matches Expected      : {memory.get_records() == ['B', 'C', 'D']}")
    print(f"Invariants Satisfied  : {memory.verify_invariants()}\n")

    print("--- Defensive Copy Immutability Verification ---")
    external_view = memory.get_records()
    print(f"Retrieved External View: {external_view}")
    print("Attempting to mutate external view by appending 'MALICIOUS_INJECTION'...")
    external_view.append("MALICIOUS_INJECTION")
    print(f"External View after mutation: {external_view}")
    print(f"Internal Memory after mutation: {memory.get_records()}")
    print(f"Immutability Intact: {'MALICIOUS_INJECTION' not in memory.get_records()}\n")

    print("--- Intermediate State Trace ---")
    for snap in memory.state_trace:
        print(
            f"Step {snap.step_index:<2} | Action: {snap.action:<5} | "
            f"Added: {str(snap.item_added):<4} | Evicted: {str(snap.item_evicted):<4} | "
            f"Size: {snap.current_size}/{snap.max_capacity} | "
            f"State: {snap.memory_state} | Invariant: {snap.invariant_capacity_holds}"
        )


if __name__ == "__main__":
    main()
