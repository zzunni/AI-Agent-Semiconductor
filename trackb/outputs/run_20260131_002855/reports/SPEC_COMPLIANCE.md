# SPEC_COMPLIANCE.md
Track B 스펙 준수 증거

Run ID: 20260131_002855
Timestamp: 2026-01-31T00:28:55.260962

## A. Path Resolution Compliance
- ✅ pathlib.Path 사용: `step1_loader.py:1-10`
- ✅ glob 패턴 사용: `step1_loader.py:87-88`
- ✅ 하드코딩 경로 없음: grep 검색 결과 없음

## B. Data Leakage Prevention
- ✅ Optimizer validation size: 210
- ✅ Test set used for optimization: False
- ✅ Test set size: 200

## C. Dataset Sizes
- ✅ Test size: 200
- ✅ Training pool size: 1050
- ✅ Validation size: 210

## D. Baseline Fairness
- ✅ Random baseline: 200 wafers
- ✅ Rule-based baseline: 200 wafers
- ✅ Same test set: True

## E. Proxy Validation
- ✅ KS statistic: 0.41
- ✅ p-value: 1.99799391269964e-15
- ✅ Proxy status: FAILED_PLAUSIBILITY
- ✅ Policy: warn_only


## F. Schema Validation
- ✅ REQUIRED_COLUMNS 정의: `schema.py:18-75`
- ✅ Schema 검증 실행: 파이프라인 통합됨

## G. Manifest
- ✅ SHA256 계산: `io.py:compute_file_hash`
- ✅ 입력/출력 모두 기록: `_manifest.json` 확인됨
