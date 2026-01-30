# Track B 파이프라인 A~Z 검증 및 최종 분석 보고서

**작성일**: 2026-01-30  
**검증 대상 run**: run_20260130_232106 (및 동일 로직의 최신 run)  
**목적**: 단계별 로직 정합성, 통합·통계적 논리, 산출물 해석, 효용성·당위성 평가

---

## 1. 파이프라인 단계별 로직 검증

### 1.1 아티팩트 로드 (Step1/2/3)

| 단계 | 로직 | 검증 결과 |
|------|------|-----------|
| Step1 | `Step1Loader` → `get_consolidated_test_data()`: 테스트 200 wafer, `yield_true`, `riskscore` 등 | ✅ test 200장 로드, 동일 소스·동일 테스트 세트 유지 |
| Step2/3 | Proxy(WM-811K, Carinthia) 로드; Core 결론에 미사용 | ✅ 실패 시에도 Core는 Step1만 사용하도록 정책 적용 |

### 1.2 High-risk 정의 (핵심 일관성)

- **정의**: `define_high_risk_bottom_quantile(df, yield_col='yield_true', quantile=0.20)` → 하위 20%, **k = floor(0.2 × N)** 고정.
- **실행 결과**: N=200 → k=40, `actual_rate=0.2`, `high_risk_definition.json`에 기록.
- **전파 경로**:
  1. `_define_and_save_high_risk(test_df)` → `high_risk_mask` (길이 200, True 40개)
  2. `run_baselines(..., high_risk_mask)` → Random/Rule-based 모두 **동일 mask**로 TP/FN 계산
  3. `run_agent` → `framework_results_df['is_high_risk']` = 동일 mask
  4. `run_validation` → `StatisticalValidator.run_all_tests(..., high_risk_mask=high_risk_mask.values)` → **threshold 미사용, mask만 사용**

**검증**: 베이스라인·프레임워크·통계 검정이 **동일한 high-risk 정의(k=40)**를 사용. `high_risk_threshold`는 Legacy fallback이며, pipeline은 항상 `high_risk_mask`를 전달하므로 **논리적 일관성 유지** ✅

### 1.3 베이스라인 (Random / Rule-based)

- **Random**: 10% 고정 비율로 **무작위** 선택. `_run_baseline_with_high_risk_mask`에서 `is_high_risk`로 TP/FN/recall 계산.
- **Rule-based**: `riskscore` 상위 10% 선택. 동일 mask로 메트릭 계산.
- **검증**: `framework_results.csv`에서 random TP=2, rulebased TP=5, framework TP=6; `selected_count=20`, `selection_rate=0.1` 일치. ✅

### 1.4 Agent (Optimizer + Scheduler)

- **Optimizer**: **Validation set만** 사용 (`train_df`에서 tau 탐색). `test_set_used_for_optimization: false` 명시.
- **Scheduler**: 테스트 200장에 `target_selection_rate=0.10` 적용 → 상위 20명 선별. 예산 제약 하에 동일 20명 선택.
- **검증**: 테스트 세트로 튜닝하지 않음 → **test leakage 없음** ✅

### 1.5 통계 검증 (StatisticalValidator)

- **입력**: `random_df`, `framework_df` 각각 `is_high_risk` 보유 (동일 mask).
- **Chi-square**: 2×2 분할표 (baseline TP/FN, framework TP/FN). high_risk_mask 기준 TP/FN 계산 → **정의 일치** ✅
- **Bootstrap recall**: `baseline_selected`, `framework_selected`, `high_risk_mask`로 per-wafer 리샘플링 → recall 차이의 95% CI. ✅
- **Bootstrap cost**: per-wafer 비용 벡터 리샘플링 → 비용 차이 CI; **delta_cost_pct_ci**로 %만 보고. ✅
- **T-test**: 선택된 웨이퍼의 yield 비교 (exploratory). ✅
- **McNemar**: `(selected == high_risk_mask)` 일치 여부 — “선택 = GT” 일치도 (exploratory). ✅

### 1.6 Primary vs Exploratory 구분

- **Primary (결론 허용)**: (1) high-risk recall @ selection_rate=10%, (2) normalized cost reduction % (또는 cost per catch). Bootstrap CI만 결론에 사용.
- **Exploratory (결론 강조 금지)**: t-test, chi-square, McNemar. 보고서에 “exploratory, primary 결론은 recall/cost CI만” 명시됨. ✅

---

## 2. 통합 과정에서의 논리·통계 검증

### 2.1 High-risk 일관성

- **한 번 정의된 mask**가 baselines → agent → validation까지 동일 참조로 전달됨.
- **comparison 테이블**: `high_risk_count=40`이 random/rulebased/framework 모두 동일. `verify_outputs`의 high_risk_count 일치 검사 통과. ✅

### 2.2 Bootstrap CI 해석

- **Recall CI [0, 0.2195]**: 0을 포함 → “개선 단정 금지”, “signal (불확실성 존재)”로만 서술. ✅
- **Cost CI (%)** : delta_cost_pct_ci ≈ [-90.9, 47.4]%. 0 포함 → 비용 절감 단정 금지. ✅
- **절대 금액 CI**: Core/보고서에 저장·표기하지 않음 (정책 준수). ✅

### 2.3 Dominance 정의

- **dominance_flag**: 동일 r에서 (recall_fw ≥ recall_baseline) & (cost_per_catch_fw ≤ cost_per_catch_baseline) → Recall-dominance.
- **dominance_type**: `recall_dominance` (cost-dominance 아님 명시). ✅
- 현재 run: framework가 모든 r에서 recall 0.15 > random 0.05, cost_per_catch 더 낮음 → 6개 r 모두 recall_dominance. ✅

### 2.4 잠재적 논리 이슈 및 대응

| 이슈 | 검증 | 대응 |
|------|------|------|
| Statistical validator의 high_risk_threshold | pipeline이 항상 high_risk_mask 전달 → threshold 미사용 | ✅ 일관됨 |
| McNemar 해석 | “선택=GT” 일치도; recall@10%와 다른 질문 | Exploratory로만 사용, 결론에서 제외 ✅ |
| Chi-square 표본 크기 | 2 vs 6 (작은 셀) → p=0.26 | Primary가 아니며, CI로 결론 도출 ✅ |

---

## 3. 결과물 요약 및 파이프라인 효용성

### 3.1 최신 run 수치 (run_20260130_232106)

| 지표 | Random | Rule-based | Framework |
|------|--------|------------|-----------|
| selected_count | 20 | 20 | 20 |
| selection_rate | 0.1 | 0.1 | 0.1 |
| true_positive | 2 | 5 | 6 |
| high_risk_recall | 0.05 (5%) | 0.125 (12.5%) | 0.15 (15%) |
| high_risk_count (GT) | 40 | 40 | 40 |
| total_cost (normalized) | 3000 | 3000 | 3000 |

- **Primary**: Recall @ 10%에서 Framework(15%) > Random(5%). Rule-based(12.5%)는 그 중간.
- **비용**: 동일 예산·동일 선택 수 → total_cost 동일; 비용 절감 % = 0. r-sweep에서 normalized cost per catch는 Framework가 더 낮음 (TP가 더 많으므로).

### 3.2 “기존 방식보다 효용성이 높은가?”

- **Random 대비**: Framework가 동일 10% 선택으로 **high-risk recall 5% → 15%** (관측치 기준). Bootstrap recall CI가 [0, 0.22]로 **0을 포함**하므로, **통계적으로 “효용이 확실히 높다”고 단정할 수 없음** → “signal (불확실성 존재)”로만 해석. ✅
- **Rule-based 대비**: Framework recall 15% > 12.5%. 표본 수가 작아 통계적 유의성은 exploratory 검정에 맡기고, primary는 CI로만 서술하는 현재 정책과 부합. ✅
- **정리**: “효용이 높게 나왔다”는 것은 **관측치 수준**(recall 15% > 5%)에서만 말할 수 있고, **당위성(통계적 유의성)**은 **Bootstrap recall CI가 0을 포함**하므로 **단정되지 않음**. 보고서와 FINAL_VALIDATION에서 이를 구분해 서술함. ✅

---

## 4. 당위성 (통계적·방법론적 정당성)

### 4.1 당위성 있음

- **동일 테스트 세트**: 200 wafer 동일, high-risk 정의 고정(k=40). ✅
- **Test leakage 없음**: Optimizer/validation은 train/validation만 사용. ✅
- **Primary endpoints 2개만 결론**: recall @ 10%, normalized cost (%). 나머지는 exploratory. ✅
- **CI 해석**: CI에 0이 포함되면 개선/악화 단정 금지. ✅
- **비용**: 절대 금액 미사용, 정규화/비율만 사용. ✅

### 4.2 한계 (당위성 경계)

- **표본 수**: N=200, k=40 → recall CI 폭이 넓음 ([0, 0.22]). “효용이 확실히 높다”고 하기엔 불확실성 존재. ✅ (문서에 한계로 명시)
- **Lot leakage**: Lot 단위 분할 미실시 → 결과는 “동일 조건 내 운영 성능” 해석. holdout lots / GroupKFold는 향후 과제로 명시. ✅
- **Proxy FAILED**: Step2/3는 Appendix만, Core 결론에 Step2/3/SEM 수치 미사용. ✅

---

## 5. 최종 검증 체크리스트

| 항목 | 상태 |
|------|------|
| High-risk 정의 일관성 (k=40, mask 전역 사용) | ✅ |
| Selection rate 10% 고정 | ✅ |
| Test set 미사용 (optimizer/validation) | ✅ |
| Bootstrap recall/cost CI 사용 (cost는 %만) | ✅ |
| CI 0 포함 시 단정 금지 서술 | ✅ |
| Dominance 정의 (recall_dominance) 명시 | ✅ |
| Primary 2개만 결론, exploratory 구분 | ✅ |
| Core에 proxy/절대비용 미포함 | ✅ |
| verify_outputs + adversarial 통과 | ✅ |
| FINAL_VALIDATION verdict (READY_WITH_LIMITATIONS) | ✅ |

---

## 6. 결론

- **단계별 로직**: 아티팩트 로드 → high-risk 정의 → 베이스라인 → Agent → 통계 검증 → 보고서까지, high_risk_mask와 k=40이 일관되게 사용되며, test leakage 없음.
- **통합·통계**: Bootstrap CI 기반 primary 해석, exploratory 검정 역할 분리, dominance 정의 및 비용 % 정책 준수.
- **결과물**: Framework가 Random 대비 관측 recall 상승(5% → 15%)을 보이나, **Bootstrap recall CI가 0을 포함**하므로 “효용이 확실히 높다”는 **당위성은 부여되지 않음**; “signal (불확실성 존재)”로만 해석하는 것이 적절하며, 현재 파이프라인과 보고서가 이를 반영함.
- **최종 판정**: READY_WITH_LIMITATIONS — 제한사항(표본 수, lot split 미실시, proxy 실패)을 명시한 상태에서 논문용 증거 패키지로 사용 가능.
