import json
import unittest

from example import TOOLS, dispatch, run_calls


def call(tool, **args):
    return json.dumps({"tool": tool, "args": args})


class DispatchTests(unittest.TestCase):
    def test_add(self):
        self.assertEqual(dispatch(call("add", a=2, b=3)), {"ok": True, "result": 5})

    def test_multiply(self):
        self.assertEqual(dispatch(call("multiply", a=2, b=3)), {"ok": True, "result": 6})

    def test_unknown_tool_is_structured_error(self):
        self.assertEqual(dispatch(call("divide", a=2, b=3)), {"ok": False, "error": "unknown_tool"})

    def test_string_argument_is_structured_error(self):
        self.assertEqual(dispatch(call("add", a="2", b=3)), {"ok": False, "error": "invalid_arguments"})

    def test_bool_and_missing_arguments_are_rejected(self):
        self.assertFalse(dispatch(call("add", a=True, b=3))["ok"])
        self.assertFalse(dispatch(call("add", a=1))["ok"])
        self.assertFalse(dispatch(call("add", a=1, b=2, c=3))["ok"])

    def test_malformed_json_is_structured_error(self):
        self.assertEqual(dispatch("not json"), {"ok": False, "error": "malformed_call"})
        self.assertEqual(dispatch('{"tool": "add"}'), {"ok": False, "error": "malformed_call"})

    def test_failed_call_stops_the_sequence(self):
        ran = []
        tools = {
            "add": lambda a, b: ran.append("add") or a + b,
            "multiply": lambda a, b: ran.append("multiply") or a * b,
        }
        results = run_calls([call("divide", a=1, b=2), call("add", a=1, b=2)], tools)
        self.assertEqual(len(results), 1)
        self.assertEqual(ran, [])

    def test_successful_sequence_runs_every_call(self):
        results = run_calls([call("add", a=2, b=3), call("multiply", a=2, b=3)])
        self.assertEqual([r["result"] for r in results], [5, 6])

    def test_allowlist_is_only_add_and_multiply(self):
        self.assertEqual(set(TOOLS), {"add", "multiply"})


if __name__ == "__main__":
    unittest.main()
