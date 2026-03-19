# mini-benchmark

This repository tracks a benchmark comparing three ways of solving the full HumanEval+ suite with GitHub Copilot CLI.

## Scenarios

1. **`gpt-5.4-plan-code`**: `gpt-5.4` handles both `plan` and `code` on `muntz` at `--reasoning-effort medium`.
2. **`gpt-5.4-plan-gpt-5.4-mini-code`**: `gpt-5.4` plans at `--reasoning-effort high`, then `gpt-5.4-mini` codes at `--reasoning-effort xhigh` on `griswold`.
3. **`gpt-5.4-plan-gpt-5.4-mini-code-review-fix`**: the same mini-track flow on `griswold`, plus `gpt-5.4` review at `--reasoning-effort high` and a conditional `gpt-5.4-mini` fix at `--reasoning-effort xhigh`.

## What we will measure

- Percent of HumanEval+ problems solved correctly
- Input tokens
- Output tokens
- Cache read tokens
- Total token-derived cost using published OpenAI API pricing
- Total wall-clock time for each full benchmark run

## Benchmark pinning

- `evalplus==0.3.1`
- HumanEval+ dataset version: `v0.1.10` (via the pinned `evalplus` package)
- Pricing source: `https://openai.com/api/pricing/`

## Benchmark rules

- Use the **full HumanEval+ benchmark**, not an easy-only subset.
- Run **one pass per scenario** to limit inference cost.
- Run the scenarios on these servers:
  - `muntz`: `gpt-5.4-plan-code`
  - `griswold`: both mini-track scenarios
- Keep the runs aligned on the same default GitHub Copilot harness and tool surface.
- Prefer only the MCP servers and tools that are preloaded in the default GitHub Copilot CLI environment.
- Use the official HumanEval+ evaluator for correctness.
- Extract token telemetry from Copilot CLI logs so input, output, and cache-read tokens are captured from the actual runs.
- Price runs using the published OpenAI API rates for the models involved.
- Run each HumanEval+ problem in its own isolated workspace and never reuse one problem session for another problem.
- Disable custom Copilot instructions during benchmark runs so local AGENTS-style guidance does not leak into results.
- Measure runtime as wall-clock time from benchmark start to benchmark end.
- Limit any parallel agent or subagent workflow to at most 6 concurrent workers.
- In the review/fix scenario, the review gate is pass/fail only; style and cleanup feedback are out of scope.

## Expected outputs

This repository will store:

- Automation used to launch and evaluate the runs
- Raw benchmark artifacts and logs
- Parsed metrics for each scenario
- A final side-by-side comparison summary

## Harness layout

- `config/benchmark.json`: benchmark pinning, three scenario definitions, per-stage reasoning budgets, and the parallelism cap
- `config/pricing.openai.json`: explicit token pricing used for cost calculations
- `prompts/`: prompt templates for planning, coding, pass/fail review, and conditional fixing
- `mini_benchmark/`: Python harness for local execution, telemetry parsing, pricing, and remote orchestration
- `tests/`: lightweight unit tests for telemetry, pricing, and response parsing

## Main commands

Set up a Python environment and install the pinned benchmark dependency:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

Prepare a remote server without starting the benchmark:

```bash
python -m mini_benchmark prepare-server --host muntz
python -m mini_benchmark prepare-server --host griswold
```

Preview the remote launch commands without executing them:

```bash
python -m mini_benchmark launch-remote --run-id humaneval-full-001 --dry-run
```

Launch one selected scenario:

```bash
python -m mini_benchmark launch-remote --run-id humaneval-full-001 \
  --scenario-id gpt-5.4-plan-code
```

Launch multiple selected scenarios together:

```bash
python -m mini_benchmark launch-remote --run-id humaneval-full-001 \
  --scenario-id gpt-5.4-plan-gpt-5.4-mini-code \
  --scenario-id gpt-5.4-plan-gpt-5.4-mini-code-review-fix
```

If you omit `--scenario-id`, the harness targets all configured scenarios.

Collect artifacts and build a combined comparison after the remote runs finish:

```bash
python -m mini_benchmark collect-results --run-id humaneval-full-001
python -m mini_benchmark summarize-run --run-id humaneval-full-001
```
