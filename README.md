# mini-benchmark

`mini-benchmark` is a repository for comparing multiple ways of solving the full HumanEval+ suite with **GitHub Copilot CLI** as the coding harness.

The goal is not just to compare models. It is to compare **end-to-end coding workflows** built on the same Copilot CLI interface: planning, coding, review, repair, direct-fix, and single-pass variants, all evaluated against the same HumanEval+ benchmark and measured for correctness, runtime, token usage, and cost.

## Executive Summary

The completed runs currently point to three different winners, depending on what you care about.

- **Best overall correctness:** Benchmark 4 with `160 / 164` fully correct tasks (`97.5610%`).
- **Best single-pass baseline:** Benchmark 6 with `155 / 164` fully correct tasks (`94.5122%`).
- **Cheapest and fastest run:** Benchmark 5 at `$9.716830` and `3251.658s` (`54m 12s`).

Benchmark 6 shows that `claude-opus-4.6` can beat the single-pass GPT baselines on correctness, but it does so at a very high cost. Benchmark 4 is still the best overall result because its repair path raises correctness much further while staying relatively fast. Benchmark 5 remains the strongest efficiency tradeoff.

### Current benchmark results

| Benchmark | Status | Fully correct (`base` + `plus`) | Total cost | Runtime | Main takeaway |
| --- | --- | ---: | ---: | ---: | --- |
| Benchmark 1 | Complete | 150 / 164 | `$17.942092` | `1h 36m 17s` | GPT-5.4 baseline |
| Benchmark 2 | Complete | 153 / 164 | `$10.634113` | `4h 23m 35s` | Cheaper than Benchmark 1, but very slow |
| Benchmark 3 | Not yet run | — | — | — | Review/fix variant on the mini track |
| Benchmark 4 | Complete | 160 / 164 | `$10.934886` | `59m 26s` | Best overall correctness |
| Benchmark 5 | Complete | 153 / 164 | `$9.716830` | `54m 12s` | Cheapest and fastest completed run |
| Benchmark 6 | Complete | 155 / 164 | `$40.944668` | `1h 28m 5s` | Best single-pass baseline, but very expensive |

For the full benchmark write-up, see [`humaneval-b1-b2-report.md`](./humaneval-b1-b2-report.md).

## Why GitHub Copilot CLI Is the Harness

The core design choice in this repo is to benchmark coding workflows through **GitHub Copilot CLI**, not through direct model API calls or ad hoc scripts.

That matters because Copilot CLI is the actual coding surface being studied.

- It provides the same terminal-agent environment across scenarios.
- It exposes model choice and reasoning effort through the same CLI interface.
- It produces structured logs that can be mined for token telemetry.
- It lets the benchmark compare workflow design while holding the tool surface mostly constant.

In other words, this project is measuring how different Copilot-driven workflows behave under a shared coding harness, not just how raw models score in isolation.

### Common Copilot harness settings

All benchmark stages are launched through the same Copilot CLI defaults from `config/benchmark.json`:

- `--allow-all`
- `--no-ask-user`
- `--no-custom-instructions`
- `--output-format json`
- `--stream off`
- `--log-level debug`

Those settings are important because they keep the runs comparable and make telemetry collection reliable.

## Methodology

### What is being measured

Every completed run in this repo is evaluated on:

- strict HumanEval+ correctness
- base HumanEval pass rate
- input, output, and cached-input tokens
- total token-derived cost using published vendor pricing
- total wall-clock runtime

### Fairness rules

The benchmark tries to hold the execution environment steady while varying only the workflow and model choices.

- Use the **full HumanEval+ suite** (`164` tasks).
- Use the HumanEval task prompt only; do not inspect hidden tests or known solutions.
- Run one pass per scenario.
- Use the same Copilot CLI harness defaults across scenarios.
- Run each HumanEval task in its own isolated workspace.
- Use fresh Copilot sessions by default rather than carrying over task state.
- Disable custom Copilot instructions during benchmark execution.
- Cap any parallel workflow at `6` workers.

### Evaluation pipeline

- Code generation is driven by GitHub Copilot CLI.
- Correctness is judged with the official EvalPlus / HumanEval+ evaluator.
- Token telemetry is parsed from Copilot CLI logs captured during each run.
- Pricing is computed from `config/pricing.openai.json`, which now stores the configured model pricing across vendors.
- Remote execution happens over SSH on the benchmark hosts (`muntz` and `griswold`).

## Scenario Catalog

| Benchmark | Scenario ID | Server | Flow | Workers | Purpose |
| --- | --- | --- | --- | ---: | --- |
| Benchmark 1 | `gpt-5.4-plan-code` | `muntz` | `plan` -> `code` | 1 | Plain GPT-5.4 baseline |
| Benchmark 2 | `gpt-5.4-plan-gpt-5.4-mini-code` | `griswold` | `plan` -> `code` | 1 | Mixed-model baseline |
| Benchmark 3 | `gpt-5.4-plan-gpt-5.4-mini-code-review-fix` | `griswold` | `plan` -> `code` -> `review` -> `fix` | 1 | Review-gated repair flow |
| Benchmark 4 | `gpt-5.4-plan-gpt-5.4-mini-code-eval-repair` | `muntz` | `plan` -> `code` -> `repair_plan` -> `fix` | 2 | EvalPlus-gated repair flow |
| Benchmark 5 | `gpt-5.4-plan-gpt-5.4-mini-code-eval-direct-fix` | `muntz` | `plan` -> `code` -> `fix` | 2 | EvalPlus-gated direct-fix flow |
| Benchmark 6 | `claude-opus-4.6-plan-code` | `griswold` | `plan` -> `code` | 1 | Opus single-pass baseline |

## Tools Used

The repo is intentionally small, but the toolchain is specific.

- **GitHub Copilot CLI**: the coding harness under test
- **EvalPlus / HumanEval+**: the correctness evaluator
- **Python**: local orchestration, parsing, and summarization
- **SSH / SCP**: remote execution and artifact collection
- **Structured prompt templates** in `prompts/`: scenario-specific planning, coding, review, and repair prompts

## Repository Layout

- `config/benchmark.json`: benchmark configuration, scenario definitions, reasoning budgets, and remote settings
- `config/pricing.openai.json`: pricing metadata for all configured models
- `prompts/`: prompt templates for each benchmark stage
- `mini_benchmark/`: the Python harness for launching runs, parsing logs, pricing usage, and summarizing results
- `tests/`: lightweight unit tests for the harness
- `runs/`: collected run artifacts copied back from remote hosts
- `humaneval-b1-b2-report.md`: the detailed benchmark comparison report

## Main Commands

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
  --scenario-id gpt-5.4-plan-gpt-5.4-mini-code-review-fix \
  --scenario-id gpt-5.4-plan-gpt-5.4-mini-code-eval-repair \
  --scenario-id gpt-5.4-plan-gpt-5.4-mini-code-eval-direct-fix \
  --scenario-id claude-opus-4.6-plan-code
```

If you omit `--scenario-id`, the harness targets all configured scenarios.

Collect artifacts and build a combined comparison after remote runs finish:

```bash
python -m mini_benchmark collect-results --run-id humaneval-full-001
python -m mini_benchmark summarize-run --run-id humaneval-full-001
```
