import unittest

from mini_benchmark.copilot_runner import (
    parse_plan_response,
    parse_review_response,
    parse_solution_response,
)


class CopilotRunnerParsingTests(unittest.TestCase):
    def test_parse_solution_response(self) -> None:
        parsed = parse_solution_response('{"solution": "def foo():\\n    return 1\\n", "notes": "ok"}')
        self.assertEqual(parsed["solution"], "def foo():\n    return 1\n")

    def test_parse_plan_response(self) -> None:
        parsed = parse_plan_response(
            '{"algorithm": "scan once", "edge_cases": ["empty"], "pitfalls": ["off by one"]}'
        )
        self.assertEqual(parsed["edge_cases"], ["empty"])

    def test_parse_review_response(self) -> None:
        parsed = parse_review_response(
            '{"will_pass": true, "reason": "Looks likely to pass.", "correctness_issues": []}'
        )
        self.assertTrue(parsed["will_pass"])


if __name__ == "__main__":
    unittest.main()
