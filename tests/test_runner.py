import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from mini_benchmark import runner


class RunnerTests(unittest.TestCase):
    def test_evaluate_samples_reads_evalplus_default_output_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            samples_path = tmp / "samples.jsonl"
            output_path = tmp / "custom.eval_results.json"
            log_path = tmp / "evalplus.log"
            samples_path.write_text('{"task_id":"HumanEval/0","solution":"def f():\\n    pass\\n"}\n', encoding="utf-8")

            def fake_evaluate(*, dataset: str, samples: str) -> None:
                self.assertEqual(dataset, "humaneval")
                self.assertEqual(samples, str(samples_path))
                evalplus_output_path = Path(str(samples_path).replace(".jsonl", "_eval_results.json"))
                evalplus_output_path.write_text(
                    json.dumps({"eval": {"HumanEval/0": [{"base_status": "pass", "plus_status": "pass"}]}}),
                    encoding="utf-8",
                )

            with patch("mini_benchmark.runner._load_evalplus", return_value=(None, None, fake_evaluate)):
                result = runner._evaluate_samples(samples_path, output_path, log_path)

            self.assertEqual(result["eval"]["HumanEval/0"][0]["base_status"], "pass")
            self.assertTrue(output_path.exists())
            self.assertTrue(log_path.exists())

    def test_task_passed_eval_requires_base_and_plus_pass(self) -> None:
        self.assertTrue(
            runner._task_passed_eval([{"base_status": "pass", "plus_status": "pass"}])
        )
        self.assertFalse(
            runner._task_passed_eval([{"base_status": "pass", "plus_status": "fail"}])
        )


if __name__ == "__main__":
    unittest.main()
