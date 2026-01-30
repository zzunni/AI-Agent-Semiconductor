# Methodology
## 실험 방법론

### 1. 데이터 분리 (CRITICAL)
- **Training set**: 1,050 wafers
  - Train inner: 840 wafers (80%)
  - Validation: 210 wafers (20%) - Optimizer 전용
- **Test set**: 200 wafers (SACRED - 최종 평가 전용)
- Train/Test 중복 없음 확인됨

### 2. Baseline 방법
- **Random**: 무작위 10% 선택
- **Rule-based**: Risk score 상위 10% 선택

### 3. 제안 프레임워크
- **Threshold Optimizer**: Validation set에서 grid search
- **Budget Scheduler**: 동적 예산 관리
- **Decision Explainer**: 결정 추적

### 4. 통계 검정
- Chi-square test (검출률 비교)
- McNemar test (paired sample 비교)
- Bootstrap CI (비용 절감 신뢰구간)

### 5. 용어 정의
- "Validated": Ground truth (yield_true) 기반 검증
- "Independently validated": 별도 벤치마크 데이터셋 검증
- "Proxy-based": 통계적 매핑, 인과관계 미입증
