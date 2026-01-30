# Track B 검증 보고서
## AI 기반 모듈러 프레임워크 - 과학적 검증

생성 시각: 2026-01-31 00:10:58


**데이터 출처**: 본 보고서의 모든 수치·표·결론은 **이 실행(run_20260131_001057)** 의 산출물만 사용합니다. 다른 run 또는 외부 데이터를 사용하지 않습니다.


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## 요약
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


### 주요 기여 (Ground Truth 검증)
- 데이터: 200개 실제 웨이퍼 (yield_true 있음)
- 방법: 자율 최적화 Agent
- Baseline: Random (10%) + Rule-based (top 10%)



**Primary conclusions use only**: Recall@10% and normalized cost reduction (%) with bootstrap 95% CI.
**All other tests** (t-test, chi-square, McNemar) are exploratory and not used for final claims.


Cost values are reported in **normalized units (unitless)**. No currency or absolute money is used.

Numbers like 3000/150/500 in tables are **normalized units (not currency)**.



**방법별 비교**

| method    |   total_wafers |   high_risk_count |   low_risk_count |   selected_count | selection_rate   |   true_positive |   false_negative |   false_positive |   true_negative | high_risk_recall   | high_risk_precision   | high_risk_f1   |   specificity | false_positive_rate   |   missed_high_risk |   n_inline |   n_followup |   total_inspections | inline_cost_norm   |   followup_cost_norm | total_cost_norm   | cost_per_catch_norm   |   cost_per_inspection |   cost_unit_inline_norm |   followup_unit_norm |   n_selected | inline_rate   |   n_high_risk |   delta_cost | delta_cost_pct   | delta_recall   |
|:----------|---------------:|------------------:|-----------------:|-----------------:|:-----------------|----------------:|-----------------:|-----------------:|----------------:|:-------------------|:----------------------|:---------------|--------------:|:----------------------|-------------------:|-----------:|-------------:|--------------------:|:-------------------|---------------------:|:------------------|:----------------------|----------------------:|------------------------:|---------------------:|-------------:|:--------------|--------------:|-------------:|:-----------------|:---------------|
| random    |            200 |                40 |              160 |               20 | 10.0%            |               2 |               38 |               18 |             142 | 5.0%               | 10.0%                 | 6.7%           |       0.8875  | 11.2%                 |                 38 |         20 |            0 |                  20 | 3,000              |                    0 | 3,000             | 1,500                 |                   150 |                     150 |                  500 |           20 | 10.0%         |            40 |            0 | +0.0%            | 0.0%           |
| rulebased |            200 |                40 |              160 |               20 | 10.0%            |               5 |               35 |               15 |             145 | 12.5%              | 25.0%                 | 16.7%          |       0.90625 | 9.4%                  |                 35 |         20 |            0 |                  20 | 3,000              |                    0 | 3,000             | 600                   |                   150 |                     150 |                  500 |           20 | 10.0%         |            40 |            0 | +0.0%            | 7.5%           |
| framework |            200 |                40 |              160 |               20 | 10.0%            |               6 |               34 |               14 |             146 | 15.0%              | 30.0%                 | 20.0%          |       0.9125  | 8.8%                  |                 34 |         20 |            0 |                  20 | 3,000              |                    0 | 3,000             | 500                   |                   150 |                     150 |                  500 |          nan |               |           nan |            0 | +0.0%            | 10.0%          |


### 검증 상태

| 구성 요소 | 상태 | 설명 |
|-----------|------|------|
| Stage 0-2A (STEP 1) | ✅ | Ground truth 검증 (200개 테스트 웨이퍼) |
| Stage 2B (STEP 2) | ⚠️ | WM-811K 벤치마크에서 독립 검증 |
| Stage 3 (STEP 3) | ⚠️ | Carinthia 데이터셋에서 독립 검증 |
| 통합 (2B → 3) | ⚠️ | Proxy 기반 (plausibility-checked, 인과 증명 아님) |

**한계**: 다른 데이터 출처로 인해 동일 웨이퍼 검증 불가
**향후 과제**: 통합된 다단계 측정 데이터 수집


## 통계 검증 결과

### 검정 요약

- **T-test (yield 비교)**: t=3.730, p=<0.001 (✅ 유의)
  - 비교 집단: 선택된 웨이퍼의 yield_true 분포 (baseline vs framework)
  - Baseline mean: 0.4787, Framework mean: 0.3042
  - Sample sizes: n_baseline=20, n_framework=20
- **Chi-square (검출률)**: χ²=1.250, p=0.2636 (❌ 비유의)
  - Contingency table: Baseline [TP=2, FN=38], Framework [TP=6, FN=34]
- **Bootstrap (normalized cost reduction %, 95% CI)**: [-90.9%, 47.4%] (percentage only; no absolute money units)
  - n_bootstrap: 10000
- **McNemar**: statistic=1.289, p=0.2561 (❌ 비유의)

**High-risk count**: 40 (하위 20% 정의 기준)

### 전체 결론

일부 검정에서 유의한 차이 확인: t_test_yields

- 총 검정 수: 5
- 유의한 검정 수: 1
- 유의한 검정: t_test_yields


### 현재 한계

1. **데이터 통합**: 다른 출처의 데이터, proxy 기반 통합
2. **클래스 불균형**: 후속검사(Step2 proxy) 데이터 87% Particle
3. **Pattern 추정**: 도메인 지식 기반, 실제 관측값 없음
4. **Lot-level**: This evaluation reflects within-production-distribution performance under the current sampling scheme. Lot-level generalization requires additional holdout-lot validation.

### 향후 개선

- 동일 웨이퍼 다단계 측정 데이터 수집
- 희귀 결함 후속검사 데이터 확장
- 엔지니어 피드백 기반 온라인 정책 업데이트

### 증거 인덱스 (run_20260131_001057)

아래 파일에서 보고서 수치를 인용했습니다. 해시로 동일 실행 여부를 확인할 수 있습니다.

| 파일                           | 경로                                                                                                                           | SHA256                                                           |
|:-------------------------------|:-------------------------------------------------------------------------------------------------------------------------------|:-----------------------------------------------------------------|
| autotune_history.csv           | /Users/choeyejun/Documents/ai-agent-semiconductor/trackb/outputs/run_20260131_001057/agent/autotune_history.csv                | 024110cecb0595453ad02be241ecbe199da31d2259ff6f52d66fe5892d177ec2 |
| rulebased_results.csv          | /Users/choeyejun/Documents/ai-agent-semiconductor/trackb/outputs/run_20260131_001057/baselines/rulebased_results.csv           | 889caf46148c784d9ccfa33dda76afeb47d50cbc1f329ae4ca6bba77c457f364 |
| random_results.csv             | /Users/choeyejun/Documents/ai-agent-semiconductor/trackb/outputs/run_20260131_001057/baselines/random_results.csv              | d023382de8c0404e6766954cc56d5f296a994acb8d02d7eb823ed94fe54ca502 |
| comparison_table.csv           | /Users/choeyejun/Documents/ai-agent-semiconductor/trackb/outputs/run_20260131_001057/baselines/comparison_table.csv            | 36db375a2719c36af4144015cc1ad5351d656e041bcbe67ceeb7204cbb3da16b |
| sensitivity_cost_ratio.csv     | /Users/choeyejun/Documents/ai-agent-semiconductor/trackb/outputs/run_20260131_001057/validation/sensitivity_cost_ratio.csv     | 828e1dddcd0a47fc0ead4a6c8fd0b75c2f7d640969282afff9740e421af5a73d |
| stage_breakdown.csv            | /Users/choeyejun/Documents/ai-agent-semiconductor/trackb/outputs/run_20260131_001057/validation/stage_breakdown.csv            | a9448245e10619a4795dd78bac8a5dc22e93a7b5be2853dcf66cb727d544fa1c |
| random_seed_sweep.csv          | /Users/choeyejun/Documents/ai-agent-semiconductor/trackb/outputs/run_20260131_001057/validation/random_seed_sweep.csv          | f3c5734c29750dd8524c89a5ecaccb8688f43f023bd5bf3fe1ab88f352f176d4 |
| framework_results.csv          | /Users/choeyejun/Documents/ai-agent-semiconductor/trackb/outputs/run_20260131_001057/validation/framework_results.csv          | 16caeec8481f7c81a545973daa2b5680fd7d877061075917fbce10aeb2c26018 |
| autotune_summary.json          | /Users/choeyejun/Documents/ai-agent-semiconductor/trackb/outputs/run_20260131_001057/agent/autotune_summary.json               | d2911aeff153e789bb28928fe38f9327c582d22b2fa982d0d777a56683377d3b |
| statistical_tests.json         | /Users/choeyejun/Documents/ai-agent-semiconductor/trackb/outputs/run_20260131_001057/validation/statistical_tests.json         | f448e84adb6d4af710a51e78b7ebfcfc6a0988ccca863234e9010b0134075ac9 |
| high_risk_definition.json      | /Users/choeyejun/Documents/ai-agent-semiconductor/trackb/outputs/run_20260131_001057/validation/high_risk_definition.json      | a75409885625a8d316315c52a101a358b4af2932f01a906aba8caff6b16c5bc8 |
| lot_leakage_diagnostics.json   | /Users/choeyejun/Documents/ai-agent-semiconductor/trackb/outputs/run_20260131_001057/validation/lot_leakage_diagnostics.json   | 4f49fccdb8c3d50af55004e07551bbf87a29fdc88ba7b792e3f13cf9eed87553 |
| random_seed_sweep_summary.json | /Users/choeyejun/Documents/ai-agent-semiconductor/trackb/outputs/run_20260131_001057/validation/random_seed_sweep_summary.json | fab64529bdaf03e61bef108e7de08a35fc036c62370718efcc941d77f719e5e7 |
| proxy_validation.json          | /Users/choeyejun/Documents/ai-agent-semiconductor/trackb/outputs/run_20260131_001057/validation/proxy_validation.json          | 19951f0ed83c241a5cc8a054769a52db9711aac0e14b766284ae3a01d18eb261 |
| sensitivity_cost_ratio.json    | /Users/choeyejun/Documents/ai-agent-semiconductor/trackb/outputs/run_20260131_001057/validation/sensitivity_cost_ratio.json    | 46b7acb98118855f04289b07843e1d8fdae4322aac5eafd76af892857b0fae0a |
| bootstrap_primary_ci.json      | /Users/choeyejun/Documents/ai-agent-semiconductor/trackb/outputs/run_20260131_001057/validation/bootstrap_primary_ci.json      | bdcd93cdc0716273635d400b075e506abc092db0e2de0196e4857a1901b8b101 |

- **Manifest**: `/Users/choeyejun/Documents/ai-agent-semiconductor/trackb/outputs/run_20260131_001057/_manifest.json` (전체 입·출력 목록 및 해시)

### 재현성

- **실행 ID**: `run_20260131_001057`
- **Manifest**: [../_manifest.json](../_manifest.json)
- **설정**: [../../configs/trackb_config.json](../../configs/trackb_config.json)

**재현 단계**:
```bash
cd trackb/
python scripts/trackb_run.py --mode from_artifacts
```


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
보고서 끝
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
