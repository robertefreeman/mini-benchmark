# HumanEval+ Benchmark Report

Run IDs:

- `humaneval-b1-b2-20260319-1629`
- `humaneval-b4-20260321-1346`
- `humaneval-b5-20260323-1814`
- `humaneval-b6-20260324-1619`

Date range: `2026-03-19` to `2026-03-24`

## Executive Summary

The completed runs now show three distinct leaders, depending on what matters most.

- **Best overall correctness:** Benchmark 4, with `160 / 164` fully correct tasks (`97.5610%`).
- **Best single-pass correctness:** Benchmark 6, with `155 / 164` fully correct tasks (`94.5122%`) and no repair flow.
- **Best cost and runtime:** Benchmark 5, at `$9.716830` and `3251.658s` (`54m 12s`).

Benchmark 6 is the strongest no-repair run in the set, beating Benchmarks 1, 2, and 5 on strict correctness. But it is also by far the most expensive run, so it does not beat Benchmark 4 overall and it is a much weaker efficiency tradeoff than Benchmark 5.

### Headline takeaways

- Benchmark 4 remained the best all-around result because its repair flow lifted strict correctness from `153` to `160` while keeping runtime under an hour.
- Benchmark 5 showed that a direct-fix path can be very efficient, but in this run it produced **no** lift over its initial pass.
- Benchmark 6 showed that `claude-opus-4.6` can beat the single-pass GPT-5.4 baselines on correctness, but only at a much higher token cost.
- Relative to Benchmark 1, Benchmark 6 delivered `5` more fully correct tasks and finished `8m 11.708s` faster, but cost `$23.002576` more.
- Relative to Benchmark 5, Benchmark 6 delivered `2` more fully correct tasks, but cost `$31.227838` more and took `33m 53.946s` longer.

## Scenario Matrix

| Benchmark | Scenario ID | Server | Flow | Parallel workers | Completed run in repo summary |
| --- | --- | --- | --- | ---: | --- |
| Benchmark 1 | `gpt-5.4-plan-code` | `muntz` | `plan` -> `code` | 1 | Yes |
| Benchmark 2 | `gpt-5.4-plan-gpt-5.4-mini-code` | `griswold` | `plan` -> `code` | 1 | Yes |
| Benchmark 4 | `gpt-5.4-plan-gpt-5.4-mini-code-eval-repair` | `muntz` | `plan` -> `code` -> `repair_plan` -> `fix` | 2 | Yes |
| Benchmark 5 | `gpt-5.4-plan-gpt-5.4-mini-code-eval-direct-fix` | `muntz` | `plan` -> `code` -> `fix` | 2 | Yes |
| Benchmark 6 | `claude-opus-4.6-plan-code` | `griswold` | `plan` -> `code` | 1 | Yes |

## Headline Results

### Correctness, cost, and runtime

- `Base pass@1` = original HumanEval tests only
- `HumanEval+ pass@1` = original HumanEval tests plus the stronger EvalPlus extra tests

| Metric | Benchmark 1 | Benchmark 2 | Benchmark 4 | Benchmark 5 | Benchmark 6 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Tasks | 164 | 164 | 164 | 164 | 164 |
| Base pass@1 | 97.6% | 98.8% | 98.8% | 97.6% | 98.8% |
| HumanEval+ pass@1 | 91.5% | 93.3% | 97.6% | 93.3% | 94.5% |
| Fully correct tasks (`base` + `plus`) | 150 | 153 | 160 | 153 | 155 |
| Total cost | `$17.942092` | `$10.634113` | `$10.934886` | `$9.716830` | `$40.944668` |
| Wall-clock runtime (seconds) | `5777.312` | `15814.830` | `3566.476` | `3251.658` | `5285.604` |
| Wall-clock runtime | `1h 36m 17s` | `4h 23m 35s` | `59m 26s` | `54m 12s` | `1h 28m 5s` |
| Runtime source | reconstructed | reconstructed | direct | direct | direct |
| Parallel workers used | 1 | 1 | 2 | 2 | 1 |
| EvalPlus repair/direct-fix attempts | 0 | 0 | 11 | 11 | 0 |

### Repair-flow outcomes

| Benchmark | Initial fully correct | Final fully correct | Net lift | Attempts | Notes |
| --- | ---: | ---: | ---: | ---: | --- |
| Benchmark 4 | 153 | 160 | +7 | 11 | Best overall result in the set |
| Benchmark 5 | 153 | 153 | +0 | 11 | Cheapest and fastest, but no correctness lift |

## Benchmark-by-Benchmark Notes

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

### Benchmark 5 direct-fix outcome

- Initial fully correct tasks before direct fix: `153 / 164` = `93.2927%`
- Direct fix attempted on `11` tasks:
  - `HumanEval/32`
  - `HumanEval/39`
  - `HumanEval/89`
  - `HumanEval/91`
  - `HumanEval/93`
  - `HumanEval/99`
  - `HumanEval/116`
  - `HumanEval/132`
  - `HumanEval/141`
  - `HumanEval/145`
  - `HumanEval/151`
- Improved by direct fix: `0` tasks
- Still failing after direct fix:
  - `HumanEval/32`
  - `HumanEval/39`
  - `HumanEval/89`
  - `HumanEval/91`
  - `HumanEval/93`
  - `HumanEval/99`
  - `HumanEval/116`
  - `HumanEval/132`
  - `HumanEval/141`
  - `HumanEval/145`
  - `HumanEval/151`
- No tasks regressed under direct fix.

### Benchmark 6 outcome

Benchmark 6 had no repair path: it was a straight `plan` -> `code` run using `claude-opus-4.6` on `griswold`.

- Fully correct tasks: `155 / 164` = `94.5122%`
- Base pass count: `162 / 164` = `98.7805%`
- HumanEval+ pass count: `155 / 164` = `94.5122%`
- Failures after the single pass: `9` tasks

Tasks still not fully correct in Benchmark 6:

- `HumanEval/32` (`base=fail`, `plus=fail`)
- `HumanEval/39` (`base=pass`, `plus=fail`)
- `HumanEval/76` (`base=pass`, `plus=fail`)
- `HumanEval/91` (`base=pass`, `plus=fail`)
- `HumanEval/124` (`base=pass`, `plus=fail`)
- `HumanEval/132` (`base=fail`, `plus=fail`)
- `HumanEval/151` (`base=pass`, `plus=fail`)
- `HumanEval/154` (`base=pass`, `plus=fail`)
- `HumanEval/163` (`base=pass`, `plus=fail`)

## Token Usage

Pricing source: `config/pricing.openai.json`

| Benchmark | Model | Input | Cached input read | Output | Requests |
| --- | --- | ---: | ---: | ---: | ---: |
| Benchmark 1 | `gpt-5.4` | 6,173,993 | 4,391,680 | 93,946 | 328 |
| Benchmark 2 | `gpt-5.4` | 3,024,103 | 1,423,872 | 72,897 | 164 |
| Benchmark 2 | `gpt-5.4-mini` | 3,607,944 | 1,760,256 | 339,220 | 175 |
| Benchmark 4 | `gpt-5.4` | 3,083,724 | 1,450,368 | 77,285 | 175 |
| Benchmark 4 | `gpt-5.4-mini` | 5,285,182 | 3,541,504 | 146,938 | 279 |
| Benchmark 5 | `gpt-5.4` | 2,882,895 | 1,423,488 | 50,331 | 164 |
| Benchmark 5 | `gpt-5.4-mini` | 4,554,416 | 2,743,808 | 95,778 | 248 |
| Benchmark 6 | `claude-opus-4.6` | 7,568,883 | 3,929,555 | 45,419 | 333 |

## Cost Breakdown

Rates used:

- `gpt-5.4`
  - input: `$2.50 / 1M`
  - cached input: `$0.25 / 1M`
  - output: `$15.00 / 1M`
- `gpt-5.4-mini`
  - input: `$0.25 / 1M`
  - cached input: `$0.025 / 1M`
  - output: `$2.00 / 1M`
- `claude-opus-4.6`
  - input: `$5.00 / 1M`
  - cached input: `$0.50 / 1M`
  - output: `$25.00 / 1M`

| Benchmark | Model | Input cost | Cached input cost | Output cost | Subtotal |
| --- | --- | ---: | ---: | ---: | ---: |
| Benchmark 1 | `gpt-5.4` | `$15.434983` | `$1.097920` | `$1.409190` | `$17.942092` |
| Benchmark 2 | `gpt-5.4` | `$7.560258` | `$0.355968` | `$1.093455` | `$9.009680` |
| Benchmark 2 | `gpt-5.4-mini` | `$0.901986` | `$0.044006` | `$0.678440` | `$1.624432` |
| Benchmark 4 | `gpt-5.4` | `$7.709310` | `$0.362592` | `$1.159275` | `$9.231177` |
| Benchmark 4 | `gpt-5.4-mini` | `$1.321296` | `$0.088538` | `$0.293876` | `$1.703709` |
| Benchmark 5 | `gpt-5.4` | `$7.207238` | `$0.355872` | `$0.754965` | `$8.318075` |
| Benchmark 5 | `gpt-5.4-mini` | `$1.138604` | `$0.068595` | `$0.191556` | `$1.398755` |
| Benchmark 6 | `claude-opus-4.6` | `$37.844415` | `$1.964778` | `$1.135475` | `$40.944668` |

## Runtime Notes

Wall-clock runtime for Benchmarks 1 and 2 is reconstructed because the original harness runs did not produce final local summaries. Two issues caused that:

- the detached local watcher command used during the live run had a shell concatenation bug, so automatic local collection/summarization never executed
- the repo-side EvalPlus integration called an older API shape (`output_file=`), which does not match the installed `evalplus==0.3.1`

For those two runs, runtime is reconstructed from:

- `started_at_unix` in each scenario manifest
- the timestamp of the last pre-manual artifact written by the scenario run

Benchmarks 4, 5, and 6 completed after the auth-persistence and EvalPlus-flow fixes, so their runtimes come directly from `summary.json`.

### Benchmark 2 outlier note

`HumanEval/32` was an extreme outlier for Benchmark 2. Its `code` stage took `5706.726s` (~`95.1` minutes).

If that one task is replaced with the **median Benchmark 2 code-stage time excluding HumanEval/32** (`20.768s`), the adjusted Benchmark 2 runtime becomes:

- `10128.871s` = `2h 48m 49s`

That would still leave Benchmark 2:

- `75.3215%` slower than Benchmark 1
- `1.7532x` as slow end-to-end as Benchmark 1

## Interpretation

### Which benchmark won?

- **Best overall correctness:** Benchmark 4 (`160 / 164`)
- **Best single-pass correctness:** Benchmark 6 (`155 / 164`)
- **Cheapest completed run:** Benchmark 5 (`$9.716830`)
- **Fastest completed run:** Benchmark 5 (`3251.658s`)

### What Benchmark 6 changes

Benchmark 6 is important because it is not just another expensive variant. It shows that a plain `plan` + `code` flow on `claude-opus-4.6` can beat every other **non-repair** run in strict correctness.

But it also shows a poor efficiency tradeoff relative to the GPT-based alternatives:

- vs Benchmark 1: `+5` fully correct tasks, `8m 11.708s` faster, but `$23.002576` more expensive
- vs Benchmark 2: `+2` fully correct tasks, `2h 55m 29.226s` faster, but `$30.310555` more expensive
- vs Benchmark 4: `-5` fully correct tasks, `28m 39.128s` slower, and `$30.009782` more expensive
- vs Benchmark 5: `+2` fully correct tasks, `33m 53.946s` slower, and `$31.227838` more expensive

### Bottom line

- If the goal is the **strongest final result**, Benchmark 4 remains the best benchmark in the repo.
- If the goal is the **best no-repair baseline**, Benchmark 6 is now the benchmark to beat.
- If the goal is the **best efficiency tradeoff**, Benchmark 5 remains the clear winner.

## Method Notes

- Every completed benchmark in this report used the full `164`-task HumanEval+ suite.
- Correctness comes from EvalPlus outputs generated from each scenario's `samples.jsonl`.
- The harness uses fresh Copilot sessions by default and carries context between stages through prompt artifacts rather than `--resume`.
- Token usage is extracted from GitHub Copilot CLI logs produced during the actual run.
- The raw scenario artifacts remain on the remote hosts under:
  - `~/mini-benchmark/runs/humaneval-b1-b2-20260319-1629/gpt-5.4-plan-code`
  - `~/mini-benchmark/runs/humaneval-b1-b2-20260319-1629/gpt-5.4-plan-gpt-5.4-mini-code`
  - `~/mini-benchmark/runs/humaneval-b4-20260321-1346/gpt-5.4-plan-gpt-5.4-mini-code-eval-repair`
  - `~/mini-benchmark/runs/humaneval-b5-20260323-1814/gpt-5.4-plan-gpt-5.4-mini-code-eval-direct-fix`
  - `~/mini-benchmark/runs/humaneval-b6-20260324-1619/claude-opus-4.6-plan-code`
- The repo-side EvalPlus integration has been updated to match the installed EvalPlus output convention.
