#!/usr/bin/env python3
"""Independently recount analysis.csv cohorts and magic flags."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

ANALYSIS_CSV = Path("/Users/kylemathewson/MagicSK/MagicMomentExplorer/data/analysis.csv")
OUT = Path(__file__).resolve().parents[1] / "outputs" / "s1_analysis_cohort_check.json"


def main() -> None:
    with ANALYSIS_CSV.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    cohort_counts = Counter(r["cohort"] for r in rows)
    magic_by_cohort = Counter()
    for r in rows:
        if r.get("is_magic", r.get("magic", "")).lower() in ("true", "1"):
            magic_by_cohort[r["cohort"]] += 1
        elif r.get("is_magic") == "True":
            magic_by_cohort[r["cohort"]] += 1

    # analysis.csv uses column 'magic' as bool string
    if not magic_by_cohort:
        for r in rows:
            if r.get("magic") == "True":
                magic_by_cohort[r["cohort"]] += 1

    result = {
        "total_rows": len(rows),
        "cohort_counts": dict(sorted(cohort_counts.items())),
        "magic_true_by_cohort": dict(sorted(magic_by_cohort.items())),
        "expected_total": 4400,
        "expected_per_cohort": 880,
    }
    OUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
