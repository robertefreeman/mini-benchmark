# HumanEval+ Benchmark Report

Run IDs:

- `humaneval-b1-b2-20260319-1629`
- `humaneval-b4-20260321-1346`

Date range: `2026-03-19` to `2026-03-21`

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

### Benchmark 4

- Scenario ID: `gpt-5.4-plan-gpt-5.4-mini-code-eval-repair`
- Server: `muntz`
- Stages:
  - `plan`: `gpt-5.4` at `medium`
  - `code`: `gpt-5.4-mini` at `medium`
  - `repair_plan`: `gpt-5.4` at `high`
  - `fix`: `gpt-5.4-mini` at `high`
- Parallel workers used: `2`

## Executive Summary

Benchmark 4 was the strongest overall result among the completed runs in this report.

Its initial pass matched Benchmark 2 on fully correct tasks, and its EvalPlus-gated repair flow lifted final correctness to the best score in the set while keeping cost close to Benchmark 2 and finishing much faster than either earlier run.

- Correctness:
  - Benchmark 1 HumanEval+: `150 / 164` = `91.4634%`
  - Benchmark 2 HumanEval+: `153 / 164` = `93.2927%`
  - Benchmark 4 initial HumanEval+: `153 / 164` = `93.2927%`
  - Benchmark 4 final HumanEval+: `160 / 164` = `97.5610%`
- Cost:
  - Benchmark 1: `$17.942092`
  - Benchmark 2: `$10.634113`
  - Benchmark 4: `$10.934886`
- Wall-clock runtime:
  - Benchmark 1: `5777.312s` = `1h 36m 17s`
  - Benchmark 2: `15814.830s` = `4h 23m 35s`
  - Benchmark 4: `3566.476s` = `59m 26s`

Relative to Benchmark 2, Benchmark 4 was:

- `7` more fully correct tasks after repair
- `$0.300773` more expensive (`2.8284%`)
- `3h 24m 8.354s` faster (`77.4485%` shorter)

Relative to Benchmark 1, Benchmark 4 was:

- `10` more fully correct tasks
- `$7.007206` cheaper (`39.0546%`)
- `36m 50.836s` faster (`38.2676%` shorter)

## Correctness

### Base vs HumanEval+

- `base pass@1` = original HumanEval tests only
- `HumanEval+ pass@1` = original HumanEval tests plus the stronger EvalPlus extra tests

HumanEval+ is the stricter metric and is the better indicator of robustness.

### Results

| Metric | Benchmark 1 | Benchmark 2 | Benchmark 4 |
| --- | ---: | ---: | ---: |
| Tasks | 164 | 164 | 164 |
| Base pass@1 | 97.6% | 98.8% | 98.8% |
| HumanEval+ pass@1 | 91.5% | 93.3% | 98.2% |
| Fully correct tasks (`base` + `plus`) | 150 | 153 | 160 |

### Benchmark 4 repair lift

- Initial fully correct tasks before repair: `153 / 164` = `93.2927%`
- Repair attempted on `11` tasks:
  - `HumanEval/32`
  - `HumanEval/39`
  - `HumanEval/91`
  - `HumanEval/97`
  - `HumanEval/99`
  - `HumanEval/101`
  - `HumanEval/116`
  - `HumanEval/132`
  - `HumanEval/141`
  - `HumanEval/145`
  - `HumanEval/151`
- Improved by repair: `7` tasks
  - `HumanEval/39`
  - `HumanEval/97`
  - `HumanEval/101`
  - `HumanEval/132`
  - `HumanEval/141`
  - `HumanEval/145`
  - `HumanEval/151`
- Still failing after repair:
  - `HumanEval/32`
  - `HumanEval/91`
  - `HumanEval/99`
  - `HumanEval/116`

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

### Benchmark 4 token totals

| Model | Input | Cached input read | Output | Requests |
| --- | ---: | ---: | ---: | ---: |
| `gpt-5.4` | 3,083,724 | 1,450,368 | 77,285 | 175 |
| `gpt-5.4-mini` | 5,285,182 | 3,541,504 | 146,938 | 279 |

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

### Benchmark 4 cost

| Component | Amount |
| --- | ---: |
| `gpt-5.4` input cost | `$7.709310` |
| `gpt-5.4` cached input cost | `$0.362592` |
| `gpt-5.4` output cost | `$1.159275` |
| `gpt-5.4` subtotal | `$9.231177` |
| `gpt-5.4-mini` input cost | `$1.321296` |
| `gpt-5.4-mini` cached input cost | `$0.088538` |
| `gpt-5.4-mini` output cost | `$0.293876` |
| `gpt-5.4-mini` subtotal | `$1.703709` |
| **Total** | **`$10.934886`** |

## Runtime

The original harness run did not produce final local summaries because two separate issues got in the way:

- the detached local watcher command used during the live run had a shell concatenation bug, so automatic local collection/summarization never executed
- the repo-side EvalPlus integration called an older API shape (`output_file=`), which does not match the installed `evalplus==0.3.1`

Because of that, wall-clock runtime for Benchmarks 1 and 2 is reconstructed from:

- `started_at_unix` in each scenario manifest
- the timestamp of the last pre-manual artifact written by the scenario run

These reconstructed runtimes are still good end-to-end estimates for scenario duration.

Benchmark 4 completed after the auth-persistence and EvalPlus-flow fixes, so its runtime below comes directly from the final `summary.json`.

| Metric | Benchmark 1 | Benchmark 2 | Benchmark 4 |
| --- | ---: | ---: | ---: |
| Wall-clock runtime (seconds) | 5777.312 | 15814.830 | 3566.476 |
| Wall-clock runtime | 1h 36m 17s | 4h 23m 35s | 59m 26s |
| Runtime source | reconstructed | reconstructed | direct from `summary.json` |

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

## Why Benchmark 2 Took Longer Than Benchmark 1

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

If the goal is strongest combined outcome among the completed runs, Benchmark 4 won.

Benchmark 2 still had the lowest cost by a small margin, but Benchmark 4 closed that gap to about `$0.30` while delivering much better final correctness and a dramatically shorter runtime.

If the goal is fastest wall-clock completion among the completed full-benchmark runs in the repo, Benchmark 4 also won.

Across the three completed runs documented here:

- Benchmark 4 improved fully correct tasks by `10` over Benchmark 1 and by `7` over Benchmark 2
- Benchmark 4 was `$7.007206` cheaper than Benchmark 1
- Benchmark 4 was only `$0.300773` more expensive than Benchmark 2
- Benchmark 4 finished `36m 50.836s` faster than Benchmark 1
- Benchmark 4 finished `3h 24m 8.354s` faster than Benchmark 2

## Method Notes

- Both original scenarios completed all `164` HumanEval tasks.
- Benchmark 4 also completed all `164` HumanEval tasks, with `11` EvalPlus-gated repair attempts under a `2`-worker configuration on `muntz`.
- Correctness in this report comes from EvalPlus outputs generated from each scenario's `samples.jsonl`.
- The raw scenario artifacts remain on the remote hosts under:
  - `~/mini-benchmark/runs/humaneval-b1-b2-20260319-1629/gpt-5.4-plan-code`
  - `~/mini-benchmark/runs/humaneval-b1-b2-20260319-1629/gpt-5.4-plan-gpt-5.4-mini-code`
  - `~/mini-benchmark/runs/humaneval-b4-20260321-1346/gpt-5.4-plan-gpt-5.4-mini-code-eval-repair`
- The repo-side EvalPlus integration has now been updated to match the installed EvalPlus output convention.
