# PAPER_IO_TRACE
## 주장·수치 → 파일(sha256)·컬럼·용도 추적

| 파일 (상대경로) | sha256 | 사용 컬럼/키 | 여기서의 용도 |
|------------------|--------|--------------|---------------|
| validation/framework_results.csv | 16caeec8481f7c81... | method, true_positive, false_negative, high_risk_recall, selected_count, total_cost, cost_per_catch 등 | Primary 결과 표·Effect size(TP gain, FN reduction)·baseline vs framework |
| validation/bootstrap_primary_ci.json | bdcd93cdc0716273... | recall_ci, cost_ci (percent_reduction, delta_cost_pct_ci) | Recall/Cost 95% CI, Core 결론 수치 |
| validation/high_risk_definition.json | a75409885625a8d3... | N, k, method, actual_rate | GT high-risk 정의·실험 정책 고정 |
| validation/sensitivity_cost_ratio.csv | 828e1dddcd0a47fc... | r, method, recall_high_risk, normalized_cost, cost_per_catch, dominance_flag, dominance_type | r-sweep·dominance 해석 |
| validation/lot_leakage_diagnostics.json | 4f49fccdb8c3d50a... | n_test_wafers, n_test_lots, overlap_lots_count, overlap_wafers_count, high_risk_rate_by_lot_* | Limitations·Lot leakage 리스크 진단 표(무재학습) |
| validation/random_seed_sweep_summary.json | fab64529bdaf03e6... | recall_mean, recall_std, recall_p5, recall_p50, recall_p95 | Random multi-seed recall 분포·Framework 위치 |
| validation/proxy_validation.json | 19951f0ed83c241a... | proxy_status, ks_statistic, p_value | Appendix 전용·Core 결론 미사용 |

**기계적 정의**: 위 표의 각 행은 "이 파일(sha256=... )의 해당 컬럼/키가 Core 또는 Appendix 보고서에서 위 용도로 쓰였다"를 의미.
- 전체 path·sha256·row_count·columns: `paper_bundle.json` → evidence_index, `_manifest.json`
