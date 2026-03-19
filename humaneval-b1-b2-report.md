# HumanEval+ Benchmark Report

Run ID: `humaneval-b1-b2-20260319-1629`

Date: `2026-03-19`

## Scenarios

### Benchmark 1

- Scenario ID: `gpt-5.4-plan-code`
- Server: `muntz`
- Stages:
  - `plan`: `gpt-5.4` at `medium`
  - `code`: `gpt-5.4` at `medium`

### Benchmark 2

- Scenario ID: `gpt-5.4-plan-gpt-5.4-mini-code`
- Server: `griswold`
- Stages:
  - `plan`: `gpt-5.4` at `high`
  - `code`: `gpt-5.4-mini` at `xhigh`

## Executive Summary

Benchmark 2 was the better result on correctness and cost, but it was much slower.

- Correctness:
  - Benchmark 1 HumanEval+: `150 / 164` = `91.4634%`
  - Benchmark 2 HumanEval+: `153 / 164` = `93.2927%`
- Cost:
  - Benchmark 1: `$17.942092`
  - Benchmark 2: `$10.634113`
- Wall-clock runtime:
  - Benchmark 1: `5777.312s` = `1h 36m 17s`
  - Benchmark 2: `15814.830s` = `4h 23m 35s`

Relative to Benchmark 1, Benchmark 2 was:

- `40.7309%` cheaper
- `173.7403%` longer in wall-clock time
- `2.7374x` as slow end-to-end

## Correctness

### Base vs HumanEval+

- `base pass@1` = original HumanEval tests only
- `HumanEval+ pass@1` = original HumanEval tests plus the stronger EvalPlus extra tests

HumanEval+ is the stricter metric and is the better indicator of robustness.

### Results

| Metric | Benchmark 1 | Benchmark 2 |
| --- | ---: | ---: |
| Tasks | 164 | 164 |
| Base pass@1 | 97.6% | 98.8% |
| HumanEval+ pass@1 | 91.5% | 93.3% |
| Fully correct tasks (`base` + `plus`) | 150 | 153 |

## Token Usage

Pricing source: `config/pricing.openai.json`

### Benchmark 1 token totals

| Model | Input | Cached input read | Output | Requests |
| --- | ---: | ---: | ---: | ---: |
| `gpt-5.4` | 6,173,993 | 4,391,680 | 93,946 | 328 |

### Benchmark 2 token totals

| Model | Input | Cached input read | Output | Requests |
| --- | ---: | ---: | ---: | ---: |
| `gpt-5.4` | 3,024,103 | 1,423,872 | 72,897 | 164 |
| `gpt-5.4-mini` | 3,607,944 | 1,760,256 | 339,220 | 175 |

## Cost

Rates used:

- `gpt-5.4`
  - input: `$2.50 / 1M`
  - cached input: `$0.25 / 1M`
  - output: `$15.00 / 1M`
- `gpt-5.4-mini`
  - input: `$0.25 / 1M`
  - cached input: `$0.025 / 1M`
  - output: `$2.00 / 1M`

### Benchmark 1 cost

| Component | Amount |
| --- | ---: |
| `gpt-5.4` input cost | `$15.434983` |
| `gpt-5.4` cached input cost | `$1.097920` |
| `gpt-5.4` output cost | `$1.409190` |
| **Total** | **`$17.942092`** |

### Benchmark 2 cost

| Component | Amount |
| --- | ---: |
| `gpt-5.4` input cost | `$7.560258` |
| `gpt-5.4` cached input cost | `$0.355968` |
| `gpt-5.4` output cost | `$1.093455` |
| `gpt-5.4` subtotal | `$9.009680` |
| `gpt-5.4-mini` input cost | `$0.901986` |
| `gpt-5.4-mini` cached input cost | `$0.044006` |
| `gpt-5.4-mini` output cost | `$0.678440` |
| `gpt-5.4-mini` subtotal | `$1.624432` |
| **Total** | **`$10.634113`** |

## Runtime

The original harness run did not produce final local summaries because two separate issues got in the way:

- the detached local watcher command used during the live run had a shell concatenation bug, so automatic local collection/summarization never executed
- the repo-side EvalPlus integration called an older API shape (`output_file=`), which does not match the installed `evalplus==0.3.1`

Because of that, wall-clock runtime below is reconstructed from:

- `started_at_unix` in each scenario manifest
- the timestamp of the last pre-manual artifact written by the scenario run

These reconstructed runtimes are still good end-to-end estimates for scenario duration.

| Metric | Benchmark 1 | Benchmark 2 |
| --- | ---: | ---: |
| Estimated wall-clock runtime (seconds) | 5777.312 | 15814.830 |
| Estimated wall-clock runtime | 1h 36m 17s | 4h 23m 35s |
| Sum of stage wall times | 5767.590 | 15801.632 |

### Benchmark 2 runtime without the HumanEval/32 outlier

`HumanEval/32` was an extreme outlier for Benchmark 2. Its code stage took `5706.726s` (~`95.1` minutes).

To estimate a more normal total runtime, replace that one outlier with the **median Benchmark 2 code-stage time excluding HumanEval/32**, which was `20.768s`.

That yields an adjusted Benchmark 2 runtime of:

- `10128.871s` = `2h 48m 49s`

Compared with the observed Benchmark 2 runtime, that adjusted figure is:

- `5685.959s` shorter
- `35.9533%` lower

Compared with Benchmark 1, the adjusted Benchmark 2 runtime would still be:

- `75.3215%` longer
- `1.7532x` as slow end-to-end

## Why Benchmark 2 Took Longer

The architecture and the observed run data point to four main causes.

### 1. The planning stage was more expensive per task

Benchmark 2 used `gpt-5.4` at `high` for planning, while Benchmark 1 used `gpt-5.4` at `medium`.

Average per-task plan stage wall time:

- Benchmark 1: `18.451s`
- Benchmark 2: `21.578s`

That is only a modest slowdown, but it contributes across all 164 tasks.

### 2. The coding stage was dramatically slower

Benchmark 2 used `gpt-5.4-mini` at `xhigh` for coding, while Benchmark 1 used `gpt-5.4` at `medium`.

Average per-task code stage wall time:

- Benchmark 1: `16.717s`
- Benchmark 2: `74.774s`

This is the main reason the overall runtime blew up.

### 3. There was a severe outlier task in Benchmark 2

The slowest stage in Benchmark 2 was:

- Task: `HumanEval/32`
- Stage: `code`
- Model: `gpt-5.4-mini`
- Reasoning effort: `xhigh`
- Wall time: `5706.726s` (~`95.1` minutes)

This single stage consumed a large fraction of the scenario runtime.

### 4. The run was sequential, so one slow task blocked everything behind it

Although the harness recorded a fairness cap of `max_parallel_workers = 6`, the actual scenario runner processed tasks sequentially:

- `parallel_workers_used = 1`

That means one pathological slow code generation step delayed every subsequent task.

### Additional observed retry behavior

For `HumanEval/32` on Benchmark 2, the stage stdout included three transient retry events:

- `2026-03-19T17:28:45.395Z`
- `2026-03-19T17:59:00.936Z`
- `2026-03-19T18:29:16.095Z`

So Benchmark 2 was not just slower because of model selection and reasoning effort; at least one task also experienced repeated backend/API retries.

## Interpretation

If the goal is lowest cost while preserving or slightly improving correctness, Benchmark 2 won this comparison.

If the goal is fastest wall-clock completion, Benchmark 1 was much better.

On these two runs:

- Benchmark 2 improved HumanEval+ correctness by `3` tasks
- Benchmark 2 reduced spend by about `$7.31`
- Benchmark 2 added about `2h 47m 18s` of wall-clock runtime
- Even after normalizing the `HumanEval/32` outlier to a typical benchmark-2 code-stage time, Benchmark 2 still would have taken about `1h 12m 32s` longer than Benchmark 1

## Method Notes

- Both scenarios completed all `164` HumanEval tasks.
- Correctness was computed manually after the run by invoking EvalPlus directly on each scenario's `samples.jsonl`.
- The raw scenario artifacts remain on the remote hosts under:
  - `~/mini-benchmark/runs/humaneval-b1-b2-20260319-1629/gpt-5.4-plan-code`
  - `~/mini-benchmark/runs/humaneval-b1-b2-20260319-1629/gpt-5.4-plan-gpt-5.4-mini-code`
- The repo-side EvalPlus integration has now been updated to match the installed EvalPlus output convention.
