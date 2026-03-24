import json
import tempfile
import unittest
from pathlib import Path
from threading import Lock
from unittest.mock import patch

from mini_benchmark import runner
from mini_benchmark.config import BenchmarkConfig, ScenarioConfig, StageConfig


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

    def test_run_stage_sequence_uses_fresh_sessions_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            task_dir = Path(tmpdir) / "task"
            config = BenchmarkConfig(
                dataset="humaneval",
                evalplus_version="0.3.1",
                humaneval_plus_dataset_version="v0",
                pricing_source_url="https://example.com",
                pricing_captured_at="2026-03-20",
                max_parallel_workers=6,
                remote_root="$HOME/mini-benchmark",
                copilot_bin="$HOME/.local/bin/copilot",
                common_copilot_args=("--allow-all",),
                fairness_rules=(),
                scenarios=(),
            )
            stages = (
                StageConfig("plan", "gpt-5.4", "medium", "planner.txt"),
                StageConfig("code", "gpt-5.4-mini", "medium", "coder.txt"),
            )
            returned = iter(
                [
                    {"response_text": '{"algorithm":"a","edge_cases":[],"pitfalls":[]}', "session_id": "s1"},
                    {"response_text": '{"solution":"def f():\\n    pass","notes":"ok"}', "session_id": "s2"},
                ]
            )
            resume_args: list[str | None] = []

            def fake_run_copilot_prompt(**kwargs):
                resume_args.append(kwargs["resume_session_id"])
                result = next(returned)
                return {
                    "stage": kwargs["stage_name"],
                    "model": kwargs["model"],
                    "reasoning_effort": kwargs["reasoning_effort"],
                    "resume_session_id": kwargs["resume_session_id"],
                    "prompt_path": "",
                    "stdout_path": "",
                    "stderr_path": "",
                    "log_dir": "",
                    "session_id": result["session_id"],
                    "session_duration_ms": 1,
                    "wall_time_seconds": 0.1,
                    "response_text": result["response_text"],
                    "token_usage": {},
                    "token_usage_by_model": {},
                    "event_count": 1,
                }

            with patch("mini_benchmark.runner.run_copilot_prompt", side_effect=fake_run_copilot_prompt):
                stage_records, stage_session_ids = runner._run_stage_sequence(
                    problem={"task_id": "HumanEval/0", "prompt": "def f(): pass"},
                    session_strategy="fresh",
                    stages=stages,
                    config=config,
                    copilot_bin="$HOME/.local/bin/copilot",
                    task_dir=task_dir,
                    seen_cross_problem_session_ids=set(),
                    session_lock=Lock(),
                    stage_outputs={},
                    allowed_existing_session_ids=set(),
                )

            self.assertEqual(resume_args, [None, None])
            self.assertEqual([stage["session_id"] for stage in stage_records], ["s1", "s2"])
            self.assertEqual(stage_session_ids, ["s1", "s2"])

    def test_run_stage_sequence_can_resume_when_requested(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            task_dir = Path(tmpdir) / "task"
            config = BenchmarkConfig(
                dataset="humaneval",
                evalplus_version="0.3.1",
                humaneval_plus_dataset_version="v0",
                pricing_source_url="https://example.com",
                pricing_captured_at="2026-03-20",
                max_parallel_workers=6,
                remote_root="$HOME/mini-benchmark",
                copilot_bin="$HOME/.local/bin/copilot",
                common_copilot_args=("--allow-all",),
                fairness_rules=(),
                scenarios=(),
            )
            stages = (
                StageConfig("plan", "gpt-5.4", "medium", "planner.txt"),
                StageConfig("code", "gpt-5.4-mini", "medium", "coder.txt"),
            )
            returned = iter(
                [
                    {"response_text": '{"algorithm":"a","edge_cases":[],"pitfalls":[]}', "session_id": "s1"},
                    {"response_text": '{"solution":"def f():\\n    pass","notes":"ok"}', "session_id": "s1"},
                ]
            )
            resume_args: list[str | None] = []

            def fake_run_copilot_prompt(**kwargs):
                resume_args.append(kwargs["resume_session_id"])
                result = next(returned)
                return {
                    "stage": kwargs["stage_name"],
                    "model": kwargs["model"],
                    "reasoning_effort": kwargs["reasoning_effort"],
                    "resume_session_id": kwargs["resume_session_id"],
                    "prompt_path": "",
                    "stdout_path": "",
                    "stderr_path": "",
                    "log_dir": "",
                    "session_id": result["session_id"],
                    "session_duration_ms": 1,
                    "wall_time_seconds": 0.1,
                    "response_text": result["response_text"],
                    "token_usage": {},
                    "token_usage_by_model": {},
                    "event_count": 1,
                }

            with patch("mini_benchmark.runner.run_copilot_prompt", side_effect=fake_run_copilot_prompt):
                _, stage_session_ids = runner._run_stage_sequence(
                    problem={"task_id": "HumanEval/0", "prompt": "def f(): pass"},
                    session_strategy="resume",
                    stages=stages,
                    config=config,
                    copilot_bin="$HOME/.local/bin/copilot",
                    task_dir=task_dir,
                    seen_cross_problem_session_ids=set(),
                    session_lock=Lock(),
                    stage_outputs={},
                    allowed_existing_session_ids=set(),
                )

            self.assertEqual(resume_args, [None, "s1"])
            self.assertEqual(stage_session_ids, ["s1"])

    def test_run_scenario_skips_eval_for_limited_runs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_root = Path(tmpdir)
            scenario = ScenarioConfig(
                id="scenario",
                display_name="Scenario",
                server="muntz",
                submission_stage="code",
                session_strategy="fresh",
                parallel_workers=1,
                eval_repair_stage_names=("repair_plan", "fix"),
                stages=(
                    StageConfig("plan", "gpt-5.4", "medium", "planner.txt"),
                    StageConfig("code", "gpt-5.4-mini", "medium", "coder.txt"),
                    StageConfig("repair_plan", "gpt-5.4", "high", "repair_planner.txt"),
                    StageConfig("fix", "gpt-5.4-mini", "high", "repair_fixer.txt"),
                ),
            )
            config = BenchmarkConfig(
                dataset="humaneval",
                evalplus_version="0.3.1",
                humaneval_plus_dataset_version="v0",
                pricing_source_url="https://example.com",
                pricing_captured_at="2026-03-20",
                max_parallel_workers=6,
                remote_root="$HOME/mini-benchmark",
                copilot_bin="$HOME/.local/bin/copilot",
                common_copilot_args=("--allow-all",),
                fairness_rules=(),
                scenarios=(scenario,),
            )
            task_record = {
                "task_id": "HumanEval/0",
                "prompt": "def f(): pass",
                "problem_session_id": "s1",
                "stage_session_ids": ["s1", "s2"],
                "stages": [
                    {"model": "gpt-5.4", "token_usage": {}},
                    {"model": "gpt-5.4-mini", "token_usage": {}},
                ],
                "stage_outputs": {
                    "plan": {"algorithm": "a", "edge_cases": [], "pitfalls": []},
                    "code": {"solution": "def f():\n    pass\n", "notes": "ok"},
                },
                "final_solution": "def f():\n    pass\n",
                "review": None,
            }

            def fake_write_samples(samples_path: Path, task_records: list[dict[str, object]]):
                samples_path.write_text("{}", encoding="utf-8")
                return [{"task_id": task_records[0]["task_id"], "solution": task_records[0]["final_solution"]}]

            with (
                patch("mini_benchmark.runner.load_benchmark_config", return_value=config),
                patch("mini_benchmark.runner.load_problems", return_value=[{"task_id": "HumanEval/0", "prompt": "def f(): pass"}]),
                patch("mini_benchmark.runner._build_metadata", return_value={"hostname": "test"}),
                patch("mini_benchmark.runner._run_problem_batch", return_value=[task_record]),
                patch("mini_benchmark.runner._write_samples", side_effect=fake_write_samples),
                patch("mini_benchmark.runner._summarize_costs", return_value={"models": [], "total_cost_usd": 0.0}),
                patch("mini_benchmark.runner._evaluate_samples", side_effect=AssertionError("should not evaluate limited runs")),
            ):
                scenario_dir = runner.run_scenario(
                    scenario_id="scenario",
                    run_id="limited-run",
                    limit=1,
                    output_root=output_root,
                )

            summary = json.loads((scenario_dir / "artifacts" / "summary.json").read_text(encoding="utf-8"))
            self.assertTrue(summary["limited_run"])
            self.assertEqual(summary["eval"], None)
            self.assertEqual(summary["eval_skipped_reason"], "limited_run")
            self.assertNotIn("eval_results_path", summary["artifacts"])

    def test_build_stage_prompt_supports_direct_eval_fix(self) -> None:
        prompt = runner._build_stage_prompt(
            stage=StageConfig("fix", "gpt-5.4", "high", "direct_repair_fixer.txt"),
            problem={"task_id": "HumanEval/0", "prompt": "def f(): pass"},
            stage_outputs={
                "plan": {"algorithm": "a", "edge_cases": [], "pitfalls": []},
                "code": {"solution": "def f():\n    pass\n", "notes": "ok"},
                "eval_failure": {"base_status": "pass", "plus_status": "fail"},
            },
        )
        self.assertIn("Evaluation signal:", prompt)
        self.assertIn("Current candidate solution:", prompt)
        self.assertIn("def f():\n    pass\n", prompt)
        self.assertNotIn("Repair plan:", prompt)
        self.assertNotIn("Review:", prompt)


if __name__ == "__main__":
    unittest.main()
