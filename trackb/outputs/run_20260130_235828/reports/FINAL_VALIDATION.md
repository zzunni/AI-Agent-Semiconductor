# Final Comprehensive Validation
## 궁극 목표 종합 검증 — 논문 제출 준비 여부

**Current run only**: 본 문서의 모든 수치·판정은 이 실행(run_20260130_235828)의 산출물만 사용합니다.

**Run ID**: 20260130_235828  
**Generated**: 2026-01-30T23:58:29.044440

---

## 최종 판정

**READY_WITH_LIMITATIONS**

Proxy validation FAILED; Core separated and policy enforced

---

## 연구 목적 (시스템 목표)

반도체 웨이퍼 공정에서 제한된 계측/SEM 예산과 처리량 제약 하에, 저수율(high-risk) 웨이퍼를 조기에 선별하고, 추가 계측/SEM/리워크/스크랩 의사결정을 단계적으로 최적화하여 (1) high-risk 검출 리콜을 높이고, (2) 동일 리콜에서 비용을 줄이거나 (3) 동일 예산에서 성능을 높이며, 모든 판단이 근거 파일(해시)+재현 절차로 추적 가능한 의사결정 시스템을 만드는 것이 목표이다.

- **TrackA**: 운영/데모/의사결정 UI 레이어 (Stage 결과 → 워크플로우/경보→SEM→조치).
- **TrackB**: 과학적 검증/재현성/증거 추적. 논문 핵심 수치는 Step1 Validated Core만 사용.

---

## Q1) 고위험 웨이퍼를 더 잘 잡는가? (Recall@10% 개선)

- **Baseline recall**: 0.05
- **Framework recall**: 0.15
- **ΔRecall (95% CI)**: [0.0, 0.21951219512195122]
- **해석**: signal (불확실성 존재) (CI가 0을 포함하면 단정하지 않음)
- **근거 파일**: `validation/bootstrap_primary_ci.json`


---

## Q2) 비용 절감 또는 동일 비용에서 성능 개선?

- **Dominance 정의**: dominance_flag=True는 **Recall-dominance** — 동일 normalized_cost에서 framework의 recall이 baseline보다 큼. cost-dominance가 아님.
- **Normalized cost reduction %**: 0 [-90.9090909090909, 47.368421052631575]%
- **r-sweep에서 framework recall-dominance 구간 수**: 6
- **근거 파일**: `validation/sensitivity_cost_ratio.csv` (dominance_type ∈ {recall_dominance, cost_dominance, none})

---

## Q3) 의사결정 파이프라인 정책 고정성

- **selection_rate**: 10% 고정 (산출물/설정과 일치)
- **GT high-risk**: yield_true 하위 20%, k=40, N=200 고정
- **근거 파일**: `validation/high_risk_definition.json`, `validation/framework_results.csv`

---

## Q4) 근거 파일로 재현 가능?

- **Manifest**: `_manifest.json` (path, sha256, rows, cols)
- **Evidence index**: `reports/paper_bundle.json` → evidence_index
- **재현 명령**: `cd trackb/scripts && python trackb_run.py --mode from_artifacts`

---

## Q5) proxy FAILED 시 Core에 proxy 미혼합?

- **Proxy status**: True
- **Core 문서 proxy/절대비용 검사**: True
- **검증기**: `verify_outputs.py`가 Core/Proxy 분리 및 절대비용 금지 정책 강제

---

## Q6) lot leakage 방지/일반화

- **Group split in core**: False
- **해석**: Lot leakage 가능성은 완전 배제할 수 없음. 결과는 동일 조건 내 운영 성능으로 해석함.
- **논문 후속 검증**: holdout lots, GroupKFold 등 lot 단위 분할 실험을 명시할 것.
- **TODO**: "동일 lot 내 train/test 분리 또는 holdout lot 평가"를 한계/향후 과제로 명시.

---

## Primary 2개 + CI 요약 (비용은 %만 표기)

| Endpoint | Baseline | Framework | Δ (95% CI) |
|----------|----------|-----------|------------|
| Recall @ selection_rate=10% | 0.05 | 0.15 | [0.0, 0.21951219512195122] |
| Normalized cost reduction % | — | — | 0% [-90.9090909090909, 47.368421052631575]% |

---

## 제한사항 및 다음 실험

- 논문 결론은 Step1 Core만 사용. Step2/Step3는 Appendix(plausibility only).
- 비용은 절대 금액 금지; 정규화/비율만 사용.
- Lot/group split 미실시: lot leakage 완전 배제 불가, 동일 조건 내 성능으로 해석. 향후 holdout lots / GroupKFold 명시.

---

## 근거 파일 인덱스

- `validation/bootstrap_primary_ci.json` — Primary recall/cost CI (cost는 % CI만)
- `validation/framework_results.csv` — 비교 테이블
- `validation/sensitivity_cost_ratio.csv` — r-sweep, dominance_type
- `validation/high_risk_definition.json` — GT 정의
- `reports/paper_bundle.json` — evidence_index, policies, results
- `_manifest.json` — 전체 입출력 해시
