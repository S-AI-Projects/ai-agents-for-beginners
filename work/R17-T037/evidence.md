# R17-T037 evidence

## Tool versions

- Python 3.12.3 (Linux)
- unittest from the standard library

## Command

```
python3 -m unittest discover 04-tool-use/applied-labs/r17-t037 -p "test_*.py"
```

## Expected vs actual

| Check | Expected | Actual |
| --- | --- | --- |
| Test run | nonzero test count, exit 0 | ran 9 tests in 0.000s, exit 0 |
| Example output equals the block in the lab README | True | True |
| Deliberate wrong result (`if not isinstance(name, str) or name not in tools` -> `if not isinstance(name, str)`) | nonzero exit | exit 1 |

## Example output

```
{"tool": "add", "args": {"a": 2, "b": 3}} -> {"ok": true, "result": 5}
{"tool": "multiply", "args": {"a": 2, "b": 3}} -> {"ok": true, "result": 6}
{"tool": "divide", "args": {"a": 2, "b": 3}} -> {"ok": false, "error": "unknown_tool"}
{"tool": "add", "args": {"a": "2", "b": 3}} -> {"ok": false, "error": "invalid_arguments"}
```

## Test output

```
.........
----------------------------------------------------------------------
Ran 9 tests in 0.000s

OK
```

## Deliberate wrong result

Changed `if not isinstance(name, str) or name not in tools` to `if not isinstance(name, str)` in a temporary copy of `example.py`. The suite then reported:

```
FAILED (errors=2)
```
