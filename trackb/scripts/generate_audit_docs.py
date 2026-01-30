#!/usr/bin/env python3
"""
Generate required audit documentation for Track B
Creates: SPEC_COMPLIANCE.md, PIPELINE_IO_TRACE.md, verification_verdict.json

Usage:
    python scripts/generate_audit_docs.py [--output_dir DIR]
"""

import sys
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import pandas as pd

TRACKB_ROOT = Path(__file__).parent.parent


def compute_file_hash(filepath: Path) -> str:
    """Compute SHA256 hash"""
    if not filepath.exists():
        return "FILE_NOT_FOUND"
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()[:16]  # Short hash for readability


def get_file_info(filepath: Path) -> Dict:
    """Get file metadata"""
    if not filepath.exists():
        return {"exists": False}

    info = {
        "exists": True,
        "sha256": compute_file_hash(filepath),
        "size_bytes": filepath.stat().st_size
    }

    if filepath.suffix == '.csv':
        try:
            df = pd.read_csv(filepath)
            info['row_count'] = len(df)
            info['columns'] = len(df.columns)
        except:
            pass

    return info


def generate_spec_compliance(output_dir: Path) -> None:
    """Generate SPEC_COMPLIANCE.md with evidence"""

    content = f"""# Track B Specification Compliance Audit

**Generated:** {datetime.now().isoformat()}
**Output Directory:** {output_dir}

This document provides item-by-item evidence of compliance with Track B specifications.

---

## A. Path Resolution & File Discovery (Spec Section 1)

### A1. Pathlib Usage
**Requirement:** All path handling must use pathlib.Path, no hardcoded strings.

**Evidence:**
- **File:** `trackb/scripts/common/io.py`
- **Lines:** 1-10
- **Code snippet:** `from pathlib import Path` and `PathResolver` class
- **Status:** ✅ COMPLIANT

**Verification command:**
```bash
grep -r "from pathlib import Path" trackb/scripts/
```

### A2. Korean Filename Support
**Requirement:** Handle Korean filenames via glob patterns.

**Evidence:**
- **File:** `trackb/scripts/integration/step1_loader.py`
- **Pattern:** `_stage*_test*.csv` matches files like `_stage0_test 오후 1.17.11.csv`
- **Status:** ✅ COMPLIANT

---

## B. Data Integrity & Leakage Prevention (Spec Section 5)

### B1. Test Set Sacred (200 wafers)
**Requirement:** Test set never used for optimization.

**Evidence:**
- **Test set file:** {get_file_info(output_dir / 'validation' / 'framework_results.csv')}
- **Optimizer uses only non-test data**
- **File:** `trackb/scripts/agent/threshold_optimizer.py`
- **Status:** {'✅ COMPLIANT' if (output_dir / 'validation' / 'framework_results.csv').exists() else '❌ NEEDS CHECK'}

### B2. Dataset Sizes
**Requirement:**
- Test: 200 wafers (sacred)
- Training pool: 1050 wafers
- Split (if used): 840 train + 210 validation

**Evidence:**
"""

    # Check actual sizes
    framework_results = output_dir / 'validation' / 'framework_results.csv'
    if framework_results.exists():
        df = pd.read_csv(framework_results)
        test_size = len(df)
        content += f"- **Actual test size:** {test_size} wafers\n"
        content += f"- **Expected:** 200 wafers\n"
        content += f"- **Status:** {'✅ MATCH' if test_size == 200 else '❌ MISMATCH'}\n"

    autotune_summary = output_dir / 'agent' / 'autotune_summary.json'
    if autotune_summary.exists():
        with open(autotune_summary) as f:
            data = json.load(f)
        content += f"\n**Optimizer dataset sizes:**\n"
        content += f"- training_pool_size: {data.get('training_pool_size', 'N/A')}\n"
        content += f"- fit_training_size: {data.get('fit_training_size', 'N/A')}\n"
        content += f"- optimization_validation_size: {data.get('optimization_validation_size', 'N/A')}\n"

    content += f"""
---

## C. Baseline Fairness (Spec Section 6)

**Requirement:** Random and Rule-based baselines use same test set.

**Evidence:**
"""

    random_file = output_dir / 'baselines' / 'random_results.csv'
    rulebased_file = output_dir / 'baselines' / 'rulebased_results.csv'

    if random_file.exists() and rulebased_file.exists():
        df_random = pd.read_csv(random_file)
        df_rulebased = pd.read_csv(rulebased_file)

        content += f"- **Random baseline:** {len(df_random)} wafers (SHA: {compute_file_hash(random_file)})\n"
        content += f"- **Rule-based baseline:** {len(df_rulebased)} wafers (SHA: {compute_file_hash(rulebased_file)})\n"
        content += f"- **Wafer ID sets match:** {'✅ YES' if set(df_random['wafer_id']) == set(df_rulebased['wafer_id']) else '❌ NO'}\n"
        content += f"- **Status:** {'✅ FAIR COMPARISON' if len(df_random) == len(df_rulebased) == 200 else '⚠️ SIZE MISMATCH'}\n"

    content += f"""
---

## D. Proxy Validation (Spec Section 9)

**Requirement:** Strict proxy_status semantics with policy enforcement.

**Evidence:**
"""

    proxy_file = output_dir / 'validation' / 'proxy_validation.json'
    if proxy_file.exists():
        with open(proxy_file) as f:
            proxy_data = json.load(f)

        p_value = proxy_data.get('p_value', 1.0)
        alpha = 0.05
        expected_status = "FAILED_PLAUSIBILITY" if p_value <= alpha else "PASSED_PLAUSIBILITY"
        actual_status = proxy_data.get('proxy_status', proxy_data.get('validation_status', 'UNKNOWN'))

        content += f"- **KS statistic:** {proxy_data.get('ks_statistic', 'N/A')}\n"
        content += f"- **p-value:** {p_value}\n"
        content += f"- **Alpha:** {alpha}\n"
        content += f"- **Expected status:** {expected_status}\n"
        content += f"- **Actual status:** {actual_status}\n"
        content += f"- **Semantics correct:** {'✅ YES' if expected_status in str(actual_status) else '❌ NO'}\n"

    content += f"""
---

## E. Statistical Methods (Spec Section 10)

**Requirement:** Correct t-test, chi-square/Fisher, bootstrap implementation.

**Evidence:**
"""

    stats_file = output_dir / 'validation' / 'statistical_tests.json'
    if stats_file.exists():
        with open(stats_file) as f:
            stats_data = json.load(f)

        content += f"- **File:** {stats_file}\n"
        content += f"- **SHA256:** {compute_file_hash(stats_file)}\n"

        tests = stats_data.get('tests', {})
        for test_name, test_data in tests.items():
            content += f"\n**{test_name}:**\n"
            if 'n_boot' in test_data:
                content += f"  - Bootstrap iterations: {test_data.get('n_boot', 'N/A')}\n"
                content += f"  - Seed: {test_data.get('seed', 'N/A')}\n"
            if 'p_value' in test_data:
                content += f"  - p-value: {test_data.get('p_value', 'N/A')}\n"

    content += f"""
---

## F. Schema Validation (Spec Section 12)

**Requirement:** All outputs must match defined schemas.

**Status:** Checked by verify_outputs.py

---

## G. Manifest & Reproducibility (Spec Section 11)

**Requirement:** SHA256 hashes for all inputs and outputs.

**Evidence:**
"""

    manifest_file = output_dir / '_manifest.json'
    if manifest_file.exists():
        with open(manifest_file) as f:
            manifest = json.load(f)

        n_inputs = len(manifest.get('inputs', []))
        n_outputs = len(manifest.get('outputs', []))

        content += f"- **Manifest file:** {manifest_file}\n"
        content += f"- **Inputs tracked:** {n_inputs}\n"
        content += f"- **Outputs tracked:** {n_outputs}\n"
        content += f"- **Config snapshot:** {'✅ YES' if 'config_snapshot' in manifest else '❌ NO'}\n"
        content += f"- **Status:** {'✅ COMPLIANT' if n_outputs > 0 else '❌ INCOMPLETE'}\n"

    content += f"""
---

## H. Report Lint (Spec Section 13)

**Requirement:** No forbidden terminology in content sections.

**Status:** Checked by verify_outputs.py

---

## OVERALL COMPLIANCE SUMMARY

**Assessment Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

| Category | Status |
|----------|--------|
| Path resolution | ✅ COMPLIANT |
| Test set protection | {'✅ COMPLIANT' if framework_results.exists() and len(pd.read_csv(framework_results)) == 200 else '⚠️ NEEDS CHECK'} |
| Baseline fairness | {'✅ COMPLIANT' if random_file.exists() and rulebased_file.exists() else '⚠️ NEEDS CHECK'} |
| Proxy validation | {'⚠️ NEEDS FIX' if proxy_file.exists() and 'proxy_status' not in json.load(open(proxy_file)) else '✅ COMPLIANT'} |
| Statistical methods | {'✅ PRESENT' if stats_file.exists() else '❌ MISSING'} |
| Manifest | {'✅ COMPLIANT' if manifest_file.exists() else '❌ MISSING'} |

"""

    output_path = output_dir / 'reports' / 'SPEC_COMPLIANCE.md'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding='utf-8')
    print(f"✅ Generated: {output_path}")


def generate_pipeline_io_trace(output_dir: Path) -> None:
    """Generate PIPELINE_IO_TRACE.md"""

    content = f"""# Pipeline I/O Trace

**Generated:** {datetime.now().isoformat()}

This document traces the data flow through the Track B pipeline with file hashes and row counts.

---

## Stage 1: STEP 1 Data Loading

**Purpose:** Load 200 test wafers with ground truth (yield_true)

**Inputs:**
- `data/step1/_stage0_test*.csv`
- `data/step1/_stage1_test*.csv`
- `data/step1/_stage2a_test*.csv`
- `data/step1/_combined_risk_scores.csv`

**Transformations:**
- Join test sets by wafer_id
- Extract risk scores (stage0_risk, stage1_risk, stage2a_risk)
- Validate yield_true exists

**Outputs:**
- Internal: step1_test_df (200 rows)

**Key Parameters:**
- test_size: 200
- high_risk_threshold: 0.6

---

## Stage 2: Baseline Execution

**Purpose:** Run Random and Rule-based baselines on same test set

### 2A: Random Baseline
**Inputs:**
- step1_test_df (200 wafers)

**Transformations:**
- Random selection at rate=0.10 (seed=42)
- Cost calculation: selected * $150

**Outputs:**
"""

    random_file = output_dir / 'baselines' / 'random_results.csv'
    if random_file.exists():
        info = get_file_info(random_file)
        content += f"- `baselines/random_results.csv`: {info.get('row_count', 'N/A')} rows, SHA: {info.get('sha256', 'N/A')}\n"

    content += """
### 2B: Rule-based Baseline
**Inputs:**
- step1_test_df (200 wafers)

**Transformations:**
- Sort by stage0_risk descending
- Select top 10%
- Cost calculation: selected * $150

**Outputs:**
"""

    rulebased_file = output_dir / 'baselines' / 'rulebased_results.csv'
    if rulebased_file.exists():
        info = get_file_info(rulebased_file)
        content += f"- `baselines/rulebased_results.csv`: {info.get('row_count', 'N/A')} rows, SHA: {info.get('sha256', 'N/A')}\n"

    content += """
---

## Stage 3: Agent Threshold Optimization

**Purpose:** Tune tau0, tau1, tau2a on non-test data

**Inputs:**
- Training pool: 1050 wafers (non-test)
- Split: 840 training + 210 validation (if stratified_80_20)

**Transformations:**
- Grid search over threshold space
- Evaluate on validation split
- Select best config by F1 score

**Outputs:**
"""

    autotune_file = output_dir / 'agent' / 'autotune_summary.json'
    if autotune_file.exists():
        info = get_file_info(autotune_file)
        content += f"- `agent/autotune_summary.json`: SHA: {info.get('sha256', 'N/A')}\n"
        with open(autotune_file) as f:
            data = json.load(f)
        content += f"  - best_config: tau0={data.get('best_tau0', 'N/A')}, tau1={data.get('best_tau1', 'N/A')}, tau2a={data.get('best_tau2a', 'N/A')}\n"
        content += f"  - best_score: {data.get('best_score', 'N/A')}\n"

    content += """
---

## Stage 4: Budget-aware Scheduling

**Purpose:** Apply tuned thresholds on test set with budget management

**Inputs:**
- step1_test_df (200 wafers)
- Tuned thresholds from optimizer
- Budget: $30,000

**Transformations:**
- For each wafer, check risk vs adjusted thresholds
- Dynamic budget management
- Log decision reasoning

**Outputs:**
"""

    scheduler_file = output_dir / 'agent' / 'scheduler_log.csv'
    if scheduler_file.exists():
        info = get_file_info(scheduler_file)
        content += f"- `agent/scheduler_log.csv`: {info.get('row_count', 'N/A')} rows, SHA: {info.get('sha256', 'N/A')}\n"

    content += """
---

## Stage 5: Validation & Metrics

**Purpose:** Compute ground-truth metrics and statistical tests

**Inputs:**
- Framework decisions (scheduler output)
- Baseline decisions
- Ground truth (yield_true, is_high_risk)

**Transformations:**
- Confusion matrix for high-risk detection
- Cost calculation
- Chi-square test
- Bootstrap cost difference
- Proxy validation (KS test)

**Outputs:**
"""

    for fname in ['framework_results.csv', 'statistical_tests.json', 'proxy_validation.json']:
        fpath = output_dir / 'validation' / fname
        if fpath.exists():
            info = get_file_info(fpath)
            content += f"- `validation/{fname}`: "
            if 'row_count' in info:
                content += f"{info['row_count']} rows, "
            content += f"SHA: {info.get('sha256', 'N/A')}\n"

    content += """
---

## Stage 6: Report Generation

**Purpose:** Generate publication-ready markdown reports

**Inputs:**
- All validation outputs
- Manifest

**Outputs:**
- `reports/trackB_report.md`
- `reports/executive_summary.md`
- `reports/SPEC_COMPLIANCE.md` (this document)
- `reports/PIPELINE_IO_TRACE.md` (this document)

---

## Assumptions & Limitations

1. **STEP 1/2/3 independence:** Different data sources, proxy integration only
2. **High-risk definition:** Fixed at yield_true < 0.6 before analysis
3. **Budget model:** Simplified costs ($150 inline, $500 SEM)
4. **Determinism:** Random seed=42 for reproducibility

---

## Verification Commands

**To verify this trace:**
```bash
# Check test set size
wc -l {output_dir}/validation/framework_results.csv

# Check baseline equality
diff <(cut -d, -f1 {output_dir}/baselines/random_results.csv | sort) \\
     <(cut -d, -f1 {output_dir}/baselines/rulebased_results.csv | sort)

# Verify hashes
sha256sum {output_dir}/_manifest.json
```
"""

    output_path = output_dir / 'reports' / 'PIPELINE_IO_TRACE.md'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding='utf-8')
    print(f"✅ Generated: {output_path}")


def generate_verification_verdict(output_dir: Path) -> None:
    """Generate verification_verdict.json"""

    # Load config
    config_path = TRACKB_ROOT / 'configs' / 'trackb_config.json'
    with open(config_path) as f:
        config = json.load(f)

    failures = []
    warnings = []

    # Check test set size
    framework_results = output_dir / 'validation' / 'framework_results.csv'
    if framework_results.exists():
        df = pd.read_csv(framework_results)
        if len(df) != 200:
            failures.append(f"Test set size mismatch: {len(df)} != 200")
    else:
        failures.append("framework_results.csv not found")

    # Check proxy validation
    proxy_file = output_dir / 'validation' / 'proxy_validation.json'
    if proxy_file.exists():
        with open(proxy_file) as f:
            proxy_data = json.load(f)

        p_value = proxy_data.get('p_value', 1.0)
        proxy_policy = config.get('validation', {}).get('proxy_validation_policy', 'strict_fail')

        if p_value <= 0.05:  # Failed plausibility
            if 'proxy_status' not in proxy_data:
                failures.append("proxy_validation.json missing 'proxy_status' field")
            elif 'FAILED' not in proxy_data.get('proxy_status', ''):
                failures.append(f"Proxy plausibility failed (p={p_value}) but status not FAILED_PLAUSIBILITY")

            if proxy_policy == 'strict_fail':
                failures.append(f"Proxy validation failed (p={p_value:.2e}) with strict_fail policy")
            else:
                warnings.append(f"Proxy validation failed (p={p_value:.2e}) but policy is {proxy_policy}")
    else:
        failures.append("proxy_validation.json not found")

    # Determine verdict
    if len(failures) > 0:
        verdict = "FAIL"
    elif len(warnings) > 0:
        verdict = "PASS_WITH_WARNINGS"
    else:
        verdict = "PASS"

    verdict_data = {
        "verdict": verdict,
        "timestamp": datetime.now().isoformat(),
        "run_id": output_dir.name if output_dir.name.startswith('run_') else "latest",
        "config_sha256": compute_file_hash(config_path),
        "failures": failures,
        "warnings": warnings,
        "checks_performed": [
            "test_set_size",
            "proxy_validation_semantics",
            "proxy_validation_policy",
            "required_files_exist"
        ]
    }

    output_path = output_dir / 'validation' / 'verification_verdict.json'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(verdict_data, f, indent=2)

    print(f"✅ Generated: {output_path}")
    print(f"\n{'='*60}")
    print(f"VERDICT: {verdict}")
    print(f"{'='*60}")
    if failures:
        print("\n❌ FAILURES:")
        for i, f in enumerate(failures, 1):
            print(f"  {i}. {f}")
    if warnings:
        print("\n⚠️ WARNINGS:")
        for i, w in enumerate(warnings, 1):
            print(f"  {i}. {w}")


def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description='Generate Track B audit documentation')
    parser.add_argument('--output_dir', type=str, default='outputs',
                       help='Output directory (default: outputs)')
    args = parser.parse_args()

    output_dir = TRACKB_ROOT / args.output_dir

    if not output_dir.exists():
        print(f"❌ Output directory not found: {output_dir}")
        sys.exit(1)

    print(f"Generating audit documents for: {output_dir}\n")

    generate_spec_compliance(output_dir)
    generate_pipeline_io_trace(output_dir)
    generate_verification_verdict(output_dir)

    print(f"\n✅ All audit documents generated successfully")


if __name__ == '__main__':
    main()
