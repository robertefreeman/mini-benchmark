import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from mini_benchmark.copilot_runner import (
    parse_plan_response,
    parse_review_response,
    parse_solution_response,
    run_copilot_prompt,
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

    def test_run_copilot_prompt_falls_back_to_assistant_message_without_final_phase(self) -> None:
        stdout = "\n".join(
            [
                json.dumps(
                    {
                        "type": "assistant.message",
                        "data": {
                            "content": '{"algorithm":"scan once","edge_cases":["empty"],"pitfalls":["off by one"]}'
                        },
                    }
                ),
                json.dumps(
                    {
                        "type": "result",
                        "sessionId": "session-123",
                        "usage": {"sessionDurationMs": 42},
                    }
                ),
            ]
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            with patch(
                "mini_benchmark.copilot_runner.subprocess.run",
                return_value=subprocess.CompletedProcess(
                    args=["copilot"],
                    returncode=0,
                    stdout=stdout,
                    stderr="",
                ),
            ), patch("mini_benchmark.copilot_runner.parse_log_dir", return_value={}):
                result = run_copilot_prompt(
                    copilot_bin="copilot",
                    common_args=("--allow-all",),
                    model="claude-opus-4.6",
                    reasoning_effort="medium",
                    prompt="prompt",
                    working_dir=tmp,
                    artifact_dir=tmp / "artifacts",
                    stage_name="plan",
                )

        self.assertEqual(
            result["response_text"],
            '{"algorithm":"scan once","edge_cases":["empty"],"pitfalls":["off by one"]}',
        )
        self.assertEqual(result["session_id"], "session-123")
        self.assertEqual(result["session_duration_ms"], 42)


if __name__ == "__main__":
    unittest.main()
