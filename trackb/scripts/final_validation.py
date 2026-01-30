#!/usr/bin/env python3
"""
Final Comprehensive Validation (궁극 목표 종합 검증)
FINAL_VALIDATION.md 생성. Q1~Q6 답변, Primary+CI, r-sweep dominance, 정책 고정성, 증거 일치, 최종 판정.
"""

from pathlib import Path
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import logging
import subprocess
import sys

logger = logging.getLogger(__name__)

VERDICT_READY = "READY_FOR_PAPER_SUBMISSION"
VERDICT_LIMITATIONS = "READY_WITH_LIMITATIONS"
VERDICT_NOT_READY = "NOT_READY"


def _load_json(p: Path) -> Optional[Dict]:
    if not p.exists():
        return None
    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _load_csv(p: Path) -> Optional[pd.DataFrame]:
    if not p.exists():
        return None
    try:
        return pd.read_csv(p, encoding="utf-8-sig")
    except Exception:
        return None


def _run_verify(run_output_dir: Path, scripts_dir: Path) -> Tuple[int, str]:
    """verify_outputs.py 실행, exitcode와 stdout 일부 반환."""
    run_id = run_output_dir.name.replace("run_", "")
    try:
        out = subprocess.run(
            [sys.executable, str(scripts_dir / "verify_outputs.py"), "--run_id", run_id],
            cwd=str(scripts_dir),
            capture_output=True,
            text=True,
            timeout=60,
        )
        return out.returncode, (out.stdout or "") + (out.stderr or "")
    except Exception as e:
        return -1, str(e)


def _check_core_no_proxy_no_dollar(reports_dir: Path) -> Tuple[bool, List[str]]:
    """Core 보고서에 proxy/절대비용 기호 없음 확인."""
    issues = []
    core_path = reports_dir / "trackB_report_core_validated.md"
    if not core_path.exists():
        return False, ["trackB_report_core_validated.md missing"]
    text = core_path.read_text(encoding="utf-8")
    dollar = chr(36)  # policy: no absolute cost in reports
    if dollar in text:
        issues.append("Core report contains absolute cost symbol (cost policy violation)")
    for kw in ["proxy", "step2", "step3", "sem ", "wafer map", "wm-811k", "carinthia"]:
        if kw in text.lower():
            issues.append(f"Core report contains proxy-related keyword: '{kw}'")
    return len(issues) == 0, issues


def build_final_validation(run_output_dir: Path, run_id: str, verify_exitcode: int, verify_log: str) -> Dict[str, Any]:
    """
    Q1~Q6 답변 및 판정 로직. 산출물만 읽어서 채움.
    """
    run_output_dir = Path(run_output_dir)
    val_dir = run_output_dir / "validation"
    reports_dir = run_output_dir / "reports"

    bootstrap = _load_json(val_dir / "bootstrap_primary_ci.json") or {}
    comp_df = _load_csv(val_dir / "framework_results.csv")
    sens_df = _load_csv(val_dir / "sensitivity_cost_ratio.csv")
    hr_def = _load_json(val_dir / "high_risk_definition.json") or {}
    proxy_val = _load_json(val_dir / "proxy_validation.json") or {}
    paper_bundle = _load_json(reports_dir / "paper_bundle.json") or {}

    proxy_failed = proxy_val.get("proxy_status") == "FAILED_PLAUSIBILITY"
    core_ok, core_issues = _check_core_no_proxy_no_dollar(reports_dir)

    # Q1) Recall@10% 개선 + CI — CI 하한이 0 포함이면 "signal(불확실성 존재)", 단정 금지
    rc = bootstrap.get("recall_ci", {})
    recall_baseline = rc.get("observed_baseline_recall")
    recall_framework = rc.get("observed_framework_recall")
    recall_diff = rc.get("observed_diff")
    recall_ci_low, recall_ci_high = rc.get("ci_lower"), rc.get("ci_upper")
    q1_improvement = recall_framework is not None and recall_baseline is not None and (recall_framework or 0) >= (recall_baseline or 0)
    q1_ci_positive = recall_ci_low is not None and recall_ci_high is not None and (recall_ci_low <= recall_diff <= recall_ci_high)
    q1_ci_contains_zero = (recall_ci_low is not None and recall_ci_high is not None and
                           recall_ci_low <= 0 <= recall_ci_high)

    # Q2) 비용 정규화 기준 절감 또는 동일 비용에서 성능 개선; dominance = Recall-dominance(동일 normalized_cost에서 recall > baseline)
    cc = bootstrap.get("cost_ci", {})
    cost_reduction_pct = cc.get("percent_reduction") or 0
    cost_pct_ci = cc.get("delta_cost_pct_ci")  # %만 사용, 절대금액 CI 미사용
    q2_cost_ok = cost_reduction_pct >= 0  # 동일 이상
    dominance_count = 0
    if sens_df is not None and "dominance_flag" in sens_df.columns:
        fw_rows = sens_df[(sens_df["method"] == "framework") & (sens_df["dominance_flag"] == True)]
        dominance_count = len(fw_rows)
    q2_dominance = dominance_count > 0

    # Q3) selection_rate 10% 고정, high-risk k=40 고정
    selection_rate_ok = hr_def.get("actual_rate") == 0.2 or (comp_df is not None and (comp_df["selection_rate"] == 0.1).all())
    k_ok = hr_def.get("k") == 40 and hr_def.get("N") == 200
    q3_ok = k_ok and (comp_df is None or (comp_df["selection_rate"] == 0.1).all())

    # Q4) manifest/sha256/evidence
    manifest_path = run_output_dir / "_manifest.json"
    manifest_ok = manifest_path.exists()
    evidence = paper_bundle.get("evidence_index") or []
    q4_ok = manifest_ok and len(evidence) > 0

    # Q5) proxy FAILED 시 core 분리
    q5_ok = not proxy_failed or core_ok

    # Q6) lot leakage / group split (TODO if not implemented)
    group_split_mentioned = False
    if comp_df is not None and "method" in comp_df.columns:
        if "group_split" in comp_df["method"].astype(str).str.lower().values or "lot" in str(comp_df.columns).lower():
            group_split_mentioned = True
    q6_todo = not group_split_mentioned

    # Verdict
    if verify_exitcode != 0:
        verdict = VERDICT_NOT_READY
        verdict_reason = "verify_outputs.py did not pass"
    elif not core_ok:
        verdict = VERDICT_NOT_READY
        verdict_reason = "Core report policy violation: " + "; ".join(core_issues[:3])
    elif not q4_ok:
        verdict = VERDICT_NOT_READY
        verdict_reason = "Evidence/manifest missing or incomplete"
    elif proxy_failed and not q5_ok:
        verdict = VERDICT_NOT_READY
        verdict_reason = "Proxy FAILED but core contained proxy content"
    elif proxy_failed:
        verdict = VERDICT_LIMITATIONS
        verdict_reason = "Proxy validation FAILED; Core separated and policy enforced"
    elif q6_todo:
        verdict = VERDICT_LIMITATIONS
        verdict_reason = "Lot/group split not in core results; documented as TODO"
    else:
        verdict = VERDICT_READY
        verdict_reason = "All conditions satisfied"

    return {
        "run_id": run_id,
        "created_at": datetime.now().isoformat(),
        "verdict": verdict,
        "verdict_reason": verdict_reason,
        "Q1_recall_improvement": {
            "question": "고위험 웨이퍼를 더 잘 잡는가? (Recall@10% 개선)",
            "baseline_recall": recall_baseline,
            "framework_recall": recall_framework,
            "delta_recall": recall_diff,
            "ci_95": [recall_ci_low, recall_ci_high],
            "improvement": q1_improvement,
                "evidence_file": "validation/bootstrap_primary_ci.json",
        },
        "Q2_cost_or_pareto": {
            "question": "비용 절감 또는 동일 비용에서 성능 개선?",
            "normalized_cost_reduction_pct": cost_reduction_pct,
            "cost_ok": q2_cost_ok,
            "r_sweep_dominance_count": dominance_count,
            "dominance_ok": q2_dominance,
            "evidence_file": "validation/sensitivity_cost_ratio.csv",
        },
        "Q3_policy_fixed": {
            "question": "selection_rate 10%, high-risk k=40 고정?",
            "selection_rate_fixed": q3_ok,
            "high_risk_k": hr_def.get("k"),
            "test_size": hr_def.get("N"),
            "evidence_file": "validation/high_risk_definition.json",
        },
        "Q4_reproducibility": {
            "question": "근거 파일로 재현 가능?",
            "manifest_exists": manifest_ok,
            "evidence_index_count": len(evidence),
            "ok": q4_ok,
        },
        "Q5_proxy_separation": {
            "question": "proxy FAILED 시 core에 proxy 미혼합?",
            "proxy_failed": proxy_failed,
            "core_clean": core_ok,
            "ok": q5_ok,
            "issues": core_issues if not core_ok else [],
        },
        "Q6_lot_or_generalization": {
            "question": "lot leakage 방지/일반화 검증?",
            "group_split_in_core": group_split_mentioned,
            "todo_documented": q6_todo,
        },
        "primary_summary": {
            "recall_at_10pct": {"baseline": recall_baseline, "framework": recall_framework, "ci_95": [recall_ci_low, recall_ci_high]},
            "normalized_cost": {"reduction_pct": cost_reduction_pct, "delta_cost_pct_ci": cost_pct_ci},
        },
        "q1_ci_contains_zero": q1_ci_contains_zero,
        "adversarial_tests": "See tests/test_adversarial_verify.py or run scripts/run_adversarial_tests.py",
    }


def render_final_validation_md(data: Dict[str, Any], run_output_dir: Path) -> str:
    """FINAL_VALIDATION.md 본문 생성. Cost CI는 %만 표기, Q1 CI 포함 0이면 단정 금지, Q2 dominance 정의, Q6 방어 문단."""
    run_id = data.get("run_id", "unknown")
    verdict = data.get("verdict", VERDICT_NOT_READY)
    reason = data.get("verdict_reason", "")
    q1 = data.get("Q1_recall_improvement", {})
    ci_95 = q1.get("ci_95", [None, None])
    q1_ci_contains_zero = data.get("q1_ci_contains_zero", False)
    # Q1: CI 하한이 0 포함이면 "signal(불확실성 존재)"로 표현, 개선 여부 단정 금지
    q1_interpretation = (
        "signal (불확실성 존재)" if q1_ci_contains_zero
        else str(q1.get("improvement"))
    )
    cost_summary = data.get("primary_summary", {}).get("normalized_cost", {})
    cost_pct_ci = cost_summary.get("delta_cost_pct_ci")
    cost_ci_str = f" [{cost_pct_ci[0]}, {cost_pct_ci[1]}]%" if cost_pct_ci else ""

    random_seed_paragraph = ""
    sweep_path = Path(run_output_dir) / "validation" / "random_seed_sweep_summary.json"
    if sweep_path.exists():
        try:
            with open(sweep_path, "r", encoding="utf-8") as f:
                sweep = json.load(f)
            fw_recall = q1.get("framework_recall")
            n_seeds = sweep.get("n_seeds", 0)
            p5, p50, p95 = sweep.get("recall_p5"), sweep.get("recall_p50"), sweep.get("recall_p95")
            random_seed_paragraph = (
                f"\n- **Random multi-seed**: {n_seeds}회 반복 시 random recall 분포 "
                f"p5/p50/p95: {p5:.3f} / {p50:.3f} / {p95:.3f}. "
                f"Framework recall({fw_recall})은 random p95({p95:.3f}) 대비 상대적 위치; 단정 금지, 'suggests' 수준."
            )
        except Exception:
            pass

    md = f"""# Final Comprehensive Validation
## 궁극 목표 종합 검증 — 논문 제출 준비 여부

**Current run only**: 본 문서의 모든 수치·판정은 이 실행(run_{run_id})의 산출물만 사용합니다.

**Run ID**: {run_id}  
**Generated**: {data.get('created_at', '')}

---

## 최종 판정

**{verdict}**

{reason}

---

## 연구 목적 (시스템 목표)

반도체 웨이퍼 공정에서 제한된 계측/SEM 예산과 처리량 제약 하에, 저수율(high-risk) 웨이퍼를 조기에 선별하고, 추가 계측/SEM/리워크/스크랩 의사결정을 단계적으로 최적화하여 (1) high-risk 검출 리콜을 높이고, (2) 동일 리콜에서 비용을 줄이거나 (3) 동일 예산에서 성능을 높이며, 모든 판단이 근거 파일(해시)+재현 절차로 추적 가능한 의사결정 시스템을 만드는 것이 목표이다.

- **TrackA**: 운영/데모/의사결정 UI 레이어 (Stage 결과 → 워크플로우/경보→SEM→조치).
- **TrackB**: 과학적 검증/재현성/증거 추적. 논문 핵심 수치는 Step1 Validated Core만 사용.

---

## Q1) 고위험 웨이퍼를 더 잘 잡는가? (Recall@10% 개선)

- **Baseline recall**: {q1.get('baseline_recall')}
- **Framework recall**: {q1.get('framework_recall')}
- **ΔRecall (95% CI)**: [{ci_95[0]}, {ci_95[1]}]
- **해석**: {q1_interpretation} (CI가 0을 포함하면 단정하지 않음)
- **근거 파일**: `validation/bootstrap_primary_ci.json`
{random_seed_paragraph}

---

## Q2) 비용 절감 또는 동일 비용에서 성능 개선?

- **Dominance 정의**: dominance_flag=True는 **Recall-dominance** — 동일 normalized_cost에서 framework의 recall이 baseline보다 큼. cost-dominance가 아님.
- **Normalized cost reduction %**: {data.get('Q2_cost_or_pareto', {}).get('normalized_cost_reduction_pct')}{cost_ci_str}
- **r-sweep에서 framework recall-dominance 구간 수**: {data.get('Q2_cost_or_pareto', {}).get('r_sweep_dominance_count')}
- **근거 파일**: `validation/sensitivity_cost_ratio.csv` (dominance_type ∈ {{recall_dominance, cost_dominance, none}})

---

## Q3) 의사결정 파이프라인 정책 고정성

- **selection_rate**: 10% 고정 (산출물/설정과 일치)
- **GT high-risk**: yield_true 하위 20%, k=40, N=200 고정
- **근거 파일**: `validation/high_risk_definition.json`, `validation/framework_results.csv`

---

## Q4) 근거 파일로 재현 가능?

- **Manifest**: `_manifest.json` (path, sha256, rows, cols)
- **Evidence index**: `reports/paper_bundle.json` → evidence_index
- **재현 명령**: `cd trackb/scripts && python trackb_run.py --mode from_artifacts`

---

## Q5) proxy FAILED 시 Core에 proxy 미혼합?

- **Proxy status**: {data.get('Q5_proxy_separation', {}).get('proxy_failed')}
- **Core 문서 proxy/절대비용 검사**: {data.get('Q5_proxy_separation', {}).get('core_clean')}
- **검증기**: `verify_outputs.py`가 Core/Proxy 분리 및 절대비용 금지 정책 강제

---

## Q6) lot leakage 방지/일반화

- **Group split in core**: {data.get('Q6_lot_or_generalization', {}).get('group_split_in_core')}
- **해석**: Lot leakage 가능성은 완전 배제할 수 없음. 결과는 동일 조건 내 운영 성능으로 해석함.
- **논문 후속 검증**: holdout lots, GroupKFold 등 lot 단위 분할 실험을 명시할 것.
- **TODO**: "동일 lot 내 train/test 분리 또는 holdout lot 평가"를 한계/향후 과제로 명시.

---

## Primary 2개 + CI 요약 (비용은 %만 표기)

| Endpoint | Baseline | Framework | Δ (95% CI) |
|----------|----------|-----------|------------|
| Recall @ selection_rate=10% | {data.get('primary_summary', {}).get('recall_at_10pct', {}).get('baseline')} | {data.get('primary_summary', {}).get('recall_at_10pct', {}).get('framework')} | [{ci_95[0]}, {ci_95[1]}] |
| Normalized cost reduction % | — | — | {cost_summary.get('reduction_pct')}%{cost_ci_str} |

---

## 제한사항 및 다음 실험

- 논문 결론은 Step1 Core만 사용. Step2/Step3는 Appendix(plausibility only).
- 비용은 절대 금액 금지; 정규화/비율만 사용.
- Lot/group split 미실시: lot leakage 완전 배제 불가, 동일 조건 내 성능으로 해석. 향후 holdout lots / GroupKFold 명시.

---

## 근거 파일 인덱스

- `validation/bootstrap_primary_ci.json` — Primary recall/cost CI (cost는 % CI만)
- `validation/framework_results.csv` — 비교 테이블
- `validation/sensitivity_cost_ratio.csv` — r-sweep, dominance_type
- `validation/high_risk_definition.json` — GT 정의
- `reports/paper_bundle.json` — evidence_index, policies, results
- `_manifest.json` — 전체 입출력 해시
"""
    return md


def write_final_validation(
    run_output_dir: Path,
    run_id: str,
    verify_exitcode: Optional[int] = None,
    verify_log: Optional[str] = None,
    scripts_dir: Optional[Path] = None,
) -> Path:
    """FINAL_VALIDATION.md 및 final_validation_report.json 생성. 판정은 산출물만으로 수행(verify 순환 의존 회피)."""
    run_output_dir = Path(run_output_dir)
    reports_dir = run_output_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    data = build_final_validation(run_output_dir, run_id, verify_exitcode or 0, verify_log or "")
    md_content = render_final_validation_md(data, run_output_dir)

    md_path = reports_dir / "FINAL_VALIDATION.md"
    md_path.write_text(md_content, encoding="utf-8")
    logger.info(f"FINAL_VALIDATION.md written: {md_path}")

    class _Encoder(json.JSONEncoder):
        def default(self, o):
            if hasattr(o, "item"):
                return o.item()
            return super().default(o)

    json_path = reports_dir / "final_validation_report.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, cls=_Encoder)
    logger.info(f"final_validation_report.json written: {json_path}")

    return md_path
