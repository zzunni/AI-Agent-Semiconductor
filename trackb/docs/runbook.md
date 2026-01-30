# Track B Runbook
## 실행 가이드

## 빠른 시작

### 1. 기본 실행

```bash
cd trackb/
python scripts/trackb_run.py --mode from_artifacts
```

### 2. 빠른 테스트 (그림 스킵)

```bash
cd trackb/
python scripts/trackb_run.py --mode from_artifacts --skip_figures
```

### 3. 상세 로그와 함께 실행

```bash
cd trackb/
python scripts/trackb_run.py --mode from_artifacts --verbose
```

## 사전 요구사항

### 필요 파일

Track B 실행 전 다음 파일들이 있어야 합니다:

**Step 1 (data/step1/)**:
- `_stage0_test*.csv` - 테스트 데이터
- `_stage0_pred*.csv` - 예측 결과
- `_stage0_risk_scores*.csv` - 리스크 점수 (선택적)

**Step 2 (data/step2/)** - 선택적:
- `test_accuracy_summary.json` - 테스트 정확도
- `stage2b_results.csv` - Stage 2B 결과

**Step 3 (data/step3/)** - 선택적:
- `stage3_results_final.csv` - 최종 결과
- `efficiency_summary.json` - 효율 요약

### Python 의존성

```bash
pip install numpy pandas scipy matplotlib scikit-learn
```

## 실행 모드

### `from_artifacts` (기본)
- 기존 아티팩트에서 분석 실행
- 베이스라인 평가
- Agent 최적화 및 스케줄링
- 통계 검증
- 시각화 및 보고서 생성

### `quick`
- `from_artifacts`와 동일하지만 그림 생성 스킵
- 디버깅 및 빠른 테스트용

### `full`
- 전체 검증 포함
- 모든 시각화 생성

## 출력 파일

실행 완료 후 다음 파일들이 생성됩니다:

```
trackb/outputs/
├── baselines/
│   ├── random_results.csv
│   ├── rulebased_results.csv
│   └── comparison_table.csv
├── agent/
│   ├── autotune_summary.json
│   ├── autotune_history.csv
│   ├── scheduler_log.csv
│   └── decision_trace.csv
├── validation/
│   ├── framework_results.csv
│   └── statistical_tests.json
├── figures/
│   ├── cost_comparison.png
│   ├── detection_performance.png
│   └── ...
├── reports/
│   ├── trackB_report.md
│   ├── step1_report.md
│   ├── step2_report.md
│   └── step3_report.md
└── _manifest.json
```

## 설정 변경

### 예산 변경
`configs/trackb_config.json`:
```json
{
  "agent": {
    "budget_total": 25000
  }
}
```

### 임계값 탐색 공간 변경
```json
{
  "agent": {
    "threshold_search_space": [0.4, 0.5, 0.6, 0.7]
  }
}
```

### 고위험 기준 변경
```json
{
  "data": {
    "high_risk_threshold": 0.5
  }
}
```

## 문제 해결

### 파일을 찾을 수 없음

```
FileNotFoundError: 파일을 찾을 수 없습니다: data/step1/_stage0_test*.csv
```

**해결**: 
1. `data/step1/` 디렉토리 확인
2. 한글 파일명 확인 (예: `오후 1.17.11`)
3. 파일 존재 여부 확인

### 메모리 부족

큰 데이터셋 처리 시:
```bash
export PYTHONMALLOC=malloc
python scripts/trackb_run.py --mode from_artifacts
```

### 그래프 폰트 문제

한글 폰트 문제 시:
```python
# visualization/*.py에서
plt.rcParams['font.family'] = 'DejaVu Sans'
```

## 검증 체크리스트

실행 후 확인:

- [ ] `trackb_run.log` 오류 없음
- [ ] `_manifest.json` 생성됨
- [ ] `trackB_report.md` 완전함
- [ ] 통계 검정 p-values 포함
- [ ] 그림 파일들 생성됨 (skip_figures 아닐 경우)

## 재현성 확인

동일 결과 재현:
1. 랜덤 시드 고정 (config에서 `random_seed: 42`)
2. 입력 파일 SHA256 확인 (`_manifest.json`)
3. 동일 Python 버전 사용

```bash
# 재현성 확인
python scripts/trackb_run.py --mode from_artifacts
diff outputs/_manifest.json expected_manifest.json
```
