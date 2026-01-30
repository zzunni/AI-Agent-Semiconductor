# Track B Core (Validated) Report
## Step1 Only — 동일 소스 + yield_true GT 매칭

생성 시각: 2026-01-30 22:53:11

본 보고서의 모든 수치·표·결론은 이 실행(run_20260130_225310)의 산출물만 사용합니다. 다른 run 또는 외부 데이터를 사용하지 않습니다.

---

## Abstract (Step1만)

예산 제약 하에서 200개 테스트 웨이퍼에 대해 high-risk(yield_true 하위 20%, k=40) 탐지율을 비교하였다. Random(10%), Rule-based(10%), Framework(Agent) 세 방법을 동일 테스트 세트로 평가하였다. Primary endpoints: high-risk recall @ selection_rate=10%, normalized cost per catch. 본 Core 결론은 Step1(동일 소스 + yield_true GT)만 사용한다.

---

## Problem & Decision Setting

- **목표**: 제한된 검사 예산으로 고위험 웨이퍼를 최대한 탐지.
- **제약**: selection_rate=10% 고정, 동일 소스(same fab) test set만 사용.
- **High-risk 목표**: 평가 라벨은 yield_true 하위 20% (k=40/200 고정). 운영 선별은 risk_score 상위 selection_rate.

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
- Cost reduction (%): 0.0 (Δ CI: [-1800.0, 1800.0])

---
## Cost Model (정규화 원칙)

- 절대 금액(달러) 사용 금지. inline_cost_unit=1, 후속검사 단위=r (r sweep).
- r ∈ {1,2,3,5,7,10} 그리드. normalized_cost, cost_per_catch, dominance_flag.

| r | recall_high_risk | normalized_cost | cost_per_catch | dominance_flag | method |
|---|---|---|---|---|---|
| 1 | 0.05 | 20.0 | 10.0 | nan | random |
| 1 | 0.125 | 20.0 | 4.0 | nan | rulebased |
| 1 | 0.15 | 20.0 | 3.333333333333 | True | framework |
| 2 | 0.05 | 20.0 | 10.0 | nan | random |
| 2 | 0.125 | 20.0 | 4.0 | nan | rulebased |
| 2 | 0.15 | 20.0 | 3.333333333333 | True | framework |
| 3 | 0.05 | 20.0 | 10.0 | nan | random |
| 3 | 0.125 | 20.0 | 4.0 | nan | rulebased |
| 3 | 0.15 | 20.0 | 3.333333333333 | True | framework |
| 5 | 0.05 | 20.0 | 10.0 | nan | random |
| 5 | 0.125 | 20.0 | 4.0 | nan | rulebased |
| 5 | 0.15 | 20.0 | 3.333333333333 | True | framework |


---
## Exploratory Stats (결론에서 강조 금지)

- t_test_yields: p=0.0006242200374749914
- chi_square_detection: p=0.26355247728296954
- bootstrap_cost: p=0.5362
- mcnemar: p=0.2561449666035265

- 위 검정은 exploratory(hypothesis-generating)이며, primary 결론은 recall CI 및 cost CI만 사용.

---
## Reproducibility + Evidence Index

- Run ID: run_20260130_225310
- Manifest: `_manifest.json` (경로·SHA256·row_count·columns)
- 설정: trackb/configs/trackb_config.json
