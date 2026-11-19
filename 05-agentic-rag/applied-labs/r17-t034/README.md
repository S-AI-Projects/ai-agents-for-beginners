# Retrieval Behind a Callable Interface

Task R17-T034 for the lesson [Agentic RAG](../../README.md).

## How it relates to the lesson

An agentic RAG loop should not care which retriever it talks to. This lab puts search behind a plain callable, `search(query) -> list of document IDs`, supplies a deterministic lexical adapter, and keeps the calling code independent of it.

## Fixture

A = "red apple", B = "green apple", C = "blue sky". Queries: `red apple`, `ocean`.

## Run

```bash
python3 05-agentic-rag/applied-labs/r17-t034/example.py
python3 -m unittest discover -s 05-agentic-rag/applied-labs/r17-t034 -p "test_*.py"
```

Expected output of the example:

```text
{'query': 'red apple', 'status': 'found', 'sources': ['A', 'B']}
{'query': 'ocean', 'status': 'no_match', 'sources': []}
```

## Where the simplification stops

This is a lexical test double, not a production vector search. The adapter does not establish real-service behavior such as latency, timeouts, rate limits, authentication, index freshness or semantic ranking. The only failure covered is an exception raised by the callable.
