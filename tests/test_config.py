import unittest

from mini_benchmark.config import load_benchmark_config


class ConfigTests(unittest.TestCase):
    def test_six_scenarios_are_configured(self) -> None:
        config = load_benchmark_config()
        self.assertEqual(len(config.scenarios), 6)
        self.assertEqual(config.max_parallel_workers, 6)

    def test_stage_reasoning_efforts_are_loaded(self) -> None:
        config = load_benchmark_config()
        scenario = config.scenario_by_id("gpt-5.4-plan-gpt-5.4-mini-code-review-fix")
        efforts = [stage.reasoning_effort for stage in scenario.stages]
        self.assertEqual(efforts, ["high", "xhigh", "high", "xhigh"])

    def test_benchmark_four_parallel_repair_config_is_loaded(self) -> None:
        config = load_benchmark_config()
        scenario = config.scenario_by_id("gpt-5.4-plan-gpt-5.4-mini-code-eval-repair")
        efforts = [stage.reasoning_effort for stage in scenario.stages]
        self.assertEqual(efforts, ["medium", "medium", "high", "high"])
        self.assertEqual(scenario.server, "muntz")
        self.assertEqual(scenario.session_strategy, "fresh")
        self.assertEqual(scenario.parallel_workers, 2)
        self.assertEqual(scenario.eval_repair_stage_names, ("repair_plan", "fix"))

    def test_benchmark_five_direct_fix_config_is_loaded(self) -> None:
        config = load_benchmark_config()
        scenario = config.scenario_by_id("gpt-5.4-plan-gpt-5.4-mini-code-eval-direct-fix")
        efforts = [stage.reasoning_effort for stage in scenario.stages]
        self.assertEqual(efforts, ["medium", "medium", "high"])
        self.assertEqual(scenario.server, "muntz")
        self.assertEqual(scenario.session_strategy, "fresh")
        self.assertEqual(scenario.parallel_workers, 2)
        self.assertEqual(scenario.eval_repair_stage_names, ("fix",))

    def test_benchmark_six_opus_config_is_loaded(self) -> None:
        config = load_benchmark_config()
        scenario = config.scenario_by_id("claude-opus-4.6-plan-code")
        efforts = [stage.reasoning_effort for stage in scenario.stages]
        models = [stage.model for stage in scenario.stages]
        self.assertEqual(efforts, ["medium", "medium"])
        self.assertEqual(models, ["claude-opus-4.6", "claude-opus-4.6"])
        self.assertEqual(scenario.server, "griswold")
        self.assertEqual(scenario.session_strategy, "fresh")
        self.assertEqual(scenario.parallel_workers, 1)
        self.assertEqual(scenario.eval_repair_stage_names, ())


if __name__ == "__main__":
    unittest.main()
