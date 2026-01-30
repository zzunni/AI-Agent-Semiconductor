# Track B 파이프라인 세부 검증 요약 (run_20260131_001057)

## 1. 파이프라인 단계별 흐름

| 순서 | 단계 | 담당 | 의존성 |
|------|------|------|--------|
| 1 | compileall | run_full_e2e | trackb/ 전체 |
| 2 | static_check | run_full_e2e | report 관련 .py에서 `$` 금지 |
| 3 | trackb_run | run_full_e2e | config, step1/2/3 아티팩트 |
| 4 | verify_outputs | run_full_e2e | run_* 산출물 |
| 5 | run_adversarial_tests | run_full_e2e | Core 보고서 정책 반증 |

**trackb_run 내부 순서**:  
Pipeline.run() → **Lot leakage diagnostics** → **Random seed sweep** → Manifest → Master report → Paper bundle/reports → Final validation

## 2. 논리적 검증 포인트

- **High-risk 정의 일관성**: `high_risk_definition.json`의 k=40가 statistical_tests, framework_results, baselines에서 동일 사용.
- **Core/Appendix 분리**: Core에는 Step1(Validated)만; proxy/Step2/Step3/SEM/절대금액 없음. Appendix에 proxy만.
- **비용 표기**: 보고서 표 컬럼명 `_norm` 접미사(inline_cost_norm, total_cost_norm 등) + 표 위 문장 "Numbers like 3000/150/500 are normalized units (not currency)".
- **Limitations**: "lot_id 없음" 대신 "Lot-level generalization was not evaluated via holdout-lot/GroupKFold..." (else 분기). diagnostics_available이면 Lot leakage 표 + "진단 근거: ... (lot_id, ...)"로 Evidence Index와 일치.
- **FINAL_VALIDATION verdict**: NOT_READY이면 verify_outputs 실패; READY_WITH_LIMITATIONS 허용.

## 3. 이번 Run에서 확인된 산출물

- `validation/lot_leakage_diagnostics.json` ✅ (trackb_run에서 자동 생성)
- `validation/random_seed_sweep.csv`, `random_seed_sweep_summary.json` ✅
- Core 보고서: Lot leakage 표 + Random baseline variability 섹션 ✅
- 메인 보고서: 비용 컬럼 _norm 라벨 + 3000/150/500 문장 ✅
- final_validation_report.json: verdict=READY_WITH_LIMITATIONS ✅

## 4. 수정 사항 (이번 검증 중 반영)

1. **trackb_run.py**: Pipeline 완료 후 `lot_leakage_diagnostics.compute_lot_diagnostics`, `random_seed_sweep.run_sweep` 호출 추가 → paper_reports/final_validation에서 사용하는 JSON/CSV 항상 생성.
2. **integration/pipeline.py**: 로그 메시지 `cost=$...` → `cost(norm)=...` 변경 (정책 일치).

E2E 완료: 모든 규칙 통과 (verify + FINAL_VALIDATION verdict).
