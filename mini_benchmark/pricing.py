from __future__ import annotations

import json
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

from .config import PRICING_PATH


ONE_MILLION = Decimal("1000000")
MONEY_QUANT = Decimal("0.000001")


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)


def load_pricing() -> dict:
    return json.loads(Path(PRICING_PATH).read_text(encoding="utf-8"))


def resolve_model_name(model: str, pricing: dict) -> str:
    for canonical_name, details in pricing["models"].items():
        if model == canonical_name or model in details.get("aliases", []):
            return canonical_name
    raise KeyError(f"No pricing configured for model: {model}")


def calculate_cost(model: str, usage: dict[str, int], pricing: dict | None = None) -> dict[str, float]:
    pricing = pricing or load_pricing()
    canonical_name = resolve_model_name(model, pricing)
    model_pricing = pricing["models"][canonical_name]

    input_cost = (
        Decimal(usage["input_tokens"]) * Decimal(str(model_pricing["input_per_million_usd"])) / ONE_MILLION
    )
    cache_read_cost = (
        Decimal(usage["cache_read_tokens"])
        * Decimal(str(model_pricing["cached_input_per_million_usd"]))
        / ONE_MILLION
    )
    output_cost = (
        Decimal(usage["output_tokens"]) * Decimal(str(model_pricing["output_per_million_usd"])) / ONE_MILLION
    )
    total_cost = input_cost + cache_read_cost + output_cost

    return {
        "input_cost_usd": float(_quantize(input_cost)),
        "cache_read_cost_usd": float(_quantize(cache_read_cost)),
        "output_cost_usd": float(_quantize(output_cost)),
        "total_cost_usd": float(_quantize(total_cost)),
        "canonical_model": canonical_name,
    }


def aggregate_usage(records: list[dict]) -> dict[str, dict[str, int]]:
    totals: dict[str, dict[str, int]] = {}
    for record in records:
        model = record["model"]
        usage = record["token_usage"]
        if model not in totals:
            totals[model] = {
                "input_tokens": 0,
                "output_tokens": 0,
                "cache_read_tokens": 0,
                "cache_write_tokens": 0,
                "request_count": 0,
            }
        for key in totals[model]:
            totals[model][key] += int(usage.get(key, 0))
    return totals

