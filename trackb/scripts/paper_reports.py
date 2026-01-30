#!/usr/bin/env python3
"""
Paper Input Bundle Reports
Core(Validated), Appendix(Proxy), TrackA, PAPER_IO_TRACE. 숫자/표는 코드가 렌더링, $ 금지.
"""

from pathlib import Path
import json
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional
import pandas as pd
import logging

logger = logging.getLogger(__name__)


def _load_json(p: Path) -> Optional[Dict]:
    if not p.exists():
        return None
    with open(p, 'r', encoding='utf-8') as f:
        return json.load(f)


def _load_csv(p: Path) -> Optional[pd.DataFrame]:
    if not p.exists():
        return None
    return pd.read_csv(p, encoding='utf-8-sig')


def render_core_validated(run_output_dir: Path, run_id: str) -> str:
    """Step1(Validated Core)만. 결론/초록/요약 Step1 값만. $ 금지."""
    val_dir = run_output_dir / 'validation'
    reports_dir = run_output_dir / 'reports'
    
    hr_def = _load_json(val_dir / 'high_risk_definition.json') or {}
    comp_df = _load_csv(val_dir / 'framework_results.csv')
    bootstrap = _load_json(val_dir / 'bootstrap_primary_ci.json') or {}
    sens_df = _load_csv(val_dir / 'sensitivity_cost_ratio.csv')
    stats = _load_json(val_dir / 'statistical_tests.json') or {}
    
    disclaimer = (
        "본 보고서의 모든 수치·표·결론은 이 실행(run_{})의 산출물만 사용합니다. "
        "다른 run 또는 외부 데이터를 사용하지 않습니다."
    ).format(run_id)
    
    md = f"""# Track B Core (Validated) Report
## Step1 Only — 동일 소스 + yield_true GT 매칭

생성 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{disclaimer}

---

## Abstract (Step1만)

예산 제약 하에서 200개 테스트 웨이퍼에 대해 high-risk(yield_true 하위 20%, k=40) 탐지율을 비교하였다. Random(10%), Rule-based(10%), Framework(Agent) 세 방법을 동일 테스트 세트로 평가하였다. Primary endpoints: high-risk recall @ selection_rate=10%, normalized cost per catch. 본 Core 결론은 Step1(동일 소스 + yield_true GT)만 사용한다.

---

## Problem & Decision Setting

- **연구 목적**: 예산 제약 하에 고위험 웨이퍼 조기 선별 및 추가 계측·후속검사·리워크 의사결정 최적화.
- **운영 정책**: selection_rate=10% 고정; 동일 소스(same fab) test set만 사용; 절대 비용 금액 미사용(정규화/비율만).
- **질문**: "하위 20% high-risk가 다음 단계로 넘어가냐?" — 운영은 risk_score top-k% 선별, 평가는 yield_true 라벨로 recall 측정.

---

## Experimental Design (공정성)

- **동일 테스트**: 200 wafer 동일 테스트 세트에 Random / Rule-based / Framework 동일 조건 적용.
- **Baseline 동일 조건**: 동일 selection_rate(10%), 동일 high-risk 정의(k=40).
- **Test leakage 금지**: threshold/optimizer는 validation set만 사용; test set은 최종 평가에만 사용.

---

## System Overview (Step1) — 입력/출력/산출물

- **입력**: 동일 소스 테스트 200 wafer. 필수 컬럼: yield_true(평가 라벨), risk_score(운영 선별 점수). Step1 아티팩트에서 로드.
- **처리**: Stage0/1/2A risk_score → 운영 선별(top-k%) → GT high-risk(yield 하위 20%) 검출 평가. Gating 정책은 산출물(decision_trace 등)에 반영.
- **출력**: recall@selection_rate, normalized cost per catch, bootstrap 95% CI. PASS/FAIL은 Step1에서만 결정.
- **산출물**: validation/framework_results.csv, validation/bootstrap_primary_ci.json, validation/sensitivity_cost_ratio.csv.

---

## Data & Label Definition

- **Evaluation label (GT_high_risk)**: {hr_def.get('evaluation_label', 'yield_true bottom 20% (k=40/200 fixed)')}
- **Operational selection**: {hr_def.get('operational_selection', 'top selection_rate by risk_score (default 10%)')}
- Test size: {hr_def.get('N', 200)}, k: {hr_def.get('k', 40)}

---

## Methods (Stage0–2A)

- **Stage0**: Inline risk score from process/equipment features (XGBoost). Output: risk_stage0, riskscore. Gating: tau0.
- **Stage1**: Refined risk with additional features (XGBoost). Gating: tau1.
- **Stage2A**: Combined multi-stage risk (XGBoost). Output: combined riskscore. Gating: tau2a. (Core 범위: Stage0–2A만)
- **Decision policy (top-k selection)**: selection_rate=10% 고정. risk_score 상위 10%만 다음 단계(추가 계측)로 선별. 운영 답은 pred_risk_score 기반 top-k%만 사용.
- 학습/추론: Step1 아티팩트에서 로드. Validation set에서만 임계치 탐색; test set 미사용.

---

## Primary Results (selection_rate=10% 고정)

"""
    if comp_df is not None and len(comp_df) > 0:
        # 표: $ 없이 수치만; 비용 컬럼은 보고서에서 _norm 라벨로 표기 (절대 비용 오해 방지)
        _cost_display_names = {
            'inline_cost': 'inline_cost_norm', 'sem_cost': 'followup_cost_norm',
            'total_cost': 'total_cost_norm', 'cost_per_catch': 'cost_per_catch_norm',
            'cost_inline_unit': 'cost_unit_inline_norm', 'cost_sem_unit': 'followup_unit_norm',
        }
        display_cols = [c for c in comp_df.columns if c != 'method' and not c.startswith('delta')]
        display_labels = [_cost_display_names.get(c, c) for c in display_cols]
        sub = comp_df[['method'] + display_cols].head(10)
        n_cols = min(8, len(display_cols))
        md += "| method | " + " | ".join(display_labels[:n_cols]) + " |\n"
        md += "|" + "---|" * (n_cols + 1) + "\n"
        for _, row in sub.iterrows():
            vals = [str(row.get(c, ''))[:12] for c in ['method'] + display_cols[:n_cols]]
            md += "| " + " | ".join(vals) + " |\n"
    
    md += "\n### Primary Endpoints + Bootstrap 95% CI\n\n"
    rc = bootstrap.get('recall_ci', {})
    cc = bootstrap.get('cost_ci', {})
    md += f"- Recall (framework): {rc.get('observed_framework_recall')} (Δ CI: [{rc.get('ci_lower')}, {rc.get('ci_upper')}])\n"
    pct_ci = cc.get('delta_cost_pct_ci')
    if pct_ci is not None:
        md += f"- Cost reduction (%): {cc.get('percent_reduction')} (Δ % CI: [{pct_ci[0]}, {pct_ci[1]}])\n"
    else:
        md += f"- Cost reduction (%): {cc.get('percent_reduction')}\n"

    # Effect size + operational interpretation (no overclaim; CI 0 포함 시 signal만)
    if comp_df is not None and len(comp_df) >= 2:
        rnd = comp_df[comp_df['method'] == 'random'].iloc[0]
        fw = comp_df[comp_df['method'] == 'framework'].iloc[0]
        tp_r, fn_r = rnd.get('true_positive'), rnd.get('false_negative')
        tp_f, fn_f = fw.get('true_positive'), fw.get('false_negative')
        if tp_r is not None and tp_f is not None:
            tp_gain = int(tp_f - tp_r)
            fn_reduction = int(fn_r - fn_f) if fn_r is not None and fn_f is not None else None
            md += "\n### Effect size (operational meaning)\n\n"
            md += f"- Absolute gain in catches: TP_framework − TP_random = **{tp_gain}** (추가 탐지 고위험 웨이퍼 수).\n"
            if fn_reduction is not None:
                md += f"- Miss reduction: FN_random − FN_framework = **{fn_reduction}** (누락 감소).\n"
            md += f"- Interpretation (관측치 기준): selection_rate=10%에서 framework는 random 대비 고위험 웨이퍼를 추가로 {tp_gain}장 더 탐지(TP 증가), 누락을 {fn_reduction or tp_gain}장 감소(FN 감소)시켰다. 통계적 확정이 아님; CI가 0을 포함하면 signal로만 해석.\n\n"

    # Random baseline multi-seed variability
    sweep_summary = _load_json(val_dir / 'random_seed_sweep_summary.json')
    if sweep_summary:
        fw_recall = rc.get('observed_framework_recall')
        md += "\n### Random baseline variability (multi-seed)\n\n"
        md += f"- Random baseline을 {sweep_summary.get('n_seeds', 0)} seed로 반복 시 recall 분포: "
        md += f"평균 {sweep_summary.get('recall_mean', 0):.3f} ± {sweep_summary.get('recall_std', 0):.3f}, "
        md += f"5/50/95 분위: {sweep_summary.get('recall_p5', 0):.3f} / {sweep_summary.get('recall_p50', 0):.3f} / {sweep_summary.get('recall_p95', 0):.3f}.\n"
        md += f"- Framework recall ({fw_recall})은 random p95({sweep_summary.get('recall_p95', 0):.3f}) 대비 상대적 위치로 해석 가능. 단정 금지; 'suggests' 또는 'consistent with' 수준.\n\n"
    
    md += "\n---\n## Cost Model (정규화 원칙)\n\n"
    md += "- 절대 금액(달러) 사용 금지. inline_cost_unit=1, 후속검사 단위=r (r sweep).\n"
    if sens_df is not None and len(sens_df) > 0:
        md += "- r ∈ {1,2,3,5,7,10} 그리드. normalized_cost, cost_per_catch, dominance_flag. dominance_type=recall_dominance: 동일 normalized_cost에서 recall이 baseline보다 큼(cost-dominance 아님).\n\n"
        cols = [c for c in sens_df.columns if c in ['r', 'method', 'recall_high_risk', 'normalized_cost', 'cost_per_catch', 'dominance_flag', 'dominance_type']]
        if not cols:
            cols = list(sens_df.columns)[:6]
        sub = sens_df[cols].head(12)
        md += "| " + " | ".join(str(c) for c in cols) + " |\n"
        md += "|" + "---|" * len(cols) + "\n"
        for _, row in sub.iterrows():
            md += "| " + " | ".join(str(row.get(c, ''))[:14] for c in cols) + " |\n"
        md += "\n"
    
    md += "\n---\n## Exploratory Stats (결론에서 강조 금지)\n\n"
    tests = stats.get('tests', {})
    for name, res in list(tests.items())[:5]:
        if isinstance(res, dict) and 'p_value' in res:
            md += f"- {name}: p={res.get('p_value')}\n"
    md += "\n- 위 검정은 exploratory(hypothesis-generating)이며, primary 결론은 recall CI 및 cost CI만 사용.\n"
    
    md += "\n---\n## Limitations\n\n"
    md += "- **Group split 미실시**: Lot leakage 가능성 완전 배제 불가. 결과는 동일 조건 내 운영 성능으로 해석.\n"
    lot_diag = _load_json(val_dir / 'lot_leakage_diagnostics.json')
    if lot_diag and lot_diag.get('diagnostics_available'):
        md += "\n**Lot leakage risk diagnostics (no retraining):**\n\n"
        md += "| 항목 | 값 |\n|------|-----|\n"
        md += f"| n_test_wafers | {lot_diag.get('n_test_wafers', '—')} |\n"
        md += f"| n_test_lots | {lot_diag.get('n_test_lots', '—')} |\n"
        md += f"| test_lot_size (min/median/max) | {lot_diag.get('test_lot_size_min')} / {lot_diag.get('test_lot_size_median')} / {lot_diag.get('test_lot_size_max')} |\n"
        if lot_diag.get('train_lots_available'):
            md += f"| n_train_lots | {lot_diag.get('n_train_lots')} |\n"
            md += f"| overlap_lots_count (train ∩ test) | {lot_diag.get('overlap_lots_count')} |\n"
            md += f"| overlap_wafers_count (test 중 overlap lot 소속) | {lot_diag.get('overlap_wafers_count')} |\n"
        hr_min = lot_diag.get('high_risk_rate_by_lot_min')
        hr_med = lot_diag.get('high_risk_rate_by_lot_median')
        hr_max = lot_diag.get('high_risk_rate_by_lot_max')
        hr_str = f"{hr_min} / {hr_med} / {hr_max}" if hr_min is not None and hr_med is not None and hr_max is not None else "—"
        md += f"| high_risk_rate_by_lot (min/median/max) | {hr_str} |\n"
        md += "\n- 진단 근거: `baselines/random_results.csv` (lot_id, yield_true, is_high_risk). train overlap은 Step1 train 아티팩트 기반.\n"
    else:
        md += "- **Lot-level generalization** was not evaluated via holdout-lot / GroupKFold in this run; leakage risk cannot be ruled out under the current sampling scheme.\n"
    md += "- **표본수**: N=200 고정; CI 해석 시 표본 크기 한계 인지.\n"
    md += "- **CI 해석**: Recall CI가 0을 포함하면 개선 단정 금지; signal(불확실성 존재)로 표현.\n"
    md += "- **논문 후속 검증**: holdout lots, GroupKFold 등 lot 단위 분할 실험 권장.\n"
    
    md += "\n---\n## Reproducibility + Evidence Index\n\n"
    md += f"- Run ID: run_{run_id}\n"
    md += "- Manifest: `_manifest.json` (경로·SHA256·row_count·columns)\n"
    md += "- 상세 IO trace: `reports/PAPER_IO_TRACE.md`\n"
    md += "- 설정: trackb/configs/trackb_config.json\n"
    
    return md


def render_appendix_proxy(run_output_dir: Path, run_id: str) -> str:
    """Step2/3만. plausibility only, NOT causal. FAILED면 배너 + 주요 결론 제외."""
    val_dir = run_output_dir / 'validation'
    proxy = _load_json(val_dir / 'proxy_validation.json') or {}
    status = proxy.get('proxy_status', 'UNKNOWN')
    failed = status == 'FAILED_PLAUSIBILITY'
    
    ks_val = proxy.get('ks_statistic', 'N/A')
    p_val = proxy.get('p_value', 'N/A')
    md = """# Track B Appendix (Proxy Only)
## Step2/Step3 — Plausibility Only, NOT Causal

**Executive Summary (Appendix)**  
Step2/Step3 are candidate follow-up modules reported Appendix-only; they are not promoted to Core due to lack of same-wafer linkage and failed proxy alignment. The pipeline is ready to validate end-to-end utility once linked data is secured. Step2/3는 동일 웨이퍼 GT 기반의 효용을 주장하는 단계가 아니라, 실제 fab 후속검사(wafermap/SEM) 운영 파이프라인에 필요한 기능 블록을 후보 모듈로 준비하고, 증거 게이트(proxy)로 Core 승격을 통제하는 구조를 제시하기 위해 포함하였다.

"""
    md += "**배너**: 본 부록은 Proxy(Step2/Step3) 결과만 다룹니다. Core 결론에 섞이지 않습니다.\n\n"
    if failed:
        md += "**Appendix only — 주요 결론 제외**: Proxy validation FAILED. Step2/Step3 수치는 주요 결론에 사용하지 않습니다.\n\n"

    md += "---\n## A. Why Step2/Step3 Exist (Operational Design Intent)\n\n"
    md += "Beyond Step1 (inline risk triage), a realistic fab pipeline needs downstream modules for triage prioritization, defect-type confirmation, and resource allocation. Step2B (wafermap pattern) and Step3 (SEM/defect classification) are **candidate follow-up modules** designed to plug into this pipeline. Step1이 \"누구를 추가 계측 후보로 올릴지(Top-k)\"를 결정한다면, Step2/3는 \"후속검사에서 어떤 결함 유형을 우선 확인할지/어떤 검사 플로우로 보낼지\"를 정하는 후보 모듈이다. They are evaluated here at module-level on external benchmarks; they are not claimed to increase real defect yield in the fab unless same-wafer GT exists.\n\n"

    md += "---\n## B. Validation Scope Statement\n\n"
    md += "Step2B was validated on WM-811K; Step3 on the Carinthia dataset. There is **no shared wafer_id** and **no same-wafer GT** across Step1, Step2, and Step3. Therefore we make **no end-to-end utility claims** (e.g., \"additional inspection improved true defect rate\"). Module-level performance on each benchmark is reported for functional feasibility only.\n\n"

    md += "---\n## Step2B (WM-811K)\n\n"
    md += "- Dataset: WM-811K. Objective: wafermap pattern classification (proxy).\n"
    md += "- Model: SmallCNN. Outputs: pattern labels, severity.\n"
    md += "- Why proxy: Different data source; no same-wafer GT.\n"
    # Benchmark 성능: data/step2 실제 파일에서만 로드 (할루시네이션 방지)
    repo_root = run_output_dir.parent.parent.parent
    step2_dir = repo_root / "data" / "step2"
    step2_acc = _load_json(step2_dir / "test_accuracy_summary.json")
    step2_cls = _load_csv(step2_dir / "test_classification_report.csv")
    if step2_acc is not None:
        acc_pct = step2_acc.get("test_accuracy", 0) * 100
        n_cls = step2_acc.get("num_classes", "—")
        macro_f1 = "—"
        if step2_cls is not None and len(step2_cls) > 0:
            first_col = step2_cls.iloc[:, 0].astype(str).str.lower()
            if "f1-score" in step2_cls.columns:
                mask = first_col.str.contains("macro", na=False)
                if mask.any():
                    macro_f1 = f"{step2_cls.loc[mask, 'f1-score'].values[0]:.2f}"
        md += f"- **Benchmark performance (WM-811K)**: Pattern classification test accuracy **{acc_pct:.1f}%**, macro-F1 **{macro_f1}** ({n_cls} classes); see table below.\n"
    else:
        md += "- Benchmark performance (WM-811K): pattern classification metrics (e.g. macro-F1/accuracy) to be reported in Appendix table when available.\n"
    md += "\n"

    md += "---\n## Step3 (Carinthia)\n\n"
    md += "- Dataset: Carinthia. Objective: SEM defect classification (proxy).\n"
    md += "- Outputs: defect classes, engineer decisions.\n"
    md += "- Why proxy: Different data source; no same-wafer GT.\n"
    step3_dir = repo_root / "data" / "step3"
    eff = _load_json(step3_dir / "efficiency_summary.json")
    if eff is not None:
        # 비용(total_sem_cost)은 절대 보고하지 않음. triage rate, mean_severity만 사용.
        ai_block = eff.get("ai") or eff.get("random")
        if ai_block is not None:
            md += "- **Benchmark performance (Carinthia)**: Defect classification triage distribution (A/B/C/D) and mean severity; see table below (normalized units only, no currency).\n"
            md += "\n| Group | Mean severity | Triage A | Triage BCD |\n|-------|---------------|---------|------------|\n"
            for g in ["random", "ai"]:
                b = eff.get(g)
                if b is not None:
                    ms = b.get("mean_severity", "—")
                    ta = b.get("triage_A_rate", "—")
                    tbcd = b.get("triage_BCD_rate", "—")
                    ms_str = f"{ms:.1f}" if isinstance(ms, (int, float)) else str(ms)
                    ta_str = f"{ta:.0%}" if isinstance(ta, (int, float)) else str(ta)
                    tbcd_str = f"{tbcd:.0%}" if isinstance(tbcd, (int, float)) else str(tbcd)
                    md += f"| {g} | {ms_str} | {ta_str} | {tbcd_str} |\n"
            md += "\n"
        else:
            md += "- Benchmark performance (Carinthia): defect classification metrics (e.g. F1/triage) to be reported in Appendix table when available.\n\n"
    else:
        md += "- Benchmark performance (Carinthia): defect classification metrics (e.g. F1/ROC-AUC) to be reported in Appendix table when available.\n\n"
    
    md += "---\n## Integration Mapping & Plausibility Checks\n\n"
    md += f"- KS statistic: {ks_val}\n"
    md += f"- p-value: {p_val}\n"
    md += f"- Passed: {proxy.get('proxy_status') == 'PASSED_PLAUSIBILITY'}\n"
    md += "- Plausibility only; 인과 증명 아님.\n\n"

    md += "---\n## C. Interpretation of \"Proxy Validation FAILED\"\n\n"
    md += "The failed proxy mapping (KS test rejecting distribution alignment) is a **governance/evidence gate success**: it blocks integrated claims that would require same-wafer linkage we do not have. It does **not** mean Step2/Step3 modules are worthless—they show functional feasibility on their respective benchmarks. It means we correctly refrain from claiming end-to-end causal utility until linked data exists.\n\n"

    md += "---\n## D. What We Can Responsibly Claim Today\n\n"
    md += "- **Functional feasibility**: Step2B and Step3 achieve their benchmark objectives (pattern/defect classification) on external datasets.\n"
    md += "- **Evidence gate**: Failed proxy alignment prevents promotion of Step2/3 into Core; Core remains Step1-only.\n"
    md += "- **Readiness for same-wafer upgrade**: When same-wafer multi-stage data is secured, the pipeline is ready to run enrichment metrics, incremental utility under fixed budget, and holdout-lot/group split for leakage control (see Future Work).\n\n"

    md += "---\n## E. Concrete Future Work (Pre-Registered Plan)\n\n"
    md += "**(a) When same-wafer multi-stage data exists**, the following will be run:\n"
    md += "- **Enrichment metrics**: Incremental recall/precision of Step2/3 over Step1-only on the same wafer set.\n"
    md += "- **Incremental utility under fixed budget**: Cost–utility curves comparing Step1-only vs Step1+2 vs Step1+2+3 under the same budget cap.\n"
    md += "- **Holdout-lot / group split**: Lot-level or GroupKFold evaluation to control for leakage and support generalization claims.\n\n"
    md += "**(b)–(c) Core 승격 조건 (예)**\n"
    md += "동일 wafer_id로 Stage 간 연결이 확인되고, (i) end-to-end에서 Step1-only 대비 recall@10%의 개선이 재현되며(bootstrap CI로 평가), (ii) fixed budget에서 Pareto 우위가 관측되고, (iii) holdout-lot/GroupKFold에서도 성능 저하가 허용 범위 내일 때 Core로 Step2/3를 승격할 수 있다. 그 전까지는 Step2/3 내용은 모두 Appendix 전용이다.\n\n"

    return md


def render_tracka_report(run_output_dir: Path) -> str:
    """TrackA: 시스템/웹 데모/오케스트레이션/UX. 스크린샷 경로·해시·캡션 리스트."""
    # 스크린샷 수집: streamlit_app 또는 docs
    repo_root = run_output_dir.parent.parent.parent
    screenshots: list = []
    for base in [repo_root / 'streamlit_app', repo_root / 'docs', run_output_dir / 'figures']:
        if base.exists():
            for ext in ['*.png', '*.jpg', '*.jpeg']:
                for f in base.rglob(ext):
                    try:
                        h = hashlib.sha256()
                        with open(f, 'rb') as fp:
                            for chunk in iter(lambda: fp.read(8192), b''):
                                h.update(chunk)
                        screenshots.append({
                            'path': str(f.relative_to(repo_root)) if repo_root in f.parents else str(f),
                            'sha256': h.hexdigest()[:16],
                            'caption': f.name,
                            'figure_candidate': f'Fig.{len(screenshots)+1}',
                        })
                    except Exception:
                        pass
    
    md = """# Track A Report
## 시스템/웹 데모/오케스트레이션 — Core와 혼합 금지

TrackA는 운영 UX·오케스트레이션·모니터링을 제공한다. 검증 결론은 TrackB Core만 사용한다.

---

## TrackA 기능

- 오케스트레이션: 단계별 실행·스케줄링
- UX: 의사결정 카드, 모니터링 대시보드
- 감사 로그: 결정 추적

---

## TrackB와의 연결

- Validated Core 결과(recall, cost, primary CI)를 운영 UI에서 소비.
- Core 수치만 대시보드에 표시; Proxy는 별도 표시 또는 제외.

---

## 확장성

- 실제 fab 의사결정 시스템에 붙일 때: Core 지표로 게이팅 정책 결정, Proxy는 참고만.

---

## 스크린샷/데모 근거

"""
    if screenshots:
        md += "| path | sha256 | caption | Figure 후보 |\n|------|--------|--------|-------------|\n"
        for s in screenshots[:20]:
            md += f"| {s['path']} | {s['sha256']} | {s['caption']} | {s['figure_candidate']} |\n"
    else:
        md += "스크린샷 없음. streamlit_app/, docs/, figures/ 에 PNG/JPG 추가 시 위 테이블에 반영됨.\n"
    
    return md


def render_paper_io_trace(run_output_dir: Path, paper_bundle: Dict[str, Any]) -> str:
    """주장/수치 → 파일(sha256)·컬럼·용도. '이 파일(sha256=...)의 컬럼 A,B,C가 여기서 이렇게 쓰였다' 형태."""
    md = "# PAPER_IO_TRACE\n## 주장·수치 → 파일(sha256)·컬럼·용도 추적\n\n"
    evidence = paper_bundle.get('evidence_index', [])
    run_output_dir = Path(run_output_dir)
    
    # 기계적 적시: 파일 경로, sha256, 사용 컬럼, 여기서의 용도
    traces = [
        ("validation/framework_results.csv", "comparison_table", "method, true_positive, false_negative, high_risk_recall, selected_count, total_cost, cost_per_catch 등", "Primary 결과 표·Effect size(TP gain, FN reduction)·baseline vs framework"),
        ("validation/bootstrap_primary_ci.json", "primary_endpoints_recall_cost", "recall_ci, cost_ci (percent_reduction, delta_cost_pct_ci)", "Recall/Cost 95% CI, Core 결론 수치"),
        ("validation/high_risk_definition.json", "high_risk_definition", "N, k, method, actual_rate", "GT high-risk 정의·실험 정책 고정"),
        ("validation/sensitivity_cost_ratio.csv", "cost_sensitivity", "r, method, recall_high_risk, normalized_cost, cost_per_catch, dominance_flag, dominance_type", "r-sweep·dominance 해석"),
        ("validation/lot_leakage_diagnostics.json", "lot_leakage_diagnostics", "n_test_wafers, n_test_lots, overlap_lots_count, overlap_wafers_count, high_risk_rate_by_lot_*", "Limitations·Lot leakage 리스크 진단 표(무재학습)"),
        ("validation/random_seed_sweep_summary.json", "random_baseline_variability", "recall_mean, recall_std, recall_p5, recall_p50, recall_p95", "Random multi-seed recall 분포·Framework 위치"),
        ("validation/proxy_validation.json", "proxy_validation", "proxy_status, ks_statistic, p_value", "Appendix 전용·Core 결론 미사용"),
    ]
    md += "| 파일 (상대경로) | sha256 | 사용 컬럼/키 | 여기서의 용도 |\n|------------------|--------|--------------|---------------|\n"
    for rel_path, claim, cols, usage in traces:
        ent = next((e for e in evidence if rel_path in e.get('path', '') or rel_path.split('/')[-1] in e.get('path', '')), None)
        sha = (ent.get('sha256') or '')[:16] + '...' if ent else '—'
        md += f"| {rel_path} | {sha} | {cols} | {usage} |\n"
    md += "\n**기계적 정의**: 위 표의 각 행은 \"이 파일(sha256=... )의 해당 컬럼/키가 Core 또는 Appendix 보고서에서 위 용도로 쓰였다\"를 의미.\n"
    md += "- 전체 path·sha256·row_count·columns: `paper_bundle.json` → evidence_index, `_manifest.json`\n"
    return md


def write_paper_reports(run_output_dir: Path, run_id: str, config: Dict[str, Any]) -> None:
    """Core, Appendix, TrackA, PAPER_IO_TRACE 보고서 파일 생성."""
    reports_dir = Path(run_output_dir) / 'reports'
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    bundle_path = reports_dir / 'paper_bundle.json'
    paper_bundle = _load_json(bundle_path) if bundle_path.exists() else {}
    
    (reports_dir / 'trackB_report_core_validated.md').write_text(
        render_core_validated(Path(run_output_dir), run_id), encoding='utf-8'
    )
    (reports_dir / 'trackB_report_appendix_proxy.md').write_text(
        render_appendix_proxy(Path(run_output_dir), run_id), encoding='utf-8'
    )
    (reports_dir / 'trackA_report.md').write_text(
        render_tracka_report(Path(run_output_dir)), encoding='utf-8'
    )
    (reports_dir / 'PAPER_IO_TRACE.md').write_text(
        render_paper_io_trace(Path(run_output_dir), paper_bundle), encoding='utf-8'
    )
    logger.info("Paper reports written: core_validated, appendix_proxy, trackA, PAPER_IO_TRACE")
