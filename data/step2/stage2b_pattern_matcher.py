# comments are lowercase as requested

import json
from typing import Dict, Any
import pandas as pd


def load_mapping(mapping_path: str) -> Dict[str, Any]:
    with open(mapping_path, "r", encoding="utf-8") as f:
        return json.load(f)


def apply_pattern_mapping(df: pd.DataFrame, mapping: Dict[str, Any]) -> pd.DataFrame:
    """
    required columns in df:
      - pred_label (str)

    added columns:
      - process_step (str)
      - process_hypothesis (str)
      - mapping_source (str)  # 'pattern_map' or 'default'
    """
    patterns = mapping.get("patterns", {})
    default = mapping.get("default", {"process_step": "unknown", "hypothesis": "no mapping rule"})

    steps = []
    hyps = []
    srcs = []

    for lab in df["pred_label"].astype(str).values:
        if lab in patterns:
            steps.append(str(patterns[lab].get("process_step", default.get("process_step", "unknown"))))
            hyps.append(str(patterns[lab].get("hypothesis", default.get("hypothesis", "no mapping rule"))))
            srcs.append("pattern_map")
        else:
            steps.append(str(default.get("process_step", "unknown")))
            hyps.append(str(default.get("hypothesis", "no mapping rule")))
            srcs.append("default")

    out = df.copy()
    out["process_step"] = steps
    out["process_hypothesis"] = hyps
    out["mapping_source"] = srcs
    return out
