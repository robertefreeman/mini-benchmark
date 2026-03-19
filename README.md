# mini-benchmark

This repository tracks a benchmark comparing two ways of solving the full HumanEval+ suite with GitHub Copilot CLI.

## Scenarios

1. **GPT-5.4 only**: `gpt-5.4` handles the work directly.
2. **Planner/coder split**: `gpt-5.4` handles planning and evaluation, while `gpt-5.4-mini` handles coding tasks.

## What we will measure

- Percent of HumanEval+ problems solved correctly
- Input tokens
- Output tokens
- Cache read tokens
- Total token-derived cost using published OpenAI API pricing
- Total wall-clock time for each full benchmark run

## Benchmark rules

- Use the **full HumanEval+ benchmark**, not an easy-only subset.
- Run **one pass per scenario** to limit inference cost.
- Run the two scenarios on separate servers:
  - `muntz`: GPT-5.4 only
  - `griswold`: GPT-5.4 planning/evaluation plus GPT-5.4-mini coding
- Keep the runs aligned on the same default GitHub Copilot harness and tool surface.
- Prefer only the MCP servers and tools that are preloaded in the default GitHub Copilot CLI environment.
- Use the official HumanEval+ evaluator for correctness.
- Extract token telemetry from Copilot CLI logs so input, output, and cache-read tokens are captured from the actual runs.
- Price runs using the published OpenAI API rates for the models involved.

## Expected outputs

This repository will store:

- Automation used to launch and evaluate the runs
- Raw benchmark artifacts and logs
- Parsed metrics for each scenario
- A final side-by-side comparison summary
