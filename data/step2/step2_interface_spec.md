# step2 interface spec

본 문서는 step2 산출물을 stage2b(sem selector + pattern matcher)에서 소비하기 위한 인터페이스를 정의한다.

## 1) 입력 경로 규칙

- base_dir
  - 03_severity
    - severity_scores_all.csv
  - config
    - stage2b_config.json
  - pattern_to_process_mapping.json

## 2) 입력 파일 스키마

### 03_severity/severity_scores_all.csv 필수 컬럼
- orig_idx
- pred_label
- severity

### 룰을 만족하기 위해 필수인 컬럼 (없으면 stage2b는 룰을 판정할 수 없음)
- random_like (0/1)
- blob_like (0/1)
- cluster_like (0/1)

## 3) stage2b 동작 요약

- top 10% severity 후보를 계산한다.
- top 10% 안에서 pred_label == scratch는 sem이 아니라 physical damage bucket으로 라우팅한다.
- scratch를 제외한 top 10% 후보에서 random_like/blob_like/cluster_like는 sem으로 반드시 포함한다.
- 예산이 설정된 경우 mandatory를 먼저 포함하고 남는 슬롯을 severity 순으로 채운다.

## 4) 산출물

- stage2b_results.csv
  - engineer_approved_count 컬럼은 비어 있어야 한다.

## 5) 실행 예시

- python stage2b_sem_selector.py --base_dir "<your_base_dir>" --config "<your_base_dir>/config/stage2b_config.json"
