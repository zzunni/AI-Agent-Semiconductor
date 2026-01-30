# Track B 검증 보고서
## AI 기반 모듈러 프레임워크 - 과학적 검증

생성 시각: 2026-01-30 20:04:28


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## 요약
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


### 주요 기여 (Ground Truth 검증)
- 데이터: 200개 실제 웨이퍼 (yield_true 있음)
- 방법: 자율 최적화 Agent
- Baseline: Random (10%) + Rule-based (top 10%)




**방법별 비교**

| method    |   total_wafers |   high_risk_count |   low_risk_count |   selected_count | selection_rate   |   true_positive |   false_negative |   false_positive |   true_negative | high_risk_recall   | high_risk_precision   | high_risk_f1   |   specificity | false_positive_rate   |   missed_high_risk |   n_inline |   n_sem |   total_inspections | inline_cost   | sem_cost   | total_cost   | cost_per_catch   | cost_per_inspection   | cost_inline_unit   | cost_sem_unit   |   n_selected | inline_rate   |   n_high_risk | delta_cost   | delta_cost_pct   | delta_recall   |
|:----------|---------------:|------------------:|-----------------:|-----------------:|:-----------------|----------------:|-----------------:|-----------------:|----------------:|:-------------------|:----------------------|:---------------|--------------:|:----------------------|-------------------:|-----------:|--------:|--------------------:|:--------------|:-----------|:-------------|:-----------------|:----------------------|:-------------------|:----------------|-------------:|:--------------|--------------:|:-------------|:-----------------|:---------------|
| random    |            200 |                40 |              160 |               20 | 10.0%            |               2 |               38 |               18 |             142 | 5.0%               | 10.0%                 | 6.7%           |       0.8875  | 11.2%                 |                 38 |         20 |       0 |                  20 | $3,000        | $0         | $3,000       | $1,500           | $150                  | $150               | $500            |           20 | 10.0%         |            40 | $0           | +0.0%            | 0.0%           |
| rulebased |            200 |                40 |              160 |               20 | 10.0%            |               5 |               35 |               15 |             145 | 12.5%              | 25.0%                 | 16.7%          |       0.90625 | 9.4%                  |                 35 |         20 |       0 |                  20 | $3,000        | $0         | $3,000       | $600             | $150                  | $150               | $500            |           20 | 10.0%         |            40 | $0           | +0.0%            | 7.5%           |
| framework |            200 |                40 |              160 |               20 | 10.0%            |               6 |               34 |               14 |             146 | 15.0%              | 30.0%                 | 20.0%          |       0.9125  | 8.8%                  |                 34 |         20 |       0 |                  20 | $3,000        | $0         | $3,000       | $500             | $150                  | $150               | $500            |          nan |               |           nan | $0           | +0.0%            | 10.0%          |


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
- **Bootstrap (비용 절감 95% CI)**: [-1800.0, 1800.0]
  - Observed diff: 0.0
  - n_bootstrap: 10000
- **McNemar**: statistic=1.289, p=0.2561 (❌ 비유의)

**High-risk count**: 40 (하위 20% 정의 기준)

### 전체 결론

일부 검정에서 유의한 차이 확인: t_test_yields

- 총 검정 수: 4
- 유의한 검정 수: 1
- 유의한 검정: t_test_yields


### 현재 한계

1. **데이터 통합**: 다른 출처의 데이터, proxy 기반 통합
2. **클래스 불균형**: SEM 데이터 87% Particle
3. **Pattern 추정**: 도메인 지식 기반, 실제 관측값 없음

### 향후 개선

- 동일 웨이퍼 다단계 측정 데이터 수집
- 희귀 결함 SEM 데이터 확장
- 엔지니어 피드백 기반 온라인 정책 업데이트

### 재현성

- **Manifest**: [../_manifest.json](../_manifest.json)
- **설정 파일**: [../../configs/trackb_config.json](../../configs/trackb_config.json)

**재현 단계**:
```bash
cd trackb/
python scripts/trackb_run.py --mode from_artifacts
```


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
보고서 끝
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
