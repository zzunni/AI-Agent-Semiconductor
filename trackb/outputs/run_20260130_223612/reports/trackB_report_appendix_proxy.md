# Track B Appendix (Proxy Only)
## Step2/Step3 — Plausibility Only, NOT Causal

**배너**: 본 부록은 Proxy(Step2/Step3) 결과만 다룹니다. Core 결론에 섞이지 않습니다.

**Appendix only — 주요 결론 제외**: Proxy validation FAILED. Step2/Step3 수치는 주요 결론에 사용하지 않습니다.

---
## Step2B (WM-811K)

- Dataset: WM-811K. Objective: wafermap pattern classification (proxy).
- Model: SmallCNN. Outputs: pattern labels, severity.
- Why proxy: Different data source; no same-wafer GT.

---
## Step3 (Carinthia)

- Dataset: Carinthia. Objective: SEM defect classification (proxy).
- Outputs: defect classes, engineer decisions.
- Why proxy: Different data source; no same-wafer GT.

---
## Integration Mapping & Plausibility Checks

- KS statistic: 0.41
- p-value: 1.99799391269964e-15
- Passed: False
- Plausibility only; 인과 증명 아님.

---
## Future Work

- 동일 wafer 다단계 측정 데이터 수집 필요.
- Same-source Step2/Step3 GT가 있으면 Core로 확장 가능.
