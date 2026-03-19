from __future__ import annotations

import re
from pathlib import Path


SUMMARY_METRIC_RE = re.compile(
    r'"model_(?P<model>[^"]+?)_(?P<metric>input_tokens|output_tokens|cache_read_tokens|cache_write_tokens|request_count|request_cost)": "(?P<value>\d+)"'
)
USAGE_BLOCK_RE = re.compile(
    r'"kind": "assistant_usage".*?"model": "(?P<model>[^"]+)".*?"input_tokens_uncached": (?P<input_tokens>\d+).*?"output_tokens": (?P<output_tokens>\d+).*?"cache_read_tokens": (?P<cache_read_tokens>\d+).*?"cache_write_tokens": (?P<cache_write_tokens>\d+)',
    re.S,
)


def _blank_usage() -> dict[str, int]:
    return {
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_read_tokens": 0,
        "cache_write_tokens": 0,
        "request_count": 0,
        "request_cost_units": 0,
    }


def _merge_usage(target: dict[str, dict[str, int]], model: str, metric: str, value: int) -> None:
    if model not in target:
        target[model] = _blank_usage()
    if metric == "request_cost":
        target[model]["request_cost_units"] += value
        return
    target[model][metric] += value


def parse_log_file(path: Path) -> dict[str, dict[str, int]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    usage_by_model: dict[str, dict[str, int]] = {}

    matches = list(SUMMARY_METRIC_RE.finditer(text))
    if matches:
        for match in matches:
            _merge_usage(
                usage_by_model,
                match.group("model"),
                match.group("metric"),
                int(match.group("value")),
            )
        return usage_by_model

    for match in USAGE_BLOCK_RE.finditer(text):
        model = match.group("model")
        if model not in usage_by_model:
            usage_by_model[model] = _blank_usage()
        usage_by_model[model]["input_tokens"] += int(match.group("input_tokens"))
        usage_by_model[model]["output_tokens"] += int(match.group("output_tokens"))
        usage_by_model[model]["cache_read_tokens"] += int(match.group("cache_read_tokens"))
        usage_by_model[model]["cache_write_tokens"] += int(match.group("cache_write_tokens"))
        usage_by_model[model]["request_count"] += 1

    return usage_by_model


def parse_log_dir(log_dir: Path) -> dict[str, dict[str, int]]:
    combined: dict[str, dict[str, int]] = {}
    for log_path in sorted(log_dir.glob("process-*.log")):
        parsed = parse_log_file(log_path)
        for model, usage in parsed.items():
            if model not in combined:
                combined[model] = _blank_usage()
            for key, value in usage.items():
                combined[model][key] += value
    return combined

