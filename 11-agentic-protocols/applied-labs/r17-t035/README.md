# Bounded Conversation Memory Refactor

Task R17-T035 for the lesson [Using Agentic Protocols (MCP, A2A and NLWeb)](../../README.md).

## How it relates to the lesson

Protocols carry conversation context between agents, so who owns that context and what is kept matters. This lab stores at most three records in arrival order and hands callers a copy. A baseline class is refactored by extracting the retention rule into `keep_latest`, and the tests show both give identical results.

## Fixture

Records `A, B, C, D` with a limit of 3, plus every prefix of `A..G` at limits 1, 2, 3 and 5.

## Run

```bash
python3 11-agentic-protocols/applied-labs/r17-t035/example.py
python3 -m unittest discover -s 11-agentic-protocols/applied-labs/r17-t035 -p "test_*.py"
```

Expected output of the example:

```text
BaselineMemory ['B', 'C', 'D']
Memory ['B', 'C', 'D']
```

## Where the simplification stops

Memory is an in-process list. This is a simulation: no MCP, A2A or NLWeb message is sent, and nothing is persisted.
