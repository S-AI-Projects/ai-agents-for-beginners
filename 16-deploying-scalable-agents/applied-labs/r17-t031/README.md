# Trace Aggregation by Request ID

Task R17-T031 for the lesson [Deploying Scalable Agents with Microsoft Foundry](../../README.md).

## How it relates to the lesson

The lesson explains that deployed agents emit OpenTelemetry traces so one request can be followed across model and tool calls. This lab takes a flat list of local trace records, groups them by request ID and reports duration, tool-call count and outcome per request.

## Fixture

Request A: start at 0 ms, two tool calls, end at 12 ms (ok). Request B: start at 2 ms, end at 9 ms (failed). Request C: start and one tool call, no end event. Each record may carry a `prompt` field; the report never includes it.

## Run

```bash
python3 16-deploying-scalable-agents/applied-labs/r17-t031/example.py
python3 -m unittest discover -s 16-deploying-scalable-agents/applied-labs/r17-t031 -p "test_*.py"
```

Expected output of the example:

```text
{
  "A": {
    "duration_ms": 12,
    "tool_calls": 2,
    "status": "success"
  },
  "B": {
    "duration_ms": 7,
    "tool_calls": 0,
    "status": "failure"
  },
  "C": {
    "duration_ms": null,
    "tool_calls": 1,
    "status": "incomplete"
  }
}
```

## Where the simplification stops

Records are hand-written fixtures in a plain list. This is a simulation: it does not use the OpenTelemetry SDK, span parenting, sampling or any Foundry backend, and says nothing about real exporter behavior. A request with no end event is reported as `incomplete` with `duration_ms: null`, never 0.
