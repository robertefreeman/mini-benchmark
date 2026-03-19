import unittest

from mini_benchmark.config import load_benchmark_config


class ConfigTests(unittest.TestCase):
    def test_three_scenarios_are_configured(self) -> None:
        config = load_benchmark_config()
        self.assertEqual(len(config.scenarios), 3)
        self.assertEqual(config.max_parallel_workers, 6)

    def test_stage_reasoning_efforts_are_loaded(self) -> None:
        config = load_benchmark_config()
        scenario = config.scenario_by_id("gpt-5.4-plan-gpt-5.4-mini-code-review-fix")
        efforts = [stage.reasoning_effort for stage in scenario.stages]
        self.assertEqual(efforts, ["high", "xhigh", "high", "xhigh"])


if __name__ == "__main__":
    unittest.main()
