# Track B Inputs

## 데이터 위치

Track B의 입력 데이터는 **프로젝트 루트의 `data/` 디렉토리**에 있습니다.

```
project_root/
├── data/                 # ← 실제 데이터 위치
│   ├── step1/           # Stage 0-2A 아티팩트
│   ├── step2/           # Stage 2B 아티팩트
│   └── step3/           # Stage 3 아티팩트
│
└── trackb/
    ├── inputs/          # ← 현재 디렉토리 (설명용)
    └── ...
```

## 경로 설정

`configs/trackb_config.json`에서 경로를 설정합니다:

```json
{
  "paths": {
    "step1_artifacts": "../data/step1/",
    "step2_artifacts": "../data/step2/",
    "step3_artifacts": "../data/step3/"
  }
}
```

## 필요 파일

### Step 1 (필수)
- `_stage0_test*.csv` - 테스트 데이터
- `_stage0_pred*.csv` - 예측 결과 (yield_true 포함)

### Step 2 (선택)
- `test_accuracy_summary.json` - 테스트 정확도
- `stage2b_results.csv` - Stage 2B 결과

### Step 3 (선택)
- `stage3_results_final.csv` - 최종 결과
- `efficiency_summary.json` - 효율 요약

## 주의사항

- 한글 파일명 (예: `오후 1.17.11`)이 포함된 경우 glob 패턴 사용
- 파일이 없으면 해당 단계는 스킵됨
- Ground truth (yield_true)는 Step 1에서만 사용 가능
