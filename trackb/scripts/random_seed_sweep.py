#!/usr/bin/env python3
"""
Random baseline multi-seed sweep (no retraining).
Same test200 and high_risk_mask; only random selection seed varies.
Outputs: validation/random_seed_sweep.csv, validation/random_seed_sweep_summary.json.
"""

from pathlib import Path
import json
import sys
import argparse
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple

TRACKB_ROOT = Path(__file__).resolve().parent.parent


def run_sweep(
    run_output_dir: Path,
    n_seeds: int = 50,
    selection_rate: float = 0.10,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Load test df + is_high_risk from run; run random 10% selection for each seed.
    Returns (sweep_df, summary_dict).
    """
    run_output_dir = Path(run_output_dir)
    test_path = run_output_dir / "baselines" / "random_results.csv"
    if not test_path.exists():
        raise FileNotFoundError(f"Need {test_path}")

    df = pd.read_csv(test_path, encoding="utf-8-sig")
    n = len(df)
    if "is_high_risk" not in df.columns:
        raise ValueError("random_results.csv must have is_high_risk")
    high_risk = df["is_high_risk"].values.astype(bool)
    n_high_risk = int(high_risk.sum())
    n_select = max(1, int(round(n * selection_rate)))

    rows = []
    for seed in range(n_seeds):
        rng = np.random.default_rng(seed)
        idx = rng.choice(n, size=n_select, replace=False)
        selected = np.zeros(n, dtype=bool)
        selected[idx] = True
        tp = int((selected & high_risk).sum())
        fn = int((~selected & high_risk).sum())
        recall = tp / n_high_risk if n_high_risk > 0 else 0.0
        rows.append({"seed": seed, "true_positive": tp, "false_negative": fn, "recall": recall})

    sweep_df = pd.DataFrame(rows)
    recalls = sweep_df["recall"].values
    summary = {
        "n_seeds": n_seeds,
        "n_test_wafers": int(n),
        "n_high_risk": n_high_risk,
        "selection_rate": selection_rate,
        "n_selected_per_run": n_select,
        "recall_mean": float(np.mean(recalls)),
        "recall_std": float(np.std(recalls)),
        "recall_p5": float(np.percentile(recalls, 5)),
        "recall_p50": float(np.percentile(recalls, 50)),
        "recall_p95": float(np.percentile(recalls, 95)),
    }
    return sweep_df, summary


def main():
    p = argparse.ArgumentParser(description="Random baseline multi-seed sweep")
    p.add_argument("--run_id", type=str, help="Run ID")
    p.add_argument("--run_dir", type=str, help="Or run directory path")
    p.add_argument("--n_seeds", type=int, default=50, help="Number of seeds (default 50)")
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
        return 1

    sweep_df, summary = run_sweep(run_dir, n_seeds=args.n_seeds)
    val_dir = run_dir / "validation"
    val_dir.mkdir(parents=True, exist_ok=True)
    sweep_df.to_csv(val_dir / "random_seed_sweep.csv", index=False)
    with open(val_dir / "random_seed_sweep_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"Wrote {val_dir / 'random_seed_sweep.csv'} and random_seed_sweep_summary.json")
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
