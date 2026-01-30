# Executive Summary
## Track B 검증 결과 요약

### 핵심 성과
- **고위험 재현율**: 5.0% → 15.0% (동일 테스트 조건)
- **데이터**: 200개 실제 fab 웨이퍼 (Ground Truth: yield_true)
- **방법**: 자율 최적화 Agent (Threshold Optimizer + Budget Scheduler)

### 검증 상태
- Stage 0–2A: ✅ Same-source, yield_true GT validated
- Stage 2B/3: ⚠️ Benchmark performance reported (proxy; different source)
- Integration: ⚠️ Proxy plausibility check only (not causal)

### 핵심 기여
동일 테스트 조건에서 고위험 검출 재현율이 5.0%→15.0%로 개선되는 신호를 관측하였다(ΔRecall 95% CI가 0을 포함하므로 단정은 금지). 최종 결론은 bootstrap CI 기반 primary endpoint만 사용한다.
