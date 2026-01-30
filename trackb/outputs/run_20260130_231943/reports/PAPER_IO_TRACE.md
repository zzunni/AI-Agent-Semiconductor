# PAPER_IO_TRACE
## 주장·수치 → 파일(sha256)·컬럼·용도 추적

| 파일 (상대경로) | sha256 | 사용 컬럼/키 | 여기서의 용도 |
|------------------|--------|--------------|---------------|
| validation/framework_results.csv | 16caeec8481f7c81... | method, high_risk_recall, true_positive, selected_count, total_cost, cost_per_catch 등 | Primary 결과 표·baseline vs framework 비교 |
| validation/bootstrap_primary_ci.json | bdcd93cdc0716273... | recall_ci, cost_ci (percent_reduction, delta_cost_pct_ci) | Recall/Cost 95% CI, Core 결론 수치 |
| validation/high_risk_definition.json | a75409885625a8d3... | N, k, method, actual_rate | GT high-risk 정의·실험 정책 고정 |
| validation/sensitivity_cost_ratio.csv | 828e1dddcd0a47fc... | r, method, recall_high_risk, normalized_cost, cost_per_catch, dominance_flag, dominance_type | r-sweep·dominance 해석 |
| validation/proxy_validation.json | 19951f0ed83c241a... | proxy_status, ks_statistic, p_value | Appendix 전용·Core 결론 미사용 |

**기계적 정의**: 위 표의 각 행은 "이 파일(sha256=... )의 해당 컬럼/키가 Core 또는 Appendix 보고서에서 위 용도로 쓰였다"를 의미.
- 전체 path·sha256·row_count·columns: `paper_bundle.json` → evidence_index, `_manifest.json`
