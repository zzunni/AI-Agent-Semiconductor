#!/usr/bin/env python3
"""
Track B Output Verification Script
Strict verifier that exits with non-zero code on any failure.

Usage:
    python scripts/verify_outputs.py [--run_id RUN_ID] [--strict]
"""

import sys
import json
import re
import hashlib
import argparse
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np

# Configuration
TRACKB_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = TRACKB_ROOT / 'outputs'

# Required output files
REQUIRED_FILES = [
    'baselines/random_results.csv',
    'baselines/rulebased_results.csv',
    'baselines/comparison_table.csv',
    'agent/autotune_summary.json',
    'agent/autotune_history.csv',
    'agent/scheduler_log.csv',
    'agent/decision_trace.csv',
    'agent/agent_report.md',
    'validation/framework_results.csv',
    'validation/stage_breakdown.csv',
    'validation/statistical_tests.json',
    'validation/proxy_validation.json',  # CRITICAL
    'validation/validation_report.md',
    'reports/trackB_report.md',
    'reports/executive_summary.md',
    'reports/methodology.md',
    'reports/results_detailed.md',
    'reports/limitations.md',
    'reports/paper_bundle.json',
    'reports/trackB_report_core_validated.md',
    'reports/trackB_report_appendix_proxy.md',
    'reports/trackA_report.md',
    'reports/PAPER_IO_TRACE.md',
    'reports/FINAL_VALIDATION.md',
    'validation/bootstrap_primary_ci.json',
    'validation/sensitivity_cost_ratio.csv',
    '_manifest.json'
]

# Forbidden terminology
FORBIDDEN_TERMS = [
    'validated end-to-end',
    'causally proven',
    'proven on same wafers',
    'ground truth confirmed',  # if used for step2/3
]

# Required schema columns
SCHEMA_REQUIREMENTS = {
    'baselines/random_results.csv': ['lot_id', 'wafer_id', 'yield_true', 'selected'],
    'baselines/rulebased_results.csv': ['lot_id', 'wafer_id', 'yield_true', 'selected', 'riskscore'],
    'agent/scheduler_log.csv': ['wafer_id', 'decision', 'risk_score', 'budget_remaining_after'],
}


def compute_sha256(filepath: Path) -> str:
    """Compute SHA256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()


def check_required_files() -> list:
    """Check all required files exist."""
    errors = []
    for rel_path in REQUIRED_FILES:
        full_path = OUTPUT_DIR / rel_path
        if not full_path.exists():
            errors.append(f"MISSING: {rel_path}")
    return errors


def check_schema(filepath: Path, required_cols: list) -> list:
    """Check CSV schema has required columns."""
    errors = []
    try:
        df = pd.read_csv(filepath)
        missing = set(required_cols) - set(df.columns)
        if missing:
            errors.append(f"SCHEMA ERROR in {filepath.name}: missing columns {missing}")
    except Exception as e:
        errors.append(f"READ ERROR in {filepath.name}: {e}")
    return errors


def check_proxy_validation(output_dir: Path, config: dict = None) -> tuple:
    """
    Check proxy_validation.json has required fields and policy compliance.
    
    Returns:
        (errors, warnings)
    """
    errors = []
    warnings = []
    proxy_path = output_dir / 'validation' / 'proxy_validation.json'
    
    if not proxy_path.exists():
        errors.append("CRITICAL: proxy_validation.json does not exist")
        return errors, warnings
    
    try:
        with open(proxy_path, 'r') as f:
            data = json.load(f)
        
        required_fields = ['ks_statistic', 'p_value', 'proxy_status', 'interpretation']
        for field in required_fields:
            if field not in data:
                errors.append(f"proxy_validation.json missing field: {field}")
        
        # Check numeric values
        if 'ks_statistic' in data and not isinstance(data['ks_statistic'], (int, float)):
            errors.append("proxy_validation.json: ks_statistic must be numeric")
        if 'p_value' in data and not isinstance(data['p_value'], (int, float)):
            errors.append("proxy_validation.json: p_value must be numeric")
        
        # Policy enforcement
        if config:
            validation_config = config.get('validation', {})
            policy = validation_config.get('proxy_validation_policy', 'strict_fail')
            proxy_status = data.get('proxy_status', '')
            
            if proxy_status == 'FAILED_PLAUSIBILITY':
                if policy == 'strict_fail':
                    errors.append(
                        f"Proxy validation FAILED (strict_fail policy): "
                        f"KS={data.get('ks_statistic', 'N/A')}, "
                        f"p={data.get('p_value', 'N/A')}"
                    )
                else:
                    warnings.append(
                        f"Proxy validation FAILED (warn_only policy): "
                        f"KS={data.get('ks_statistic', 'N/A')}, "
                        f"p={data.get('p_value', 'N/A')}. "
                        f"Report must highlight this prominently."
                    )
            
    except json.JSONDecodeError as e:
        errors.append(f"proxy_validation.json: invalid JSON - {e}")
    
    return errors, warnings


def check_forbidden_terminology() -> list:
    """Scan reports for forbidden terminology."""
    errors = []
    reports_dir = OUTPUT_DIR / 'reports'
    
    if not reports_dir.exists():
        return errors
    
    for md_file in reports_dir.glob('*.md'):
        try:
            content = md_file.read_text(encoding='utf-8').lower()
            for term in FORBIDDEN_TERMS:
                if term.lower() in content:
                    errors.append(f"FORBIDDEN TERM '{term}' found in {md_file.name}")
        except Exception as e:
            errors.append(f"Could not read {md_file.name}: {e}")
    
    return errors


def check_manifest_sha256() -> list:
    """Check manifest includes SHA256 for all outputs."""
    errors = []
    manifest_path = OUTPUT_DIR / '_manifest.json'
    
    if not manifest_path.exists():
        errors.append("_manifest.json does not exist")
        return errors
    
    try:
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        if 'outputs' not in manifest:
            errors.append("_manifest.json missing 'outputs' section")
        else:
            # Check some outputs have sha256
            outputs = manifest['outputs']
            if isinstance(outputs, dict):
                has_sha = any('sha256' in str(v) for v in outputs.values())
                if not has_sha:
                    errors.append("_manifest.json outputs section missing SHA256 hashes")
            
    except json.JSONDecodeError as e:
        errors.append(f"_manifest.json: invalid JSON - {e}")
    
    return errors


def check_statistical_tests() -> list:
    """Verify statistical tests are correctly structured."""
    errors = []
    stats_path = OUTPUT_DIR / 'validation' / 'statistical_tests.json'
    
    if not stats_path.exists():
        errors.append("statistical_tests.json does not exist")
        return errors
    
    try:
        with open(stats_path, 'r') as f:
            data = json.load(f)
        
        # Check required tests exist
        tests = data.get('tests', {})
        required_tests = ['chi_square_detection', 'bootstrap_cost']
        for test in required_tests:
            if test not in tests:
                errors.append(f"statistical_tests.json missing test: {test}")
        
        # Check bootstrap is per-wafer (n_samples should be ~200)
        bootstrap = tests.get('bootstrap_cost', {})
        n_samples = bootstrap.get('n_samples', 0)
        if n_samples < 100:
            errors.append(f"bootstrap_cost n_samples too low ({n_samples}), should be ~200 wafers")
        
        # Check CI exists
        if 'ci_lower' not in bootstrap or 'ci_upper' not in bootstrap:
            errors.append("bootstrap_cost missing CI bounds")
            
    except json.JSONDecodeError as e:
        errors.append(f"statistical_tests.json: invalid JSON - {e}")
    
    return errors


def check_high_risk_rate(output_dir: Path, config: dict = None) -> tuple:
    """Check high-risk definition consistency."""
    errors = []
    warnings = []
    
    # Load high-risk definition
    hr_def_path = output_dir / 'validation' / 'high_risk_definition.json'
    if not hr_def_path.exists():
        warnings.append("high_risk_definition.json not found - using legacy check")
        # Fallback to legacy check
        return check_high_risk_rate_legacy(output_dir, config)
    
    try:
        with open(hr_def_path, 'r') as f:
            hr_def = json.load(f)
        
        # Verify definition is correct
        method = hr_def.get('method')
        quantile = hr_def.get('quantile', 0.20)
        k = hr_def.get('k')
        N = hr_def.get('N')
        actual_rate = hr_def.get('actual_rate')
        
        if method != 'bottom_quantile_fixed_k':
            errors.append(f"High-risk method mismatch: expected 'bottom_quantile_fixed_k', got '{method}'")
        
        expected_k = int(np.floor(quantile * N))
        if k != expected_k:
            errors.append(
                f"High-risk k mismatch: expected {expected_k} (floor({quantile}*{N})), got {k}"
            )
        
        expected_rate = quantile
        if abs(actual_rate - expected_rate) > 0.01:  # 1% tolerance
            warnings.append(
                f"High-risk rate deviation: expected {expected_rate:.1%}, got {actual_rate:.1%}"
            )
        
        # Verify it's used consistently in results
        test_file = output_dir / 'baselines' / 'random_results.csv'
        if test_file.exists():
            df = pd.read_csv(test_file)
            if 'is_high_risk' in df.columns:
                actual_hr_count = df['is_high_risk'].sum()
                if actual_hr_count != k:
                    errors.append(
                        f"High-risk count mismatch in results: expected {k}, got {actual_hr_count}"
                    )
        
    except Exception as e:
        errors.append(f"High-risk definition check failed: {e}")
    
    return errors, warnings


def check_high_risk_rate_legacy(output_dir: Path, config: dict = None) -> tuple:
    """Legacy high-risk rate check (for backwards compatibility)."""
    errors = []
    warnings = []
    
    test_file = output_dir / 'baselines' / 'random_results.csv'
    if not test_file.exists():
        return errors, warnings
    
    try:
        df = pd.read_csv(test_file)
        if 'yield_true' not in df.columns:
            return errors, warnings
        
        if config:
            data_config = config.get('data', {})
            threshold = data_config.get('high_risk_threshold', 0.6)
            expected_rate = data_config.get('expected_high_risk_rate', 0.20)
            tolerance = data_config.get('high_risk_rate_tolerance_warn', 0.10)
            policy = data_config.get('high_risk_rate_policy', 'warn_only')
            
            is_high_risk = df['yield_true'] < threshold
            actual_rate = is_high_risk.mean()
            
            if abs(actual_rate - expected_rate) > tolerance:
                msg = (
                    f"High-risk rate mismatch: actual={actual_rate:.1%} vs "
                    f"expected={expected_rate:.1%} "
                    f"(diff={abs(actual_rate - expected_rate):.1%} > tolerance={tolerance:.1%})"
                )
                if policy == 'strict_fail':
                    errors.append(msg)
                else:
                    warnings.append(msg)
    except Exception as e:
        errors.append(f"High-risk rate check failed: {e}")
    
    return errors, warnings


def check_validation_set_size(output_dir: Path, config: dict = None) -> tuple:
    """Check validation set size consistency."""
    errors = []
    warnings = []
    
    autotune_path = output_dir / 'agent' / 'autotune_summary.json'
    if not autotune_path.exists():
        return errors, warnings
    
    try:
        with open(autotune_path, 'r') as f:
            summary = json.load(f)
        
        if config:
            data_config = config.get('data', {})
            agent_config = config.get('agent', {})
            
            training_pool_size = data_config.get('training_pool_size', 1050)
            split_strategy = agent_config.get('split_strategy', 'stratified_80_20')
            
            # Check consistency
            reported_pool = summary.get('training_pool_size')
            reported_val = summary.get('optimization_validation_size')
            reported_fit = summary.get('fit_training_size')
            
            if reported_pool != training_pool_size:
                errors.append(
                    f"Training pool size mismatch: config={training_pool_size}, "
                    f"autotune_summary={reported_pool}"
                )
            
            if split_strategy == 'stratified_80_20':
                expected_fit = int(training_pool_size * agent_config.get('fit_training_fraction', 0.80))
                expected_val = training_pool_size - expected_fit
                
                if reported_fit != expected_fit:
                    warnings.append(
                        f"Fit training size mismatch: expected={expected_fit}, "
                        f"reported={reported_fit}"
                    )
                
                if reported_val != expected_val:
                    warnings.append(
                        f"Validation size mismatch: expected={expected_val}, "
                        f"reported={reported_val}"
                    )
            
            # Check test set not used
            if summary.get('test_set_used_for_optimization', False):
                errors.append("CRITICAL: Test set was used for optimization!")
                
    except Exception as e:
        errors.append(f"Validation set size check failed: {e}")
    
    return errors, warnings


def check_high_risk_count_consistency(output_dir: Path) -> tuple:
    """
    High-risk count 정합성 검증 (CRITICAL)
    
    high_risk_definition.json의 k 값이 모든 산출물에서 일치하는지 확인
    """
    errors = []
    warnings = []
    
    # Load high-risk definition
    hr_def_path = output_dir / 'validation' / 'high_risk_definition.json'
    if not hr_def_path.exists():
        errors.append("high_risk_definition.json not found")
        return errors, warnings
    
    try:
        with open(hr_def_path, 'r') as f:
            hr_def = json.load(f)
        
        expected_k = hr_def.get('k')
        if expected_k is None:
            errors.append("high_risk_definition.json에 'k' 필드가 없습니다")
            return errors, warnings
        
        # Check statistical_tests.json
        stats_path = output_dir / 'validation' / 'statistical_tests.json'
        if stats_path.exists():
            with open(stats_path, 'r') as f:
                stats_data = json.load(f)
            actual_hr = stats_data.get('high_risk_count')
            if actual_hr != expected_k:
                errors.append(
                    f"statistical_tests.json high_risk_count 불일치: "
                    f"expected={expected_k}, actual={actual_hr}"
                )
        
        # Check framework_results.csv
        framework_path = output_dir / 'validation' / 'framework_results.csv'
        if framework_path.exists():
            df = pd.read_csv(framework_path)
            if 'high_risk_count' in df.columns:
                framework_hr = df[df['method'] == 'framework']['high_risk_count'].values
                if len(framework_hr) > 0 and framework_hr[0] != expected_k:
                    errors.append(
                        f"framework_results.csv framework high_risk_count 불일치: "
                        f"expected={expected_k}, actual={framework_hr[0]}"
                    )
        
        # Check baselines
        baseline_files = [
            output_dir / 'baselines' / 'random_results.csv',
            output_dir / 'baselines' / 'rulebased_results.csv'
        ]
        for baseline_file in baseline_files:
            if baseline_file.exists():
                df = pd.read_csv(baseline_file)
                if 'is_high_risk' in df.columns:
                    actual_hr = df['is_high_risk'].sum()
                    if actual_hr != expected_k:
                        method = baseline_file.stem.replace('_results', '')
                        errors.append(
                            f"{baseline_file.name} high-risk count 불일치: "
                            f"expected={expected_k}, actual={actual_hr}"
                        )
        
        # Check trackB_report.md (spot-check)
        report_path = output_dir / 'reports' / 'trackB_report.md'
        if report_path.exists():
            content = report_path.read_text(encoding='utf-8')
            # framework 행에서 high_risk_count 찾기
            import re
            # Markdown 테이블에서 framework 행 찾기
            framework_match = re.search(r'\| framework.*?\|', content, re.DOTALL)
            if framework_match:
                framework_line = framework_match.group(0)
                # 숫자 추출 (high_risk_count 컬럼 위치 찾기)
                # 간단한 방법: | framework | 200 | (\d+) | 패턴 찾기
                hr_match = re.search(r'\| framework\s*\|\s*\d+\s*\|\s*(\d+)', framework_line)
                if hr_match:
                    reported_hr = int(hr_match.group(1))
                    if reported_hr != expected_k:
                        errors.append(
                            f"trackB_report.md framework high_risk_count 불일치: "
                            f"expected={expected_k}, actual={reported_hr}"
                        )
        
    except Exception as e:
        errors.append(f"High-risk count consistency check failed: {e}")
    
    return errors, warnings


def check_statistical_policy(output_dir: Path, config: dict = None) -> tuple:
    """Check statistical significance policy compliance."""
    errors = []
    warnings = []
    
    stats_path = output_dir / 'validation' / 'statistical_tests.json'
    if not stats_path.exists():
        return errors, warnings
    
    try:
        with open(stats_path, 'r') as f:
            data = json.load(f)
        
        if config:
            validation_config = config.get('validation', {})
            policy = validation_config.get('significance_policy', 'primary_endpoints_only')
            primary_endpoints = validation_config.get('primary_endpoints', ['high_risk_recall', 'cost_per_catch'])
            alpha = validation_config.get('alpha', 0.05)
            
            tests = data.get('tests', {})
            
            if policy == 'strict_all_p_lt_alpha':
                # All tests must be significant
                for test_name, test_result in tests.items():
                    p_value = test_result.get('p_value')
                    if p_value is not None and p_value >= alpha:
                        errors.append(
                            f"Test {test_name} not significant (p={p_value:.4f} >= alpha={alpha}) "
                            f"but policy requires all significant"
                        )
            elif policy == 'primary_endpoints_only':
                # Only primary endpoints must be significant
                # This is checked in report generation, not here
                pass
            # 'report_only' policy: no enforcement
            
    except Exception as e:
        errors.append(f"Statistical policy check failed: {e}")
    
    return errors, warnings


def resolve_run_directory(run_id: str = None) -> Path:
    """Resolve run directory from run_id or latest pointer."""
    if run_id:
        run_dir = OUTPUT_DIR / f'run_{run_id}'
        if run_dir.exists():
            return run_dir
        else:
            raise FileNotFoundError(f"Run directory not found: {run_dir}")
    
    # Try latest pointer
    latest_path = OUTPUT_DIR / 'latest'
    if latest_path.exists():
        if latest_path.is_symlink():
            target = latest_path.readlink()
            return OUTPUT_DIR / target
        elif latest_path.is_file():
            target = latest_path.read_text().strip()
            return OUTPUT_DIR / target
    
    # Fallback: use outputs/ directly (backwards compatibility)
    return OUTPUT_DIR


def load_config() -> dict:
    """Load trackb_config.json."""
    config_path = TRACKB_ROOT / 'configs' / 'trackb_config.json'
    if config_path.exists():
        with open(config_path, 'r') as f:
            return json.load(f)
    return {}


def main():
    """Main verification routine."""
    parser = argparse.ArgumentParser(description='Track B Output Verification')
    parser.add_argument('--run_id', type=str, help='Specific run ID to verify')
    parser.add_argument('--strict', action='store_true', help='Treat warnings as errors')
    args = parser.parse_args()
    
    print("=" * 60)
    print("Track B Output Verification")
    print("=" * 60)
    
    # Resolve run directory
    try:
        run_dir = resolve_run_directory(args.run_id)
        print(f"\nVerifying run directory: {run_dir}")
    except FileNotFoundError as e:
        print(f"❌ {e}")
        sys.exit(1)
    
    # Load config
    config = load_config()
    
    all_errors = []
    all_warnings = []
    
    # 1. Check required files
    print("\n[1] Checking required files...")
    errors = []
    for rel_path in REQUIRED_FILES:
        full_path = run_dir / rel_path
        if not full_path.exists():
            errors.append(f"MISSING: {rel_path}")
    all_errors.extend(errors)
    if errors:
        for e in errors:
            print(f"  ❌ {e}")
    else:
        print(f"  ✅ All {len(REQUIRED_FILES)} required files exist")
    
    # 2. Check schemas
    print("\n[2] Checking CSV schemas...")
    for rel_path, required_cols in SCHEMA_REQUIREMENTS.items():
        filepath = run_dir / rel_path
        if filepath.exists():
            errors = check_schema(filepath, required_cols)
            all_errors.extend(errors)
            if errors:
                for e in errors:
                    print(f"  ❌ {e}")
            else:
                print(f"  ✅ {rel_path} schema OK")
    # Optional: random_seed_sweep.csv schema (if present)
    sweep_path = run_dir / 'validation' / 'random_seed_sweep.csv'
    if sweep_path.exists():
        errs = check_schema(sweep_path, ['seed', 'true_positive', 'false_negative', 'recall'])
        if errs:
            all_warnings.extend(errs)
            for w in errs:
                print(f"  ⚠️  {w}")
        else:
            print(f"  ✅ validation/random_seed_sweep.csv schema OK (optional)")
    
    # 3. Check proxy_validation.json
    print("\n[3] Checking proxy_validation.json...")
    errors, warnings = check_proxy_validation(run_dir, config)
    all_errors.extend(errors)
    all_warnings.extend(warnings)
    if errors:
        for e in errors:
            print(f"  ❌ {e}")
    if warnings:
        for w in warnings:
            print(f"  ⚠️  {w}")
    if not errors and not warnings:
        print("  ✅ proxy_validation.json structure OK")
    
    # 4. Check high-risk rate
    print("\n[4] Checking high-risk rate sanity...")
    errors, warnings = check_high_risk_rate(run_dir, config)
    all_errors.extend(errors)
    all_warnings.extend(warnings)
    if errors:
        for e in errors:
            print(f"  ❌ {e}")
    if warnings:
        for w in warnings:
            print(f"  ⚠️  {w}")
    if not errors and not warnings:
        print("  ✅ High-risk rate OK")
    
    # 4b. Check high-risk count consistency (CRITICAL)
    print("\n[4b] Checking high-risk count consistency...")
    errors, warnings = check_high_risk_count_consistency(run_dir)
    all_errors.extend(errors)
    all_warnings.extend(warnings)
    if errors:
        for e in errors:
            print(f"  ❌ {e}")
    if warnings:
        for w in warnings:
            print(f"  ⚠️  {w}")
    if not errors and not warnings:
        print("  ✅ High-risk count consistent across all outputs")
    
    # 5. Check validation set size consistency
    print("\n[5] Checking validation set size consistency...")
    errors, warnings = check_validation_set_size(run_dir, config)
    all_errors.extend(errors)
    all_warnings.extend(warnings)
    if errors:
        for e in errors:
            print(f"  ❌ {e}")
    if warnings:
        for w in warnings:
            print(f"  ⚠️  {w}")
    if not errors and not warnings:
        print("  ✅ Validation set size consistent")
    
    # 6. Check forbidden terminology
    print("\n[6] Scanning for forbidden terminology...")
    errors = []
    reports_dir = run_dir / 'reports'
    if reports_dir.exists():
        for md_file in reports_dir.glob('*.md'):
            try:
                content = md_file.read_text(encoding='utf-8').lower()
                for term in FORBIDDEN_TERMS:
                    if term.lower() in content:
                        errors.append(f"FORBIDDEN TERM '{term}' found in {md_file.name}")
            except Exception as e:
                errors.append(f"Could not read {md_file.name}: {e}")
    all_errors.extend(errors)
    if errors:
        for e in errors:
            print(f"  ❌ {e}")
    else:
        print("  ✅ No forbidden terminology found")
    
    # 7. Check manifest SHA256
    print("\n[7] Checking manifest SHA256...")
    errors = []
    manifest_path = run_dir / '_manifest.json'
    if manifest_path.exists():
        try:
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
            if 'outputs' not in manifest:
                errors.append("_manifest.json missing 'outputs' section")
        except Exception as e:
            errors.append(f"_manifest.json: invalid JSON - {e}")
    all_errors.extend(errors)
    if errors:
        for e in errors:
            print(f"  ❌ {e}")
    else:
        print("  ✅ Manifest structure OK")
    
    # 8. Check statistical tests
    print("\n[8] Verifying statistical tests...")
    errors = []
    stats_path = run_dir / 'validation' / 'statistical_tests.json'
    if stats_path.exists():
        try:
            with open(stats_path, 'r') as f:
                data = json.load(f)
            tests = data.get('tests', {})
            required_tests = ['chi_square_detection', 'bootstrap_cost']
            for test in required_tests:
                if test not in tests:
                    errors.append(f"statistical_tests.json missing test: {test}")
            bootstrap = tests.get('bootstrap_cost', {})
            if bootstrap.get('n_samples', 0) < 100:
                errors.append("bootstrap_cost n_samples too low")
        except Exception as e:
            errors.append(f"statistical_tests.json: invalid JSON - {e}")
    all_errors.extend(errors)
    if errors:
        for e in errors:
            print(f"  ❌ {e}")
    else:
        print("  ✅ Statistical tests structure OK")
    
    # 9. Check statistical policy
    print("\n[9] Checking statistical policy compliance...")
    errors, warnings = check_statistical_policy(run_dir, config)
    all_errors.extend(errors)
    all_warnings.extend(warnings)
    if errors:
        for e in errors:
            print(f"  ❌ {e}")
    if warnings:
        for w in warnings:
            print(f"  ⚠️  {w}")
    if not errors and not warnings:
        print("  ✅ Statistical policy compliant")
    
    # 10. No $ in reports (cost policy: absolute $ forbidden)
    print("\n[10] Checking no $ in reports...")
    errors = []
    for name in ['trackB_report.md', 'trackB_report_core_validated.md', 'trackB_report_appendix_proxy.md',
                 'FINAL_VALIDATION.md']:
        p = run_dir / 'reports' / name
        if p.exists():
            text = p.read_text(encoding='utf-8')
            if '$' in text:
                errors.append(f"Cost policy violated: '$' found in {name}")
    # final_validation_report.json: no absolute money keys in displayed values
    fv_json = run_dir / 'reports' / 'final_validation_report.json'
    if fv_json.exists():
        try:
            fv_text = fv_json.read_text(encoding='utf-8')
            if '$' in fv_text or '달러' in fv_text or '절대금액' in fv_text or re.search(r'\d+\s*원', fv_text):
                errors.append("Cost policy: $ or absolute money term in final_validation_report.json")
        except Exception:
            pass
    all_errors.extend(errors)
    if errors:
        for e in errors:
            print(f"  ❌ {e}")
    else:
        print("  ✅ No $ in reports")
    
    # 11. If proxy FAILED: core_validated.md must not contain proxy keywords
    print("\n[11] Checking Core/Proxy separation...")
    proxy_path = run_dir / 'validation' / 'proxy_validation.json'
    core_path = run_dir / 'reports' / 'trackB_report_core_validated.md'
    proxy_failed = False
    if proxy_path.exists():
        try:
            with open(proxy_path, 'r', encoding='utf-8') as f:
                proxy_data = json.load(f)
            proxy_failed = proxy_data.get('proxy_status') == 'FAILED_PLAUSIBILITY'
        except Exception:
            pass
    errors = []
    if proxy_failed and core_path.exists():
        text = core_path.read_text(encoding='utf-8').lower()
        for kw in ['proxy', 'step2', 'step3', 'sem', 'wafer map', 'wafermap', 'wm-811k', 'carinthia', 'ks_stat', 'p_value']:
            if kw in text:
                errors.append(f"Core report must not contain proxy content: '{kw}' in trackB_report_core_validated.md")
    all_errors.extend(errors)
    if errors:
        for e in errors:
            print(f"  ❌ {e}")
    else:
        print("  ✅ Core/Proxy separation OK")
    
    # 12. Appendix must have plausibility disclaimer and FAILED banner if proxy failed
    print("\n[12] Checking appendix disclaimer...")
    appendix_path = run_dir / 'reports' / 'trackB_report_appendix_proxy.md'
    errors = []
    if appendix_path.exists():
        text = appendix_path.read_text(encoding='utf-8')
        if 'plausibility' not in text.lower():
            errors.append("Appendix must contain 'plausibility only' disclaimer")
        if proxy_failed and '주요 결론 제외' not in text and 'appendix only' not in text.lower():
            errors.append("Appendix must contain 'Appendix only' / '주요 결론 제외' when proxy FAILED")
    all_errors.extend(errors)
    if errors:
        for e in errors:
            print(f"  ❌ {e}")
    else:
        print("  ✅ Appendix disclaimer OK")
    
    # 13. paper_bundle.json schema: meta.disclaimer_current_run_only, evidence_index
    print("\n[13] Checking paper_bundle.json schema...")
    bundle_path = run_dir / 'reports' / 'paper_bundle.json'
    errors = []
    if bundle_path.exists():
        try:
            with open(bundle_path, 'r', encoding='utf-8') as f:
                bundle = json.load(f)
            if not bundle.get('meta', {}).get('disclaimer_current_run_only'):
                errors.append("paper_bundle.json missing meta.disclaimer_current_run_only")
            ev = bundle.get('evidence_index', [])
            if not ev or not isinstance(ev, list):
                errors.append("paper_bundle.json evidence_index missing or empty")
            for key in ['meta', 'system_goal', 'policies', 'pipeline', 'data', 'results', 'limitations', 'reproducibility']:
                if key not in bundle:
                    errors.append(f"paper_bundle.json missing key: {key}")
        except Exception as e:
            errors.append(f"paper_bundle.json invalid: {e}")
    all_errors.extend(errors)
    if errors:
        for e in errors:
            print(f"  ❌ {e}")
    else:
        print("  ✅ paper_bundle.json schema OK")
    
    # 14. FINAL_VALIDATION.md 존재, 판정 라벨, Current run only 문구
    print("\n[14] Checking FINAL_VALIDATION.md...")
    final_val_path = run_dir / 'reports' / 'FINAL_VALIDATION.md'
    final_val_json = run_dir / 'reports' / 'final_validation_report.json'
    errors = []
    if not final_val_path.exists():
        errors.append("reports/FINAL_VALIDATION.md missing (final comprehensive validation required)")
    else:
        text = final_val_path.read_text(encoding='utf-8')
        if 'READY_FOR_PAPER_SUBMISSION' not in text and 'READY_WITH_LIMITATIONS' not in text and 'NOT_READY' not in text:
            errors.append("FINAL_VALIDATION.md must contain verdict: READY_FOR_PAPER_SUBMISSION / READY_WITH_LIMITATIONS / NOT_READY")
        if 'Current run only' not in text and '이 실행(run_' not in text:
            errors.append("FINAL_VALIDATION.md must contain 'Current run only' or '이 실행(run_...)' disclaimer")
        # NOT_READY 판정이면 FAIL (궁극 목표 미달)
        if final_val_json.exists():
            try:
                with open(final_val_json, 'r', encoding='utf-8') as f:
                    fv = json.load(f)
                if fv.get('verdict') == 'NOT_READY':
                    errors.append("Final validation verdict is NOT_READY; policy violation or reproducibility failure")
            except Exception:
                pass
    all_errors.extend(errors)
    if errors:
        for e in errors:
            print(f"  ❌ {e}")
    else:
        print("  ✅ FINAL_VALIDATION.md present with valid verdict")
    
    # Generate verdict
    verdict = {
        'verdict': 'PASS' if not all_errors and (not args.strict or not all_warnings) else ('PASS_WITH_WARNINGS' if not all_errors else 'FAIL'),
        'failures': all_errors,
        'warnings': all_warnings,
        'run_id': run_dir.name.replace('run_', '') if 'run_' in run_dir.name else 'unknown',
        'timestamp': datetime.now().isoformat(),
        'config_sha256': None  # Could compute from config file
    }
    
    # Save verdict
    verdict_path = run_dir / 'validation' / 'verification_verdict.json'
    verdict_path.parent.mkdir(parents=True, exist_ok=True)
    with open(verdict_path, 'w', encoding='utf-8') as f:
        json.dump(verdict, f, indent=2, ensure_ascii=False)
    
    # Summary
    print("\n" + "=" * 60)
    if all_errors:
        print(f"❌ VERIFICATION FAILED: {len(all_errors)} errors found")
        print("\nErrors:")
        for i, e in enumerate(all_errors, 1):
            print(f"  {i}. {e}")
        if all_warnings:
            print(f"\n⚠️  WARNINGS ({len(all_warnings)}):")
            for i, w in enumerate(all_warnings, 1):
                print(f"  {i}. {w}")
        sys.exit(1)
    elif all_warnings:
        if args.strict:
            print(f"❌ VERIFICATION FAILED (strict mode): {len(all_warnings)} warnings treated as errors")
            print("\nWarnings:")
            for i, w in enumerate(all_warnings, 1):
                print(f"  {i}. {w}")
            sys.exit(1)
        else:
            print(f"⚠️  VERIFICATION PASSED WITH WARNINGS: {len(all_warnings)} warnings")
            print("\nWarnings:")
            for i, w in enumerate(all_warnings, 1):
                print(f"  {i}. {w}")
            sys.exit(0)
    else:
        print("✅ VERIFICATION PASSED: All checks successful")
        sys.exit(0)


if __name__ == '__main__':
    main()
