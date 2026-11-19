# Bounded Agent Loop

Task R17-T032 for the lesson [Exploring Microsoft Agent Framework](../../README.md).

## How it relates to the lesson

The lesson highlights observability of every agent action. This lab runs a scripted plan of at most three steps, records each action in a trace, and ends on `stop` or with `budget_exceeded`. The direct implementation is checked against an explicit expected-result table and against a separate, simpler calculation on identical inputs.

## Fixture

Plans: `[inspect, answer, stop]`, an endless `inspect` cycle, `[stop, answer]`, and `[inspect, inspect, inspect, stop]`.

## Run

```bash
python3 14-microsoft-agent-framework/applied-labs/r17-t032/example.py
python3 -m unittest discover -s 14-microsoft-agent-framework/applied-labs/r17-t032 -p "test_*.py"
```

Expected output of the example:

```text
normal: completed ['inspect', 'answer', 'stop']
endless: budget_exceeded ['inspect', 'inspect', 'inspect']
stop first: completed ['stop']
stop at step 4: budget_exceeded ['inspect', 'inspect', 'inspect']
```

## Where the simplification stops

The plan is a fixed script, not model output, and the tools only append to a list. This is a simulation: it does not use Microsoft Agent Framework, and the step budget here is not an Agent Framework setting.
