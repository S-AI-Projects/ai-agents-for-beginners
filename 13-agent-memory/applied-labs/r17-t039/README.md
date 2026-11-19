# Memory Boundary Cases

Task R17-T039 for the lesson [Memory for AI Agents](../../README.md).

## How it relates to the lesson

Short-term memory has to decide what to drop. This lab fixes the boundary rule for a bounded buffer: eviction happens only when the count exceeds capacity, so a buffer holding exactly its capacity keeps every record.

## Fixture

Capacity 3 with 0, 1, 3 and 4 records; capacity 1 with `A, B`; invalid capacities `0`, `-1`, `"3"` and `True`.

## Run

```bash
python3 13-agent-memory/applied-labs/r17-t039/example.py
python3 -m unittest discover -s 13-agent-memory/applied-labs/r17-t039 -p "test_*.py"
```

Expected output of the example:

```text
empty: []
one record: ['A']
exactly full: ['A', 'B', 'C']
one over: ['B', 'C', 'D']
smallest capacity: ['B']
capacity 0: capacity must be a positive integer
capacity -1: capacity must be a positive integer
capacity '3': capacity must be a positive integer
capacity True: capacity must be a positive integer
```

## Where the simplification stops

A single in-process list with oldest-first eviction. It does not cover persistence, summarization or long-term memory stores.
