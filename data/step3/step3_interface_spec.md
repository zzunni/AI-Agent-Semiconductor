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
- `defect_to_action_mapping.json` : triage 정책/권고(action) 정의 + (선택) 구현 비용 추정치

