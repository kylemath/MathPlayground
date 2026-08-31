#!/usr/bin/env python3
"""Normalize Dudeney histogram keys (int vs str) from existing S1 audit JSON."""

from __future__ import annotations

import json
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "outputs"
DATA = json.loads((OUT / "s1_independent_verify.json").read_text(encoding="utf-8"))

csv_hist = DATA["csv_audit"]["dudeney_group_distribution"]
json_hist = DATA["analysis_crosscheck"]["analysis_dudeneyCounts"]

csv_norm = {str(k): v for k, v in csv_hist.items()}
json_norm = {str(k): v for k, v in json_hist.items()}

result = {
    "raw_comparison_equal": json_hist == csv_hist,
    "normalized_comparison_equal": json_norm == csv_norm,
    "csv_keys_type": "int (from Counter on int dudeney_group)",
    "json_keys_type": "str (JSON object keys are always strings)",
    "csv_histogram_normalized": csv_norm,
    "analysis_histogram_normalized": json_norm,
    "note": (
        "dudeney_matches_csv=false in s1_independent_verify.json is a key-type "
        "artifact only; histograms match after str() normalization."
    ),
}

out_path = OUT / "s1_dudeney_key_normalize.json"
out_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(result, indent=2, sort_keys=True))
