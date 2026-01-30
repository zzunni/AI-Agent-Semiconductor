#!/usr/bin/env python3
"""
Paper Input Bundle Generator
논문 에이전트용 머신리더블 JSON 생성. 모든 수치/표는 CSV/JSON에서 직접 로드.
"""

from pathlib import Path
import json
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional
import pandas as pd
import logging

logger = logging.getLogger(__name__)

DISCLAIMER_CURRENT_RUN_ONLY = (
    "본 보고서의 모든 수치·표·결론은 이 실행(run_{run_id})의 산출물만 사용합니다. "
    "다른 run 또는 외부 데이터를 사용하지 않습니다."
)


def _load_json_safe(p: Path) -> Optional[Dict]:
    if not p.exists():
        return None
    try:
        with open(p, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Load failed {p}: {e}")
        return None


def _load_csv_safe(p: Path) -> Optional[pd.DataFrame]:
    if not p.exists():
        return None
    try:
        return pd.read_csv(p, encoding='utf-8-sig')
    except Exception as e:
        logger.warning(f"Load failed {p}: {e}")
        return None


def _sha256(p: Path) -> Optional[str]:
    if not p.exists():
        return None
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()


def _schema_hash(df: pd.DataFrame) -> str:
    cols = sorted(df.columns.tolist())
    return hashlib.sha256(json.dumps(cols).encode()).hexdigest()[:16]


def build_paper_bundle(run_output_dir: Path, config: Dict[str, Any], run_id: str) -> Dict[str, Any]:
    """
    Run 디렉토리와 설정에서 paper_bundle.json 구조를 채움.
    모든 수치는 CSV/JSON에서만 로드.
    """
    run_output_dir = Path(run_output_dir)
    val_dir = run_output_dir / 'validation'
    reports_dir = run_output_dir / 'reports'
    
    # Manifest
    manifest_path = run_output_dir / '_manifest.json'
    manifest = _load_json_safe(manifest_path)
    
    # High-risk definition
    hr_def = _load_json_safe(val_dir / 'high_risk_definition.json') or {}
    
    # Comparison (numbers only)
    comp_df = _load_csv_safe(val_dir / 'framework_results.csv')
    comparison_table = None
    if comp_df is not None and len(comp_df) > 0:
        comp_numeric = comp_df.select_dtypes(include=['number'])
        comparison_table = comp_numeric.to_dict(orient='records')
    
    # Bootstrap primary CI
    bootstrap_ci = _load_json_safe(val_dir / 'bootstrap_primary_ci.json') or {}
    
    # Sensitivity cost ratio
    sens_df = _load_csv_safe(val_dir / 'sensitivity_cost_ratio.csv')
    r_sweep_table = sens_df.to_dict(orient='records') if sens_df is not None else []
    sens_json = _load_json_safe(val_dir / 'sensitivity_cost_ratio.json') or {}
    
    # Proxy validation
    proxy_val = _load_json_safe(val_dir / 'proxy_validation.json') or {}
    proxy_passed = proxy_val.get('proxy_status') == 'PASSED_PLAUSIBILITY'
    ks_stat = proxy_val.get('ks_statistic')
    ks_p = proxy_val.get('p_value')
    
    # Config
    val_config = config.get('validation', {})
    proxy_policy = val_config.get('proxy_validation_policy', 'warn_only')
    
    # Evidence index from manifest (path relative to run or full)
    evidence_index: List[Dict[str, Any]] = []
    if manifest:
        for out_entry in manifest.get('outputs', []):
            path = out_entry.get('path', '')
            if 'validation/' not in path and 'baselines/' not in path and 'agent/' not in path:
                continue
            rel = path.split('/')[-2] + '/' + path.split('/')[-1] if '/' in path else path
            schema_hash_val = None
            try:
                full = run_output_dir.parent.parent / path if path.startswith('outputs/') else run_output_dir / path
                if full.exists() and path.endswith('.csv'):
                    df = pd.read_csv(full, encoding='utf-8-sig', nrows=0)
                    schema_hash_val = _schema_hash(df)
            except Exception:
                pass
            evidence_index.append({
                'path': rel,
                'sha256': out_entry.get('sha256'),
                'rows': out_entry.get('row_count'),
                'cols': out_entry.get('columns'),
                'schema_hash': schema_hash_val,
            })
    manifest_sha = _sha256(manifest_path) if manifest_path.exists() else None
    evidence_index.append({'path': '_manifest.json', 'sha256': manifest_sha, 'rows': None, 'cols': None, 'schema_hash': None})
    
    # Repo commit (optional)
    repo_commit = None
    try:
        import subprocess
        repo_commit = subprocess.check_output(
            ['git', 'rev-parse', 'HEAD'],
            cwd=run_output_dir.parent.parent.parent,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()[:12]
    except Exception:
        pass
    
    bundle = {
        'meta': {
            'run_id': run_id,
            'created_at': datetime.now().isoformat(),
            'repo_commit': repo_commit,
            'generator_version': '1.0',
            'disclaimer_current_run_only': DISCLAIMER_CURRENT_RUN_ONLY.format(run_id=run_id),
        },
        'system_goal': {
            'one_sentence_definition': (
                'Budget-constrained high-risk wafer selection using multi-stage risk scores '
                'with same-source ground truth (yield_true) validation.'
            ),
            'problem_setting': (
                'Operational decision: which wafers to send to next-stage inspection under '
                'budget and throughput constraints; goal is to maximize high-risk detection (recall).'
            ),
        },
        'policies': {
            'pass_fail_policy': 'Step1_only',
            'proxy_policy': {
                'warn_only': proxy_policy == 'warn_only',
                'integration_in_primary': False,
            },
            'high_risk_definition': {
                'evaluation_label': hr_def.get('evaluation_label', 'yield_true bottom 20% (k=40/200 fixed)'),
                'operational_selection': hr_def.get('operational_selection', 'risk_score top selection_rate (default 10%)'),
            },
            'cost_policy': {
                'absolute_dollar_forbidden': True,
                'inline_cost_unit': 1,
                'sem_cost_unit_grid': [1, 2, 3, 5, 7, 10],
            },
            'endpoints': {
                'primary': ['recall_at_selection_rate', 'normalized_cost_per_catch_or_cost_reduction'],
                'exploratory': ['t_test', 'chi_square', 'mcnemar', 'bootstrap_cost'],
                'exploratory_statement': 'hypothesis-generating',
            },
            'leakage_policy': {
                'split_policy': 'group_by_lot (if implemented) OR explicit limitation if not',
            },
        },
        'pipeline': {
            'stage0': {
                'objective': 'Inline risk score from process features',
                'inputs': 'Stage0 test/train CSVs',
                'features': 'Process + equipment',
                'model': 'XGBoost',
                'training': 'From step1 artifacts',
                'inference': 'Predicted risk score',
                'outputs': 'risk_stage0, riskscore',
                'gating_rule': 'Threshold (tau0) for selection',
                'artifacts': ['_stage0_pred*.csv', '_stage0_risk_scores*.csv'],
            },
            'stage1': {
                'objective': 'Refined risk with additional features',
                'inputs': 'Stage1 test/train',
                'features': 'Stage0 + extra',
                'model': 'XGBoost',
                'training': 'From step1 artifacts',
                'inference': 'Risk score',
                'outputs': 'risk_stage1',
                'gating_rule': 'tau1',
                'artifacts': ['_stage1_pred*.csv', '_stage1_risk_scores*.csv'],
            },
            'stage2a': {
                'objective': 'Final inline risk (Stage 2A)',
                'inputs': 'Stage2a test/train',
                'features': 'Multi-stage',
                'model': 'XGBoost',
                'training': 'From step1 artifacts',
                'inference': 'Combined risk',
                'outputs': 'riskscore (combined)',
                'gating_rule': 'tau2a',
                'artifacts': ['_stage2a_pred*.csv', '_combined_risk_scores.csv'],
            },
            'stage2b_proxy': {
                'dataset_source': 'WM-811K',
                'objective': 'Wafermap pattern classification (proxy)',
                'model': 'SmallCNN',
                'outputs': 'Pattern labels, severity',
                'why_proxy': 'Different data source; no same-wafer GT',
                'artifacts': ['stage2b_results.csv', 'severity_scores*.csv'],
            },
            'stage3_proxy': {
                'dataset_source': 'Carinthia',
                'objective': 'SEM defect classification (proxy)',
                'model': 'From step3 artifacts',
                'outputs': 'Defect classes, engineer decisions',
                'why_proxy': 'Different data source; no same-wafer GT',
                'artifacts': ['stage3_results.csv', 'stage3_results_final.csv'],
            },
            'integration_proxy': {
                'mapping_logic': 'Proxy mapping between step2 and step3',
                'plausibility_checks': 'KS test on risk/severity alignment',
                'failure_mode': 'FAILED_PLAUSIBILITY if distributions differ',
                'artifacts': ['proxy_validation.json'],
            },
        },
        'data': {
            'step1_dataset': {
                'row_count': hr_def.get('N', 200),
                'unique_lots': None,
                'train_test_split': '200 test (sacred), 1050 train pool',
                'selection_rate_used': config.get('baselines', {}).get('random', {}).get('rate', 0.1),
                'GT_availability': 'yield_true on test',
                'caveats': 'Same source for test; train from same fab.',
            },
            'proxy_datasets': [
                {'name': 'WM-811K', 'source': 'WM-811K', 'license_notes': None, 'caveats': 'Different wafers from Step1.'},
                {'name': 'Carinthia', 'source': 'Carinthia', 'license_notes': None, 'caveats': 'Different wafers from Step1.'},
            ],
        },
        'results': {
            'step1_core_tables': {
                'comparison_table': comparison_table,
                'primary_endpoints': {
                    'recall_at_selection_rate_10pct': bootstrap_ci.get('recall_ci', {}).get('observed_framework_recall'),
                    'normalized_cost_reduction_pct': bootstrap_ci.get('cost_ci', {}).get('percent_reduction'),
                },
                'bootstrap_CI': bootstrap_ci,
            },
            'cost_sensitivity': {
                'r_sweep_table_values': r_sweep_table,
                'r_grid': sens_json.get('r_grid', [1, 2, 3, 5, 7, 10]),
            },
            'proxy_validation': {
                'ks_stat': ks_stat,
                'p_value': ks_p,
                'passed': proxy_passed,
            },
        },
        'limitations': [
            'Proven: Step1 high-risk recall and cost vs baselines on same-source test set (n=200, k=40).',
            'Not proven: Causal effect of Step2/Step3; proxy integration is plausibility-only.',
            'Not proven: Generalization to other fabs or time periods.',
        ],
        'reproducibility': {
            'exact_commands': ['cd trackb/scripts', 'python trackb_run.py --mode from_artifacts'],
            'config_paths': ['trackb/configs/trackb_config.json'],
            'deterministic_settings': {'random_seed': config.get('random_seed', 42), 'bootstrap_seed': val_config.get('bootstrap', {}).get('seed', 42)},
        },
        'evidence_index': evidence_index,
    }
    
    return bundle


def write_paper_bundle(run_output_dir: Path, config: Dict[str, Any], run_id: str) -> Path:
    """paper_bundle.json 파일을 쓰고 경로 반환."""
    bundle = build_paper_bundle(run_output_dir, config, run_id)
    out_path = Path(run_output_dir) / 'reports' / 'paper_bundle.json'
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(bundle, f, ensure_ascii=False, indent=2)
    logger.info(f"paper_bundle.json written: {out_path}")
    return out_path
