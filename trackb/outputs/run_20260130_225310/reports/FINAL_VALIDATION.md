# Final Comprehensive Validation
## 궁극 목표 종합 검증 — 논문 제출 준비 여부

**Run ID**: 20260130_225310  
**Generated**: 2026-01-30T22:53:11.900408

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
- **개선 여부**: True
- **근거 파일**: `validation/bootstrap_primary_ci.json`

---

## Q2) 비용 절감 또는 동일 비용에서 성능 개선?

- **Normalized cost reduction %**: 0
- **r-sweep에서 framework dominance 구간 수**: 6
- **근거 파일**: `validation/sensitivity_cost_ratio.csv`, `sensitivity_cost_ratio.json`

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
- **Core 문서 proxy/$ 검사**: True
- **검증기**: `verify_outputs.py`가 Core/Proxy 분리 및 $ 금지 정책 강제

---

## Q6) lot leakage 방지/일반화

- **Group split in core**: False
- **TODO**: lot 기준 그룹 분할 실험이 없으면, "동일 lot 내 train/test 분리 또는 holdout lot 평가"를 추가 실험으로 명시. `reports/trackB_report_core_validated.md` 또는 한계 섹션에 기록.

---

## Primary 2개 + CI 요약

| Endpoint | Baseline | Framework | Δ (95% CI) |
|----------|----------|-----------|------------|
| Recall @ selection_rate=10% | 0.05 | 0.15 | [0.0, 0.21951219512195122] |
| Normalized cost reduction % | — | — | 0% |

---

## 제한사항 및 다음 실험

- 논문 결론은 Step1 Core만 사용. Step2/Step3는 Appendix(plausibility only).
- 비용은 절대 금액 금지; 정규화/비율만 사용.
- Lot/group split 실험이 있으면 Core에 포함; 없으면 한계에 "동일 wafer 다단계 측정 데이터 및 lot holdout 평가"를 향후 과제로 명시.

---

## 근거 파일 인덱스

- `validation/bootstrap_primary_ci.json` — Primary recall/cost CI
- `validation/framework_results.csv` — 비교 테이블
- `validation/sensitivity_cost_ratio.csv` — r-sweep, dominance
- `validation/high_risk_definition.json` — GT 정의
- `reports/paper_bundle.json` — evidence_index, policies, results
- `_manifest.json` — 전체 입출력 해시
