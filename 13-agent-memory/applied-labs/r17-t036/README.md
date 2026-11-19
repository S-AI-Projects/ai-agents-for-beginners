# Memory Capacity Experiment

Task R17-T036 for the lesson [Memory for AI Agents](../../README.md).

## How it relates to the lesson

The lesson separates short-term from long-term memory. This lab compares three capacities (1, 3 and 5) of a short-term buffer over the same six records, measuring whether the newest records are retained and how many records are stored.

## Fixture

Stream `A..F`, capacities 1, 3 and 5. Metric `recall_newest` is the share of the three newest records still held.

## Run

```bash
python3 13-agent-memory/applied-labs/r17-t036/example.py
python3 -m unittest discover -s 13-agent-memory/applied-labs/r17-t036 -p "test_*.py"
```

Expected output of the example:

```text
capacity  kept             correct  recall_newest
1         F                True     0.33
3         DEF              True     1.0
5         BCDEF            True     1.0
```

## Where the simplification stops

The metric only measures retention of recent records in a toy buffer. It says nothing about retrieval quality, model accuracy or cost in a real agent. Capacity 5 stores more without scoring higher here, but older records may matter in other designs.
