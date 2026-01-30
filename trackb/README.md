# Track B: Scientific Validation Pipeline
## AI 기반 모듈러 반도체 검사 프레임워크 - 과학적 검증

## 개요

Track B는 반도체 웨이퍼 검사 프레임워크의 과학적 검증을 위한 자동화된 배치 파이프라인입니다.

**목적**: 출판 가능한 실험 결과 생성
**방법**: Artifact-driven, 재현 가능, 자율 최적화

## 주요 기능

### ✅ 구현 완료

1. **베이스라인 비교**
   - Random Sampling (업계 표준)
   - Rule-based (단순 임계값)

2. **자율 최적화 Agent**
   - Threshold Optimizer: 최적 임계값 탐색
   - Budget-aware Scheduler: 동적 예산 관리
   - Decision Explainer: 결정 추적

3. **Ground Truth 검증**
   - 200개 실제 웨이퍼 테스트
   - T-test, Chi-square, Bootstrap 통계 검정

4. **자동 보고서 생성**
   - 마크다운 보고서
   - 출판용 그래프
   - SHA256 매니페스트

## 빠른 시작

```bash
cd trackb/
python scripts/trackb_run.py --mode from_artifacts
```

## 디렉토리 구조

```
trackb/
├── configs/              # 설정 파일
│   └── trackb_config.json
├── scripts/              # 실행 스크립트
│   ├── trackb_run.py     # 메인 진입점
│   ├── common/           # 공통 유틸리티
│   ├── baselines/        # 베이스라인 구현
│   ├── agent/            # Agent 구성 요소
│   ├── integration/      # 아티팩트 로더
│   ├── validation/       # 검증 모듈
│   └── visualization/    # 시각화
├── docs/                 # 문서
│   ├── interface_spec.md
│   └── runbook.md
├── outputs/              # 출력 (자동 생성)
│   ├── baselines/
│   ├── agent/
│   ├── validation/
│   ├── figures/
│   └── reports/
└── README.md
```

## 검증 상태

| 구성 요소 | 상태 | 설명 |
|-----------|------|------|
| Stage 0–2A (STEP 1) | ✅ | Same-source, yield_true GT validated |
| Stage 2B (STEP 2) | ⚠️ | Benchmark performance reported (proxy; WM-811K) |
| Stage 3 (STEP 3) | ⚠️ | Benchmark performance reported (proxy; Carinthia) |
| 통합 | ⚠️ | Proxy plausibility check only (not causal) |

## 주요 결과 (예시, run_20260131_004542 기준)

**Primary endpoints** (Step1 Core, selection_rate=10%):

| Method | High-risk Recall | Cost per catch (norm) |
|--------|------------------|----------------------|
| random | 5.0% | 1500 |
| rulebased | 12.5% | 600 |
| framework | 15.0% | 500 |

**Note**: Cost values are in **normalized units (not currency)**. Core conclusions use bootstrap 95% CI only. See `outputs/run_*/reports/trackB_report_core_validated.md` for full results.

## 관련 문서

- [실행 가이드](docs/runbook.md)
- [인터페이스 명세](docs/interface_spec.md)
- [전체 보고서](outputs/reports/trackB_report.md) (실행 후 생성)

## 라이선스

내부 연구용

## 연락처

반도체 검사 AI 연구팀
