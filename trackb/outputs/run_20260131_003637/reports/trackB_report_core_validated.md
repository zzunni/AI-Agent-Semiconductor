# Track B Core (Validated) Report
## Step1 Only — 동일 소스 + yield_true GT 매칭

생성 시각: 2026-01-31 00:36:37

본 보고서의 모든 수치·표·결론은 이 실행(run_20260131_003637)의 산출물만 사용합니다. 다른 run 또는 외부 데이터를 사용하지 않습니다.

---

## Abstract (Step1만)

예산 제약 하에서 200개 테스트 웨이퍼에 대해 high-risk(yield_true 하위 20%, k=40) 탐지율을 비교하였다. Random(10%), Rule-based(10%), Framework(Agent) 세 방법을 동일 테스트 세트로 평가하였다. Primary endpoints: high-risk recall @ selection_rate=10%, normalized cost per catch. 본 Core 결론은 Step1(동일 소스 + yield_true GT)만 사용한다.

---

## Problem & Decision Setting

- **연구 목적**: 예산 제약 하에 고위험 웨이퍼 조기 선별 및 추가 계측·후속검사·리워크 의사결정 최적화.
- **운영 정책**: selection_rate=10% 고정; 동일 소스(same fab) test set만 사용; 절대 비용 금액 미사용(정규화/비율만).
- **질문**: "하위 20% high-risk가 다음 단계로 넘어가냐?" — 운영은 risk_score top-k% 선별, 평가는 yield_true 라벨로 recall 측정.

---

## Experimental Design (공정성)

- **동일 테스트**: 200 wafer 동일 테스트 세트에 Random / Rule-based / Framework 동일 조건 적용.
- **Baseline 동일 조건**: 동일 selection_rate(10%), 동일 high-risk 정의(k=40).
- **Test leakage 금지**: threshold/optimizer는 validation set만 사용; test set은 최종 평가에만 사용.

---

## System Overview (Step1) — 입력/출력/산출물

- **입력**: 동일 소스 테스트 200 wafer. 필수 컬럼: yield_true(평가 라벨), risk_score(운영 선별 점수). Step1 아티팩트에서 로드.
- **처리**: Stage0/1/2A risk_score → 운영 선별(top-k%) → GT high-risk(yield 하위 20%) 검출 평가. Gating 정책은 산출물(decision_trace 등)에 반영.
- **출력**: recall@selection_rate, normalized cost per catch, bootstrap 95% CI. PASS/FAIL은 Step1에서만 결정.
- **산출물**: validation/framework_results.csv, validation/bootstrap_primary_ci.json, validation/sensitivity_cost_ratio.csv.

---

## Data & Label Definition

- **Evaluation label (GT_high_risk)**: yield_true bottom 20% with k fixed on test=200 (k=40)
- **Operational selection**: top selection_rate by risk_score (default 10%)
- Test size: 200, k: 40

---

## Methods (Stage0–2A)

- **Stage0**: Inline risk score from process/equipment features (XGBoost). Output: risk_stage0, riskscore. Gating: tau0.
- **Stage1**: Refined risk with additional features (XGBoost). Gating: tau1.
- **Stage2A**: Combined multi-stage risk (XGBoost). Output: combined riskscore. Gating: tau2a. (Core 범위: Stage0–2A만)
- **Decision policy (top-k selection)**: selection_rate=10% 고정. risk_score 상위 10%만 다음 단계(추가 계측)로 선별. 운영 답은 pred_risk_score 기반 top-k%만 사용.
- 학습/추론: Step1 아티팩트에서 로드. Validation set에서만 임계치 탐색; test set 미사용.

---

## Primary Results (selection_rate=10% 고정)

| method | total_wafers | high_risk_count | low_risk_count | selected_count | selection_rate | true_positive | false_negative | false_positive |
|---|---|---|---|---|---|---|---|---|
| random | 200 | 40 | 160 | 20 | 0.1 | 2 | 38 | 18 |
| rulebased | 200 | 40 | 160 | 20 | 0.1 | 5 | 35 | 15 |
| framework | 200 | 40 | 160 | 20 | 0.1 | 6 | 34 | 14 |

### Primary Endpoints + Bootstrap 95% CI

- Recall (framework): 0.15 (Δ CI: [0.0, 0.21951219512195122])
- Cost reduction (%): 0.0 (Δ % CI: [-90.9090909090909, 47.368421052631575])

### Effect size (operational meaning)

- Absolute gain in catches: TP_framework − TP_random = **4** (추가 탐지 고위험 웨이퍼 수).
- Miss reduction: FN_random − FN_framework = **4** (누락 감소).
- Interpretation (관측치 기준): selection_rate=10%에서 framework는 random 대비 고위험 웨이퍼를 추가로 4장 더 탐지(TP 증가), 누락을 4장 감소(FN 감소)시켰다. 통계적 확정이 아님; CI가 0을 포함하면 signal로만 해석.


### Random baseline variability (multi-seed)

- Random baseline을 50 seed로 반복 시 recall 분포: 평균 0.102 ± 0.045, 5/50/95 분위: 0.036 / 0.100 / 0.164.
- Framework recall (0.15)은 random p95(0.164) 대비 상대적 위치로 해석 가능. 단정 금지; 'suggests' 또는 'consistent with' 수준.


---
## Cost Model (정규화 원칙)

- 절대 금액(달러) 사용 금지. inline_cost_unit=1, 후속검사 단위=r (r sweep).
- r ∈ {1,2,3,5,7,10} 그리드. normalized_cost, cost_per_catch, dominance_flag. dominance_type=recall_dominance: 동일 normalized_cost에서 recall이 baseline보다 큼(cost-dominance 아님).

| r | recall_high_risk | normalized_cost | cost_per_catch | dominance_flag | dominance_type | method |
|---|---|---|---|---|---|---|
| 1 | 0.05 | 20.0 | 10.0 | nan | nan | random |
| 1 | 0.125 | 20.0 | 4.0 | nan | nan | rulebased |
| 1 | 0.15 | 20.0 | 3.333333333333 | True | recall_dominan | framework |
| 2 | 0.05 | 20.0 | 10.0 | nan | nan | random |
| 2 | 0.125 | 20.0 | 4.0 | nan | nan | rulebased |
| 2 | 0.15 | 20.0 | 3.333333333333 | True | recall_dominan | framework |
| 3 | 0.05 | 20.0 | 10.0 | nan | nan | random |
| 3 | 0.125 | 20.0 | 4.0 | nan | nan | rulebased |
| 3 | 0.15 | 20.0 | 3.333333333333 | True | recall_dominan | framework |
| 5 | 0.05 | 20.0 | 10.0 | nan | nan | random |
| 5 | 0.125 | 20.0 | 4.0 | nan | nan | rulebased |
| 5 | 0.15 | 20.0 | 3.333333333333 | True | recall_dominan | framework |


---
## Exploratory Stats (결론에서 강조 금지)

- t_test_yields: p=0.0006242200374749914
- chi_square_detection: p=0.26355247728296954
- bootstrap_cost: p=0.5362
- mcnemar: p=0.2561449666035265

- 위 검정은 exploratory(hypothesis-generating)이며, primary 결론은 recall CI 및 cost CI만 사용.

---
## Limitations

- **Group split 미실시**: Lot leakage 가능성 완전 배제 불가. 결과는 동일 조건 내 운영 성능으로 해석.

**Lot leakage risk diagnostics (no retraining):**

| 항목 | 값 |
|------|-----|
| n_test_wafers | 200 |
| n_test_lots | 49 |
| test_lot_size (min/median/max) | 1 / 4.0 / 8 |
| high_risk_rate_by_lot (min/median/max) | 0.0 / 0.2 / 0.6666666666666666 |

- 진단 근거: `baselines/random_results.csv` (lot_id, yield_true, is_high_risk). train overlap은 Step1 train 아티팩트 기반.
- **표본수**: N=200 고정; CI 해석 시 표본 크기 한계 인지.
- **CI 해석**: Recall CI가 0을 포함하면 개선 단정 금지; signal(불확실성 존재)로 표현.
- **논문 후속 검증**: holdout lots, GroupKFold 등 lot 단위 분할 실험 권장.

---
## Reproducibility + Evidence Index

- Run ID: run_20260131_003637
- Manifest: `_manifest.json` (경로·SHA256·row_count·columns)
- 상세 IO trace: `reports/PAPER_IO_TRACE.md`
- 설정: trackb/configs/trackb_config.json
