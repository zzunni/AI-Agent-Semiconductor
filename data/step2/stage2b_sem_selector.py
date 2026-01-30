# comments are lowercase as requested

import os
import json
import math
import argparse
import pandas as pd

from stage2b_pattern_matcher import load_mapping, apply_pattern_mapping


def compute_top_threshold(sev: pd.Series, top_p: float) -> float:
    return float(sev.quantile(1.0 - float(top_p)))


def select_sem_with_budget(cand_non_scratch: pd.DataFrame, mandatory_cols, max_count):
    cand = cand_non_scratch.copy().sort_values("severity", ascending=False).reset_index(drop=True)
    mand = cand[(cand[mandatory_cols].sum(axis=1) >= 1)].drop_duplicates(subset=["orig_idx"]).copy()

    # mandatory must be included even if budget is smaller
    if max_count is None:
        send = cand.copy()
        budget_overrun = False
    else:
        max_count = int(max_count)
        if len(mand) >= max_count:
            send = mand.copy()
            budget_overrun = True
        else:
            remaining = max_count - len(mand)
            rest = cand[~cand["orig_idx"].isin(set(mand["orig_idx"]))].head(remaining).copy()
            send = pd.concat([mand, rest], axis=0, ignore_index=True)
            budget_overrun = False

    send = send.sort_values("severity", ascending=False).reset_index(drop=True)

    reasons = []
    for r in send.itertuples(index=False):
        rr = []
        for c in mandatory_cols:
            if int(getattr(r, c)) == 1:
                rr.append(f"mandatory_{c}")
        if len(rr) == 0:
            rr.append("top_percent_high_severity")
        reasons.append(",".join(rr))
    send["sem_reason"] = reasons
    send["sem_selected"] = 1
    send["budget_overrun"] = int(budget_overrun)
    return send


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base_dir", type=str, required=True)
    ap.add_argument("--config", type=str, default=None)
    ap.add_argument("--severity_csv", type=str, default=None)
    ap.add_argument("--out_csv", type=str, default=None)
    args = ap.parse_args()

    base_dir = args.base_dir
    cfg_path = args.config or os.path.join(base_dir, "config", "stage2b_config.json")
    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    top_p = float(cfg["severity_policy"].get("top_p", 0.10))
    if abs(top_p - 0.10) > 1e-9:
        raise ValueError(f"stage2b is fixed to top_p=0.10, but config has top_p={top_p}")

    physical_damage_label = str(cfg["routing_policy"]["physical_damage_label"])
    mandatory_flags = list(cfg["mandatory_policy_within_top"]["mandatory_flags"])

    sem_unit_cost = cfg["sem_budget"].get("sem_unit_cost", 1.0)
    sem_total_budget = cfg["sem_budget"].get("sem_total_budget", None)
    sem_max_count = cfg["sem_budget"].get("sem_max_count", None)

    max_count = None
    if sem_total_budget is not None and sem_unit_cost is not None:
        max_count = int(math.floor(float(sem_total_budget) / float(sem_unit_cost)))
    if sem_max_count is not None:
        max_count = int(sem_max_count) if max_count is None else min(int(sem_max_count), int(max_count))

    sev_csv = args.severity_csv or os.path.join(base_dir, "03_severity", "severity_scores_all.csv")
    if not os.path.exists(sev_csv):
        raise FileNotFoundError(f"missing severity csv: {sev_csv}")

    df = pd.read_csv(sev_csv)

    for c in ["orig_idx", "pred_label", "severity"]:
        if c not in df.columns:
            raise ValueError(f"severity csv must contain column: {c}")

    missing_flags = [c for c in mandatory_flags if c not in df.columns]
    if missing_flags:
        raise ValueError(
            "missing mandatory flag columns in severity csv: "
            + ", ".join(missing_flags)
            + ". step2 must write these columns into 03_severity/severity_scores_all.csv"
        )

    thr = compute_top_threshold(df["severity"], top_p)
    cand_all = df[df["severity"] >= thr].copy().sort_values("severity", ascending=False).reset_index(drop=True)

    # route scratch to physical damage (not sem)
    phys = cand_all[cand_all["pred_label"].astype(str) == physical_damage_label].copy()
    phys["route"] = "physical_damage"
    phys["route_reason"] = "physical_damage_scratch_top10"
    phys["sem_selected"] = 0
    phys["sem_reason"] = "do_not_send_to_sem"

    # sem candidates are non-scratch top10
    sem_cand = cand_all[cand_all["pred_label"].astype(str) != physical_damage_label].copy()
    sem_cand["route"] = "sem_candidate"
    sem_cand["route_reason"] = "top10_non_scratch"

    selected = select_sem_with_budget(sem_cand, mandatory_flags, max_count)
    selected["route"] = "sem_selected"
    selected["route_reason"] = "selected_for_sem"
    selected["sem_unit_cost"] = float(sem_unit_cost)
    selected["sem_cost"] = float(sem_unit_cost) * 1.0

    if max_count is None:
        remainder = pd.DataFrame(columns=sem_cand.columns)
    else:
        selected_idx = set(selected["orig_idx"].astype(int).tolist())
        remainder = sem_cand[~sem_cand["orig_idx"].astype(int).isin(selected_idx)].copy()
        remainder["sem_selected"] = 0
        remainder["sem_reason"] = "not_selected_due_to_budget"
        remainder["route"] = "sem_not_selected"
        remainder["route_reason"] = "budget_cap"
        remainder["sem_unit_cost"] = float(sem_unit_cost)
        remainder["sem_cost"] = 0.0
        remainder["budget_overrun"] = 0

    # attach pattern mapping
    mapping_path = cfg["pattern_mapping"]["mapping_path"]
    if not os.path.isabs(mapping_path):
        mapping_path = os.path.normpath(os.path.join(os.path.dirname(cfg_path), "..", mapping_path))

    mapping = load_mapping(mapping_path)

    selected = apply_pattern_mapping(selected, mapping)
    remainder = apply_pattern_mapping(remainder, mapping) if len(remainder) else remainder
    phys = apply_pattern_mapping(phys, mapping)

    # engineer_approved_count must be null
    for t in [selected, remainder, phys]:
        if len(t):
            t["engineer_approved_count"] = None

    out = pd.concat([selected, remainder, phys], axis=0, ignore_index=True)
    out["top_p"] = top_p
    out["severity_threshold"] = thr

    first_cols = [
        "orig_idx", "true_label", "pred_label", "severity", "conf",
        "random_like", "blob_like", "cluster_like",
        "sem_selected", "sem_reason",
        "route", "route_reason",
        "process_step", "process_hypothesis", "mapping_source",
        "sem_unit_cost", "sem_cost",
        "top_p", "severity_threshold",
        "engineer_approved_count"
    ]
    cols = [c for c in first_cols if c in out.columns] + [c for c in out.columns if c not in first_cols]
    out = out[cols].copy()

    out_csv = args.out_csv or os.path.join(base_dir, "stage2b_results.csv")
    out.to_csv(out_csv, index=False, na_rep="")

    print("saved:", out_csv)


if __name__ == "__main__":
    main()
