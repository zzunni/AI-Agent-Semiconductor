#!/usr/bin/env python3
"""
Lot leakage risk diagnostics (no retraining, no data change).
Loads existing Step1 test data from run outputs and optionally train from step1 artifacts;
computes lot-level stats and train/test overlap. Saves validation/lot_leakage_diagnostics.json.
"""

from pathlib import Path
import json
import sys
import logging
from typing import Dict, Any, Optional

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)
SCRIPT_DIR = Path(__file__).resolve().parent
TRACKB_ROOT = SCRIPT_DIR.parent


def _find_lot_col(df: pd.DataFrame) -> Optional[str]:
    for c in ["lot_id", "LotID", "lot"]:
        if c in df.columns:
            return c
    return None


def compute_lot_diagnostics(
    run_output_dir: Path,
    step1_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Compute lot leakage risk diagnostics from existing run outputs.
    No model retraining, no dataset change.
    """
    run_output_dir = Path(run_output_dir)
    # Test: use baselines/random_results.csv (200 rows, same test set)
    test_path = run_output_dir / "baselines" / "random_results.csv"
    if not test_path.exists():
        return {
            "diagnostics_available": False,
            "reason": "baselines/random_results.csv not found",
            "n_test_wafers": None,
        }

    test_df = pd.read_csv(test_path, encoding="utf-8-sig")
    n_test = len(test_df)
    lot_col = _find_lot_col(test_df)
    yield_col = "yield_true" if "yield_true" in test_df.columns else "yield"
    hr_col = "is_high_risk" if "is_high_risk" in test_df.columns else None

    out = {
        "diagnostics_available": True,
        "source_test_file": "baselines/random_results.csv",
        "n_test_wafers": int(n_test),
    }

    if lot_col is None:
        out["n_test_lots"] = None
        out["reason_partial"] = "lot_id (or equivalent) not in test file; risk diagnostics limited."
        out["test_lot_size_min"] = None
        out["test_lot_size_median"] = None
        out["test_lot_size_max"] = None
        out["train_lots_available"] = False
        out["overlap_lots_count"] = None
        out["overlap_wafers_count"] = None
        out["yield_by_lot_summary"] = None
        out["high_risk_rate_by_lot_min"] = None
        out["high_risk_rate_by_lot_median"] = None
        out["high_risk_rate_by_lot_max"] = None
        return out

    test_lots = test_df[lot_col].astype(str)
    n_test_lots = int(test_lots.nunique())
    out["n_test_lots"] = n_test_lots
    lot_sizes = test_df.groupby(lot_col, dropna=False).size()
    out["test_lot_size_min"] = int(lot_sizes.min())
    out["test_lot_size_median"] = float(lot_sizes.median())
    out["test_lot_size_max"] = int(lot_sizes.max())

    if yield_col in test_df.columns:
        by_lot = test_df.groupby(lot_col)[yield_col].agg(["mean", "std", "min", "max"])
        out["yield_by_lot_mean_of_means"] = float(by_lot["mean"].mean())
        out["yield_by_lot_std_of_means"] = float(by_lot["mean"].std()) if len(by_lot) > 1 else 0.0
        q = by_lot["mean"].quantile([0.25, 0.5, 0.75])
        out["yield_by_lot_iqr"] = [float(q[0.25]), float(q[0.5]), float(q[0.75])]

    if hr_col and hr_col in test_df.columns:
        hr_rate = test_df.groupby(lot_col)[hr_col].mean()
        out["high_risk_rate_by_lot_min"] = float(hr_rate.min())
        out["high_risk_rate_by_lot_median"] = float(hr_rate.median())
        out["high_risk_rate_by_lot_max"] = float(hr_rate.max())

    # Train overlap (optional)
    out["train_lots_available"] = False
    out["n_train_lots"] = None
    out["overlap_lots_count"] = None
    out["overlap_wafers_count"] = None

    if step1_dir is not None:
        step1_dir = Path(step1_dir)
        train_files = list(step1_dir.glob("_stage*_train*.csv")) or list(step1_dir.glob("*train*.csv"))
        train_df = None
        for fp in train_files[:1]:
            try:
                train_df = pd.read_csv(fp, encoding="utf-8-sig", nrows=2000)
                break
            except Exception:
                continue
        if train_df is not None:
            train_lot_col = _find_lot_col(train_df)
            if train_lot_col is not None:
                train_lots = set(train_df[train_lot_col].astype(str).unique())
                test_lot_set = set(test_lots.unique())
                overlap_lots = train_lots & test_lot_set
                out["train_lots_available"] = True
                out["n_train_lots"] = int(len(train_lots))
                out["overlap_lots_count"] = int(len(overlap_lots))
                out["overlap_wafers_count"] = int(test_df[test_lots.isin(overlap_lots)].shape[0])

    return out


def main():
    import argparse
    p = argparse.ArgumentParser(description="Lot leakage risk diagnostics (no retraining)")
    p.add_argument("--run_id", type=str, help="Run ID (e.g. 20260130_232106)")
    p.add_argument("--run_dir", type=str, help="Or full path to run_<run_id> dir")
    p.add_argument("--step1_dir", type=str, default=None, help="Step1 artifacts dir for train lot overlap")
    args = p.parse_args()

    run_dir = None
    if args.run_dir:
        run_dir = Path(args.run_dir)
    elif args.run_id:
        run_dir = TRACKB_ROOT / "outputs" / f"run_{args.run_id}"
    else:
        latest = TRACKB_ROOT / "outputs" / "latest"
        if latest.exists():
            target = latest.read_text().strip() if latest.is_file() else latest.resolve().name
            run_dir = TRACKB_ROOT / "outputs" / target
        else:
            dirs = sorted(
                [d for d in (TRACKB_ROOT / "outputs").iterdir() if d.is_dir() and d.name.startswith("run_")],
                key=lambda x: x.name,
                reverse=True,
            )
            run_dir = dirs[0] if dirs else None
    if run_dir is None or not run_dir.exists():
        print("Run directory not found", file=sys.stderr)
        sys.exit(1)

    step1 = Path(args.step1_dir) if args.step1_dir else TRACKB_ROOT.parent / "data" / "step1"
    if not step1.exists():
        step1 = None

    diag = compute_lot_diagnostics(run_dir, step1_dir=step1)
    out_path = run_dir / "validation" / "lot_leakage_diagnostics.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(diag, f, indent=2, ensure_ascii=False)
    print(f"Wrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
