# PIPELINE_IO_TRACE.md
Track B 파이프라인 입출력 추적

Run ID: 20260131_003637
Timestamp: 2026-01-31T00:36:37.294818

## Stage 1: Artifact Loading
- Input: `../../data/step1`
- Output: test_df (200 rows)

## Stage 2: Baseline Execution
- Input: test_df (200 rows)
- Output: `baselines/random_results.csv`, `baselines/rulebased_results.csv`

## Stage 3: Threshold Optimizer
- Input: validation_df (210 rows)
- Output: `agent/autotune_summary.json`, `agent/autotune_history.csv`
- Key params: budget=3000, target=recall

## Stage 4: Budget Scheduler
- Input: test_df (200 rows), optimized thresholds
- Output: `agent/scheduler_log.csv`

## Stage 5: Statistical Validation
- Input: baseline results, framework results
- Output: `validation/statistical_tests.json`, `validation/proxy_validation.json`


## Key Parameters
- Random seed: 42
- High-risk threshold: 0.6
- Budget (units): 3,000
- Alpha: 0.05
