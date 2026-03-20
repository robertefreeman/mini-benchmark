from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO_ROOT / "config" / "benchmark.json"
PRICING_PATH = REPO_ROOT / "config" / "pricing.openai.json"
PROMPTS_DIR = REPO_ROOT / "prompts"


@dataclass(frozen=True)
class StageConfig:
    name: str
    model: str
    reasoning_effort: str
    prompt_template: str


@dataclass(frozen=True)
class ScenarioConfig:
    id: str
    display_name: str
    server: str
    submission_stage: str
    parallel_workers: int
    eval_repair_stage_names: tuple[str, ...]
    stages: tuple[StageConfig, ...]


@dataclass(frozen=True)
class BenchmarkConfig:
    dataset: str
    evalplus_version: str
    humaneval_plus_dataset_version: str
    pricing_source_url: str
    pricing_captured_at: str
    max_parallel_workers: int
    remote_root: str
    copilot_bin: str
    common_copilot_args: tuple[str, ...]
    fairness_rules: tuple[str, ...]
    scenarios: tuple[ScenarioConfig, ...]

    def scenario_by_id(self, scenario_id: str) -> ScenarioConfig:
        for scenario in self.scenarios:
            if scenario.id == scenario_id:
                return scenario
        raise KeyError(f"Unknown scenario: {scenario_id}")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_benchmark_config() -> BenchmarkConfig:
    raw = _load_json(CONFIG_PATH)
    benchmark = raw["benchmark"]
    scenarios = tuple(
        ScenarioConfig(
            id=scenario["id"],
            display_name=scenario["display_name"],
            server=scenario["server"],
            submission_stage=scenario["submission_stage"],
            parallel_workers=scenario.get("parallel_workers", 1),
            eval_repair_stage_names=tuple(scenario.get("eval_repair_stage_names", [])),
            stages=tuple(
                StageConfig(
                    name=stage["name"],
                    model=stage["model"],
                    reasoning_effort=stage["reasoning_effort"],
                    prompt_template=stage["prompt_template"],
                )
                for stage in scenario["stages"]
            ),
        )
        for scenario in raw["scenarios"]
    )
    return BenchmarkConfig(
        dataset=benchmark["dataset"],
        evalplus_version=benchmark["evalplus_version"],
        humaneval_plus_dataset_version=benchmark["humaneval_plus_dataset_version"],
        pricing_source_url=benchmark["pricing_source_url"],
        pricing_captured_at=benchmark["pricing_captured_at"],
        max_parallel_workers=benchmark["max_parallel_workers"],
        remote_root=benchmark["remote_root"],
        copilot_bin=benchmark["copilot_bin"],
        common_copilot_args=tuple(benchmark["common_copilot_args"]),
        fairness_rules=tuple(raw["fairness_rules"]),
        scenarios=scenarios,
    )
