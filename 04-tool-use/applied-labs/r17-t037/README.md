# Typed Tool Dispatch

Task R17-T037 for the lesson [Tool Use Design Pattern](../../README.md).

## How it relates to the lesson

The lesson lists function schemas and error handling and validation as building blocks. This lab dispatches JSON tool calls through an explicit allowlist, validates numeric arguments, returns structured errors, and stops a sequence at the first failed call.

## Fixture

`add(2, 3)`, `multiply(2, 3)`, an unknown tool `divide`, and `add("2", 3)`.

## Run

```bash
python3 04-tool-use/applied-labs/r17-t037/example.py
python3 -m unittest discover -s 04-tool-use/applied-labs/r17-t037 -p "test_*.py"
```

Expected output of the example:

```text
{"tool": "add", "args": {"a": 2, "b": 3}} -> {"ok": true, "result": 5}
{"tool": "multiply", "args": {"a": 2, "b": 3}} -> {"ok": true, "result": 6}
{"tool": "divide", "args": {"a": 2, "b": 3}} -> {"ok": false, "error": "unknown_tool"}
{"tool": "add", "args": {"a": "2", "b": 3}} -> {"ok": false, "error": "invalid_arguments"}
```

## Where the simplification stops

This is a local contract fixture, not a full MCP transport implementation. There is no model producing the calls, no schema negotiation and no network.
