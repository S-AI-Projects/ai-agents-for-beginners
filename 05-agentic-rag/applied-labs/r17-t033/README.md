# Lexical Retrieval State Trace

Task R17-T033 for the lesson [Agentic RAG](../../README.md).

## How it relates to the lesson

Agentic RAG depends on retrieving and ranking sources before answering. This lab scores three local documents by word overlap with a lowercase query and records the state after normalizing, scoring, ranking and filtering. The tests check that the final output always follows from the recorded state.

## Fixture

A = "red apple", B = "green apple", C = "blue sky". Queries: `red apple`, `ocean`.

## Run

```bash
python3 05-agentic-rag/applied-labs/r17-t033/example.py
python3 -m unittest discover -s 05-agentic-rag/applied-labs/r17-t033 -p "test_*.py"
```

Expected output of the example:

```text
red apple -> [('A', 2), ('B', 1)]
   normalize ['apple', 'red']
   score {'A': 2, 'B': 1, 'C': 0}
   rank ['A', 'B', 'C']
   filter ['A', 'B']
ocean -> []
   normalize ['ocean']
   score {'A': 0, 'B': 0, 'C': 0}
   rank ['A', 'B', 'C']
   filter []
```

## Where the simplification stops

This is a lexical test double, not a production vector search. There are no embeddings, no stemming, no query rewriting and no LLM, so it does not reflect how Azure AI Search or any real retriever ranks results.
