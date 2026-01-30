# Step3 Report (Random vs AI-assisted + Stage3/Engineer Loop)

본 리포트는 Stage2B(SEM 후보 선별) → Stage3(Decision Card 매칭) → UI(엔지니어 결정) 흐름에서,
동일 예산(K) 조건에서 Random 추출 대비 AI-assisted 선별 전략의 효율을 비교하고,
Stage3 결과와 엔지니어 결정 분포를 함께 요약한다.

## 1) Efficiency Summary
| Group | K | Total SEM Cost | Mean Severity | A | B | C | D | B+C+D |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| random | 100 | $500,000 | 49.35 | 76.0% | 2.0% | 20.0% | 2.0% | 24.0% |
| ai | 100 | $500,000 | 88.79 | 86.0% | 0.0% | 10.0% | 4.0% | 14.0% |

Artifacts:
- `outputs/selections/selected_mapped.csv` : wafer_id ↔ case_id 정합 테이블
- `outputs/efficiency/efficiency_table.csv` : 비교 지표 표
- `outputs/ui_logs/engineer_decisions.csv` : triage 기반 엔지니어 결정 로그(시뮬레이터)
- Stage3 results used: `outputs/stage3/stage3_results_final.csv`

## 2) Stage3 + Engineer Decision Summary
- Rows: **200**
- engineer_decision NULL rate: **0.0%**

### 2.1 Engineer Decision Distribution
| engineer_decision | count | rate |
| --- | --- | --- |
| IMPLEMENT | 157 | 0.785 |
| INVESTIGATE | 25 | 0.125 |
| MODIFY | 14 | 0.07 |
| DEFER | 4 | 0.02 |

### 2.2 Triage × Engineer Decision (Counts)
| triage | DEFER | IMPLEMENT | INVESTIGATE | MODIFY |
| --- | --- | --- | --- | --- |
| A_strong_evidence | 0 | 147 | 7 | 8 |
| B_overconfidence_warn | 0 | 0 | 2 | 0 |
| C_ambiguous_boundary | 3 | 9 | 15 | 3 |
| D_acquisition_risk | 1 | 1 | 1 | 3 |

### 2.3 Sanity (Head)
```
selection_tag wafer_id   pattern  severity               triage  pred_class  gt  calibrated_conf  entropy     process_improvement_action engineer_decision
           ai  W000605      blob     79.77    A_strong_evidence           3   3         0.930911 0.360492                        Confirm         IMPLEMENT
           ai  W001334      blob     63.11    A_strong_evidence           3   3         0.961802 0.216034                        Confirm         IMPLEMENT
           ai  W000109    random     51.83    A_strong_evidence           3   3         0.977777 0.140770                        Confirm            MODIFY
           ai  W001263    random     66.75    A_strong_evidence           3   3         0.894287 0.395894                        Confirm         IMPLEMENT
           ai  W000897    random     70.76    A_strong_evidence           3   3         0.976443 0.145321                        Confirm         IMPLEMENT
           ai  W001456    random      5.49    A_strong_evidence           6   6         0.966919 0.187295                        Confirm       INVESTIGATE
           ai  W001920      blob     29.75    A_strong_evidence           3   3         0.954433 0.252697                        Confirm         IMPLEMENT
           ai  W000166    random     54.99    A_strong_evidence           3   3         0.954242 0.249645                        Confirm         IMPLEMENT
           ai  W000407    random     27.04 C_ambiguous_boundary           3   3         0.705392 1.065808 Re-check + Optional re-acquire         IMPLEMENT
           ai  W001590    random     40.20    A_strong_evidence           3   3         0.945605 0.291527                        Confirm         IMPLEMENT
           ai  W001864 edge-ring     85.89    A_strong_evidence           3   3         0.961711 0.222219                        Confirm         IMPLEMENT
           ai  W000836 edge-ring     86.10 C_ambiguous_boundary           4   4         0.391886 1.332556 Re-check + Optional re-acquire             DEFER
```

## 3) Step3 Operational Impact (Data-driven)

Based on simulated triage distribution from **ai** selection (K=100),
the expected operational load per 100 reviewed wafers is estimated as follows:

| Triage | Rate | Expected cases / 100 | Manual intervention rate |
| --- | --- | --- | --- |
| A_strong_evidence | 86.0% | 86.0 | Low (auto-confirmable) |
| C_ambiguous_boundary | 10.0% | 10.0 | Medium |
| D_acquisition_risk | 4.0% | 4.0 | High |
| B_overconfidence_warn | 0.0% | 0.0 | High |

This indicates that the proposed Step3 pipeline can automatically
confirm approximately **86%** of SEM cases,
while concentrating human review on the remaining **14% high-risk cases**.

## 4) Step3 Interface Spec (Appendix)
Source: `stage3/step3_interface_spec.md`

---
# Step3 Interface Spec (SEM Defect Analyst)

본 문서는 `sem_step003` 기준 Step3(SEM Defect Analyst)의 **입출력 규격**과, Stage2B(선별) → Stage3(매칭/카드) → UI(엔지니어 결정) 흐름을 정의합니다.

## 1) Purpose
- Step3는 **정답 판정기**가 아니라,
  - (1) SEM 분류 결과(결함 클래스) + 불확실성(triage)
  - (2) 클래스/triage 기반 운영 가이드(원인 가설/체크리스트)
  - (3) 조치 권고(action)
  를 묶어 **Decision Card**로 제공하는 레이어입니다.

## 2) Pipeline
1. `sim/00_find_inputs.py` : 입력 경로 캐시(`sim/_cache/paths.json`) 생성/검증
2. `sim/01_stage2b_selector.py` : AI-assisted Top-K 선별 → `outputs/selections/selected_ai.csv`
3. `sim/02_random_selector.py` : Random Top-K → `outputs/selections/selected_random.csv`
4. `sim/03_stage3_mapper.py` : wafer_id ↔ case_id 매핑 → `outputs/selections/selected_mapped.csv`
5. (Real Step3) `stage3_defect_matcher.py` : mapped selection + decision_cards join → `outputs/stage3/stage3_results.csv`
6. `sim/05_ui_simulator.py` : triage 기반 엔지니어 결정 샘플링 → `outputs/ui_logs/engineer_decisions.csv`
7. `sim/04_efficiency_eval.py` : 효율 비교 테이블/요약 → `outputs/efficiency/*`
8. `sim/06_report_generator.py` : 리포트 생성 → `outputs/reports/efficiency_comparison.md`

> Note: `sim/05_ui_simulator.py`는 `process_improvement_action` 필드를 표준으로 사용합니다.
> (`ai_immediate_action`은 폐기/이관: **필드명만 변경, 로직 변경 없음**)

## 3) Key Artifacts
### 3.1 Decision Cards (`outputs/sem_decision_cards/decision_cards.csv`)
필수 컬럼:
- `img_path` : 케이스 식별자(경로). `selected_mapped.csv`의 `case_id`와 join됨
- `triage` : A_strong_evidence / B_overconfidence_warn / C_ambiguous_boundary / D_acquisition_risk
- `pred_class`, `gt`(optional), `calibrated_conf`, `entropy`, `brightness_tag`(optional)
- `cause_hypo_1..3`, `check_1..3`
- `process_improvement_action` : **표준 액션 필드(새 이름)**
- `recommendation` : (호환용) 기존 필드 유지 가능
- `dr_priority`, `auto_confirm_allowed`

### 3.2 Stage3 Results (`outputs/stage3/stage3_results.csv`)
= `selected_mapped.csv`(선별 결과) + `decision_cards.csv`(Step3 카드) join 결과.

필수 컬럼(최소):
- selection 측: `selection_tag`, `wafer_id`, `pattern`, `severity`, `case_id`
- Step3 측: `img_path`, `triage`, `pred_class`, `gt`, `calibrated_conf`, `entropy`,
  `cause_hypo_1..3`, `check_1..3`, `process_improvement_action`, `dr_priority`, `auto_confirm_allowed`

엔지니어 입력 컬럼(초기 NULL):
- `engineer_decision` (IMPLEMENT / MODIFY / INVESTIGATE / DEFER)
- `engineer_modification` (optional free text)
- `engineer_note` (optional free text)
- `decision_timestamp` (optional)

## 4) Config
- `config/stage3_config.json` : Step3 matcher 실행에 필요한 경로/조인키/출력 설정

## 5) Mapping
- `configs/defect_to_action_mapping_data_driven.json` : **(official)** triage 분포 기반 운영부하/impl_cost 추정치 포함 (data-driven)
