from __future__ import annotations

import argparse
import json
import os
import shutil
import socket
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from threading import Lock
from typing import Any, Callable

from .config import REPO_ROOT, BenchmarkConfig, ScenarioConfig, StageConfig, load_benchmark_config
from .copilot_runner import (
    parse_plan_response,
    parse_review_response,
    parse_solution_response,
    run_copilot_prompt,
)
from .pricing import aggregate_usage, calculate_cost, load_pricing
from .prompts import render_prompt


def _load_evalplus():
    try:
        from evalplus.data import write_jsonl
        from evalplus.data.humaneval import get_human_eval_plus
        from evalplus.evaluate import evaluate as evalplus_evaluate
    except ImportError as exc:
        raise RuntimeError(
            "evalplus is not installed. Install requirements before running the harness."
        ) from exc
    return get_human_eval_plus, write_jsonl, evalplus_evaluate


def _task_sort_key(task_id: str) -> int:
    return int(task_id.split("/")[-1])


def load_problems(limit: int | None = None) -> list[dict[str, Any]]:
    get_human_eval_plus, _, _ = _load_evalplus()
    problems = get_human_eval_plus()
    ordered = [problems[task_id] for task_id in sorted(problems, key=_task_sort_key)]
    return ordered[:limit] if limit else ordered


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _run_environment_command(command: list[str]) -> str:
    completed = subprocess.run(command, capture_output=True, text=True, check=True)
    return completed.stdout.strip()


def _build_metadata(copilot_bin: str) -> dict[str, str]:
    return {
        "hostname": socket.gethostname(),
        "python_version": _run_environment_command(["python3", "--version"]),
        "git_commit": _run_environment_command(["git", "rev-parse", "HEAD"]),
        "copilot_version": _run_environment_command([str(Path(copilot_bin).expanduser()), "--version"]),
    }


def _task_slug(task_id: str) -> str:
    return task_id.replace("/", "_")


def _evaluate_samples(samples_path: Path, output_path: Path, log_path: Path) -> dict[str, Any]:
    _, _, evalplus_evaluate = _load_evalplus()
    with log_path.open("w", encoding="utf-8") as handle, redirect_stdout(handle), redirect_stderr(handle):
        evalplus_evaluate(dataset="humaneval", samples=str(samples_path))
    evalplus_output_path = Path(str(samples_path).replace(".jsonl", "_eval_results.json"))
    if evalplus_output_path != output_path:
        shutil.copyfile(evalplus_output_path, output_path)
    return json.loads(output_path.read_text(encoding="utf-8"))


def _task_passed_eval(task_results: list[dict[str, Any]]) -> bool:
    first = task_results[0]
    base_ok = str(first.get("base_status", "")).lower() == "pass"
    plus_ok = str(first.get("plus_status", "")).lower() == "pass"
    return base_ok and plus_ok


def _summarize_eval(eval_results: dict[str, Any]) -> dict[str, Any]:
    per_task = eval_results["eval"]
    correct = 0
    total = len(per_task)
    passed_task_ids: list[str] = []

    for task_id, task_results in per_task.items():
        if _task_passed_eval(task_results):
            correct += 1
            passed_task_ids.append(task_id)

    percent_correct = (correct / total * 100.0) if total else 0.0
    return {
        "correct_tasks": correct,
        "total_tasks": total,
        "percent_correct": round(percent_correct, 4),
        "passed_task_ids": passed_task_ids,
    }


def _summarize_costs(stage_records: list[dict[str, Any]]) -> dict[str, Any]:
    pricing = load_pricing()
    usage_by_model = aggregate_usage(stage_records)
    costs_by_model: dict[str, Any] = {}
    total_cost = 0.0
    total_usage = {
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_read_tokens": 0,
        "cache_write_tokens": 0,
        "request_count": 0,
    }

    for model, usage in usage_by_model.items():
        cost = calculate_cost(model, usage, pricing)
        costs_by_model[model] = {**usage, **cost}
        total_cost += cost["total_cost_usd"]
        for key in total_usage:
            total_usage[key] += usage.get(key, 0)

    return {
        "by_model": costs_by_model,
        "total": {
            **total_usage,
            "total_cost_usd": round(total_cost, 6),
            "pricing_source_url": pricing["source_url"],
            "pricing_captured_at": pricing["captured_at"],
        },
    }


def _build_workspace(task_dir: Path) -> Path:
    workspace = task_dir / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    return workspace


def _build_stage_prompt(
    *,
    stage: StageConfig,
    problem: dict[str, Any],
    stage_outputs: dict[str, dict[str, Any]],
) -> str:
    if stage.name == "plan":
        return render_prompt(stage.prompt_template, task_id=problem["task_id"], prompt=problem["prompt"])
    if stage.name == "code":
        return render_prompt(
            stage.prompt_template,
            task_id=problem["task_id"],
            prompt=problem["prompt"],
            plan_json=stage_outputs["plan"],
        )
    if stage.name == "review":
        return render_prompt(
            stage.prompt_template,
            task_id=problem["task_id"],
            prompt=problem["prompt"],
            plan_json=stage_outputs["plan"],
            candidate_solution=stage_outputs["code"]["solution"],
        )
    if stage.name == "repair_plan":
        return render_prompt(
            stage.prompt_template,
            task_id=problem["task_id"],
            prompt=problem["prompt"],
            plan_json=stage_outputs["plan"],
            eval_failure_json=stage_outputs["eval_failure"],
            candidate_solution=stage_outputs["code"]["solution"],
        )
    if stage.name == "fix" and "repair_plan" in stage_outputs:
        return render_prompt(
            stage.prompt_template,
            task_id=problem["task_id"],
            prompt=problem["prompt"],
            plan_json=stage_outputs["plan"],
            repair_plan_json=stage_outputs["repair_plan"],
            eval_failure_json=stage_outputs["eval_failure"],
            candidate_solution=stage_outputs["code"]["solution"],
        )
    if stage.name == "fix":
        return render_prompt(
            stage.prompt_template,
            task_id=problem["task_id"],
            prompt=problem["prompt"],
            plan_json=stage_outputs["plan"],
            review_json=stage_outputs["review"],
            candidate_solution=stage_outputs["code"]["solution"],
        )
    raise ValueError(f"Unsupported stage: {stage.name}")


def _parse_stage_output(stage_name: str, response_text: str) -> dict[str, Any]:
    if stage_name in {"plan", "repair_plan"}:
        return parse_plan_response(response_text)
    if stage_name in {"code", "fix"}:
        return parse_solution_response(response_text)
    if stage_name == "review":
        return parse_review_response(response_text)
    raise ValueError(f"Unsupported stage: {stage_name}")


def _should_run_stage(stage: StageConfig, stage_outputs: dict[str, dict[str, Any]]) -> bool:
    if stage.name != "fix":
        return True
    if "repair_plan" in stage_outputs:
        return True
    review = stage_outputs.get("review")
    return bool(review) and not review.get("will_pass", False)


def _determine_final_solution(
    *,
    stage_outputs: dict[str, dict[str, Any]],
    submission_stage: str,
) -> str:
    submission_output = stage_outputs.get(submission_stage)
    if submission_output and "solution" in submission_output:
        return submission_output["solution"]
    return stage_outputs["code"]["solution"]


def _write_task_record(task_dir: Path, task_record: dict[str, Any]) -> None:
    _write_json(task_dir / "task_record.json", task_record)


def _run_stage_sequence(
    *,
    problem: dict[str, Any],
    session_strategy: str,
    stages: tuple[StageConfig, ...],
    config: BenchmarkConfig,
    copilot_bin: str,
    task_dir: Path,
    seen_cross_problem_session_ids: set[str],
    session_lock: Lock,
    stage_outputs: dict[str, dict[str, Any]],
    allowed_existing_session_ids: set[str],
) -> tuple[list[dict[str, Any]], list[str]]:
    workspace = _build_workspace(task_dir)
    stage_records: list[dict[str, Any]] = []
    stage_session_ids: list[str] = []
    session_id: str | None = None

    for stage in stages:
        if not _should_run_stage(stage, stage_outputs):
            continue

        prompt = _build_stage_prompt(stage=stage, problem=problem, stage_outputs=stage_outputs)
        result = run_copilot_prompt(
            copilot_bin=copilot_bin,
            common_args=config.common_copilot_args,
            model=stage.model,
            reasoning_effort=stage.reasoning_effort,
            prompt=prompt,
            working_dir=workspace,
            artifact_dir=task_dir / "stages" / stage.name,
            stage_name=stage.name,
            resume_session_id=session_id if session_strategy == "resume" else None,
        )

        parsed = _parse_stage_output(stage.name, result["response_text"])
        stage_outputs[stage.name] = parsed
        stage_records.append({**result, "parsed": parsed})

        returned_session_id = result.get("session_id")
        if returned_session_id:
            with session_lock:
                if (
                    returned_session_id in seen_cross_problem_session_ids
                    and returned_session_id not in allowed_existing_session_ids
                    and returned_session_id not in stage_session_ids
                ):
                    raise RuntimeError(
                        f"Session {returned_session_id} was reused across different HumanEval+ problems."
                    )
                seen_cross_problem_session_ids.add(returned_session_id)
            session_id = returned_session_id
            if returned_session_id not in stage_session_ids:
                stage_session_ids.append(returned_session_id)

    return stage_records, stage_session_ids


def _build_task_record(
    *,
    problem: dict[str, Any],
    stage_outputs: dict[str, dict[str, Any]],
    stage_records: list[dict[str, Any]],
    stage_session_ids: list[str],
    submission_stage: str,
) -> dict[str, Any]:
    if "code" not in stage_outputs:
        raise RuntimeError(f"Problem {problem['task_id']} did not produce a code stage output.")

    serializable_stage_outputs = {
        key: value for key, value in stage_outputs.items() if key != "eval_failure"
    }
    return {
        "task_id": problem["task_id"],
        "prompt": problem["prompt"],
        "problem_session_id": stage_session_ids[0] if stage_session_ids else None,
        "stage_session_ids": stage_session_ids,
        "stages": stage_records,
        "stage_outputs": serializable_stage_outputs,
        "final_solution": _determine_final_solution(
            stage_outputs=stage_outputs,
            submission_stage=submission_stage,
        ),
        "review": serializable_stage_outputs.get("review"),
    }


def _run_initial_problem(
    *,
    problem: dict[str, Any],
    session_strategy: str,
    initial_stages: tuple[StageConfig, ...],
    submission_stage: str,
    config: BenchmarkConfig,
    copilot_bin: str,
    task_dir: Path,
    seen_cross_problem_session_ids: set[str],
    session_lock: Lock,
) -> dict[str, Any]:
    stage_outputs: dict[str, dict[str, Any]] = {}
    stage_records, stage_session_ids = _run_stage_sequence(
        problem=problem,
        session_strategy=session_strategy,
        stages=initial_stages,
        config=config,
        copilot_bin=copilot_bin,
        task_dir=task_dir,
        seen_cross_problem_session_ids=seen_cross_problem_session_ids,
        session_lock=session_lock,
        stage_outputs=stage_outputs,
        allowed_existing_session_ids=set(),
    )
    task_record = _build_task_record(
        problem=problem,
        stage_outputs=stage_outputs,
        stage_records=stage_records,
        stage_session_ids=stage_session_ids,
        submission_stage=submission_stage,
    )
    _write_task_record(task_dir, task_record)
    return task_record


def _repair_problem(
    *,
    problem: dict[str, Any],
    task_record: dict[str, Any],
    session_strategy: str,
    repair_stages: tuple[StageConfig, ...],
    config: BenchmarkConfig,
    copilot_bin: str,
    task_dir: Path,
    seen_cross_problem_session_ids: set[str],
    session_lock: Lock,
    eval_failure: dict[str, Any],
    submission_stage: str,
) -> dict[str, Any]:
    stage_outputs = dict(task_record["stage_outputs"])
    stage_outputs["eval_failure"] = eval_failure
    existing_session_ids = set(task_record["stage_session_ids"])
    stage_records, new_session_ids = _run_stage_sequence(
        problem=problem,
        session_strategy=session_strategy,
        stages=repair_stages,
        config=config,
        copilot_bin=copilot_bin,
        task_dir=task_dir,
        seen_cross_problem_session_ids=seen_cross_problem_session_ids,
        session_lock=session_lock,
        stage_outputs=stage_outputs,
        allowed_existing_session_ids=existing_session_ids,
    )

    merged_session_ids = list(task_record["stage_session_ids"])
    for session_id in new_session_ids:
        if session_id not in merged_session_ids:
            merged_session_ids.append(session_id)

    repaired_task_record = _build_task_record(
        problem=problem,
        stage_outputs=stage_outputs,
        stage_records=[*task_record["stages"], *stage_records],
        stage_session_ids=merged_session_ids,
        submission_stage=submission_stage,
    )
    if "initial_eval" in task_record:
        repaired_task_record["initial_eval"] = task_record["initial_eval"]
    _write_task_record(task_dir, repaired_task_record)
    return repaired_task_record


def _run_problem_batch(
    *,
    problems: list[dict[str, Any]],
    worker_count: int,
    run_problem: Callable[[dict[str, Any]], dict[str, Any]],
) -> list[dict[str, Any]]:
    if worker_count <= 1:
        return [run_problem(problem) for problem in problems]

    results_by_task_id: dict[str, dict[str, Any]] = {}
    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        futures = {executor.submit(run_problem, problem): problem["task_id"] for problem in problems}
        for future in as_completed(futures):
            task_id = futures[future]
            results_by_task_id[task_id] = future.result()

    return [results_by_task_id[problem["task_id"]] for problem in problems]


def _write_samples(samples_path: Path, task_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    _, write_jsonl, _ = _load_evalplus()
    samples = [{"task_id": task_record["task_id"], "solution": task_record["final_solution"]} for task_record in task_records]
    write_jsonl(str(samples_path), samples, append=False, drop_builtin=False)
    return samples


def run_scenario(*, scenario_id: str, run_id: str, limit: int | None = None, output_root: Path | None = None) -> Path:
    config = load_benchmark_config()
    scenario = config.scenario_by_id(scenario_id)
    copilot_bin = os.path.expandvars(config.copilot_bin)

    output_root = output_root or (REPO_ROOT / "runs")
    scenario_dir = output_root / run_id / scenario.id
    artifacts_dir = scenario_dir / "artifacts"
    tasks_dir = scenario_dir / "tasks"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    tasks_dir.mkdir(parents=True, exist_ok=True)

    started_at_unix = time.time()
    started_at_mono = time.monotonic()
    problems = load_problems(limit=limit)
    limited_run = limit is not None
    worker_count = min(config.max_parallel_workers, max(1, scenario.parallel_workers))

    manifest = {
        "scenario_id": scenario.id,
        "display_name": scenario.display_name,
        "server": scenario.server,
        "dataset": config.dataset,
        "evalplus_version": config.evalplus_version,
        "humaneval_plus_dataset_version": config.humaneval_plus_dataset_version,
        "runtime_measurement": "wall_clock",
        "max_parallel_workers": config.max_parallel_workers,
        "parallel_workers_configured": scenario.parallel_workers,
        "started_at_unix": started_at_unix,
        "metadata": _build_metadata(copilot_bin),
        "fairness_rules": list(config.fairness_rules),
        "task_count": len(problems),
        "common_copilot_args": list(config.common_copilot_args),
        "stages": [
            {
                "name": stage.name,
                "model": stage.model,
                "reasoning_effort": stage.reasoning_effort,
                "prompt_template": stage.prompt_template,
            }
            for stage in scenario.stages
        ],
    }
    _write_json(artifacts_dir / "manifest.json", manifest)

    seen_cross_problem_session_ids: set[str] = set()
    session_lock = Lock()
    repair_stage_names = set(scenario.eval_repair_stage_names)
    initial_stages = tuple(stage for stage in scenario.stages if stage.name not in repair_stage_names)
    repair_stages = tuple(stage for stage in scenario.stages if stage.name in repair_stage_names)
    initial_submission_stage = "code" if repair_stages else scenario.submission_stage

    def run_initial(problem: dict[str, Any]) -> dict[str, Any]:
        task_dir = tasks_dir / _task_slug(problem["task_id"])
        return _run_initial_problem(
            problem=problem,
            session_strategy=scenario.session_strategy,
            initial_stages=initial_stages,
            submission_stage=initial_submission_stage,
            config=config,
            copilot_bin=copilot_bin,
            task_dir=task_dir,
            seen_cross_problem_session_ids=seen_cross_problem_session_ids,
            session_lock=session_lock,
        )

    task_records = _run_problem_batch(
        problems=problems,
        worker_count=worker_count,
        run_problem=run_initial,
    )
    task_records_by_id = {task_record["task_id"]: task_record for task_record in task_records}

    initial_eval_summary = None
    repair_attempted_task_ids: list[str] = []
    final_samples_path = artifacts_dir / "samples.jsonl"
    eval_results_path = artifacts_dir / "humaneval.eval_results.json"
    eval_log_path = artifacts_dir / "evalplus.log"

    if repair_stages and not limited_run:
        initial_samples_path = artifacts_dir / "initial.samples.jsonl"
        _write_samples(initial_samples_path, task_records)
        initial_eval_results_path = artifacts_dir / "initial.humaneval.eval_results.json"
        initial_eval_log_path = artifacts_dir / "initial.evalplus.log"
        initial_eval_results = _evaluate_samples(initial_samples_path, initial_eval_results_path, initial_eval_log_path)
        initial_eval_summary = _summarize_eval(initial_eval_results)

        failed_task_ids = [
            task_id for task_id in sorted(initial_eval_results["eval"], key=_task_sort_key) if not _task_passed_eval(initial_eval_results["eval"][task_id])
        ]
        repair_attempted_task_ids = list(failed_task_ids)
        for task_id, task_record in task_records_by_id.items():
            task_record["initial_eval"] = initial_eval_results["eval"][task_id][0]
            _write_task_record(tasks_dir / _task_slug(task_id), task_record)

        if failed_task_ids:
            failed_problem_lookup = {problem["task_id"]: problem for problem in problems}

            def run_repair(problem: dict[str, Any]) -> dict[str, Any]:
                task_dir = tasks_dir / _task_slug(problem["task_id"])
                eval_failure = initial_eval_results["eval"][problem["task_id"]][0]
                return _repair_problem(
                    problem=problem,
                    task_record=task_records_by_id[problem["task_id"]],
                    session_strategy=scenario.session_strategy,
                    repair_stages=repair_stages,
                    config=config,
                    copilot_bin=copilot_bin,
                    task_dir=task_dir,
                    seen_cross_problem_session_ids=seen_cross_problem_session_ids,
                    session_lock=session_lock,
                    eval_failure=eval_failure,
                    submission_stage=scenario.submission_stage,
                )

            repaired_records = _run_problem_batch(
                problems=[failed_problem_lookup[task_id] for task_id in failed_task_ids],
                worker_count=worker_count,
                run_problem=run_repair,
            )
            for repaired_record in repaired_records:
                task_records_by_id[repaired_record["task_id"]] = repaired_record

        task_records = [task_records_by_id[problem["task_id"]] for problem in problems]

    _write_samples(final_samples_path, task_records)
    eval_summary = None
    if not limited_run:
        eval_results = _evaluate_samples(final_samples_path, eval_results_path, eval_log_path)
        eval_summary = _summarize_eval(eval_results)

    stage_cost_records: list[dict[str, Any]] = []
    predicted_failures = 0
    for task_record in task_records:
        review = task_record.get("review")
        if review and not review.get("will_pass", True):
            predicted_failures += 1
        for stage in task_record["stages"]:
            stage_cost_records.append({"model": stage["model"], "token_usage": stage["token_usage"]})

    runtime_seconds = time.monotonic() - started_at_mono
    ended_at_unix = time.time()
    cost_summary = _summarize_costs(stage_cost_records)

    summary = {
        "scenario_id": scenario.id,
        "display_name": scenario.display_name,
        "server": scenario.server,
        "task_count": len(task_records),
        "predicted_failures": predicted_failures,
        "repair_attempted_tasks": len(repair_attempted_task_ids),
        "repair_attempted_task_ids": repair_attempted_task_ids,
        "runtime_measurement": "wall_clock",
        "runtime_seconds": round(runtime_seconds, 6),
        "started_at_unix": started_at_unix,
        "ended_at_unix": ended_at_unix,
        "max_parallel_workers": config.max_parallel_workers,
        "parallel_workers_used": worker_count,
        "limited_run": limited_run,
        "eval": eval_summary,
        "costs": cost_summary,
        "artifacts": {
            "samples_path": str(final_samples_path),
            "task_records_path": str(artifacts_dir / "task_records.json"),
        },
    }
    if not limited_run:
        summary["artifacts"]["eval_results_path"] = str(eval_results_path)
    else:
        summary["eval_skipped_reason"] = "limited_run"
    if initial_eval_summary is not None:
        summary["initial_eval"] = initial_eval_summary
        summary["artifacts"]["initial_samples_path"] = str(artifacts_dir / "initial.samples.jsonl")
        summary["artifacts"]["initial_eval_results_path"] = str(artifacts_dir / "initial.humaneval.eval_results.json")

    _write_json(artifacts_dir / "task_records.json", {"tasks": task_records})
    _write_json(artifacts_dir / "summary.json", summary)
    return scenario_dir


def summarize_run(run_id: str, output_root: Path | None = None) -> Path:
    config = load_benchmark_config()
    output_root = output_root or (REPO_ROOT / "runs")
    run_dir = output_root / run_id
    comparison = {
        "run_id": run_id,
        "scenarios": [],
    }

    for scenario in config.scenarios:
        summary_path = run_dir / scenario.id / "artifacts" / "summary.json"
        if summary_path.exists():
            comparison["scenarios"].append(json.loads(summary_path.read_text(encoding="utf-8")))

    comparison_path = run_dir / "comparison.json"
    _write_json(comparison_path, comparison)
    return comparison_path


def build_run_scenario_parser(subparsers) -> None:
    parser = subparsers.add_parser("run-scenario", help="Run one scenario locally on the current machine")
    parser.add_argument("--scenario-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--limit", type=int, default=None, help="Optional task limit for smoke tests")
    parser.set_defaults(command="run-scenario")


def build_summarize_parser(subparsers) -> None:
    parser = subparsers.add_parser("summarize-run", help="Combine scenario summaries for a run")
    parser.add_argument("--run-id", required=True)
    parser.set_defaults(command="summarize-run")


def dispatch_runner_command(args: argparse.Namespace) -> int:
    if args.command == "run-scenario":
        run_scenario(scenario_id=args.scenario_id, run_id=args.run_id, limit=args.limit)
        return 0
    if args.command == "summarize-run":
        summarize_run(args.run_id)
        return 0
    raise ValueError(f"Unsupported runner command: {args.command}")
