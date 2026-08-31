#!/usr/bin/env python3
"""Evidence table for cohort counts, energy conventions, and UI claims."""

from __future__ import annotations

import json
from pathlib import Path

SHIPPED_JSON = Path("/Users/kylemathewson/MagicSK/MagicMomentExplorer/data/analysis.json")

AXIAL_NAMES = sorted(
    f"M{x}{y}"
    for x in range(4)
    for y in range(4)
    if (x == 0) != (y == 0)  # exactly one zero index; matches analyze.py
)
INTERACTION_NAMES = [
    f"M{x}{y}" for x in range(1, 4) for y in range(1, 4)
]

def main() -> None:
    with SHIPPED_JSON.open(encoding="utf-8") as handle:
        payload = json.load(handle)

    meta = payload["metadata"]
    records = payload["records"]

    table = {
        "ui_claims": {
            "fundamental_squares": 880,
            "oriented_squares": 7040,
            "analyzed_records": 4400,
            "fixed_height_energy": 340,
            "seed": 20260709,
        },
        "metadata_values": {
            "sourceCount": meta["sourceCount"],
            "expandedOrientedCount": meta["expandedOrientedCount"],
            "record_count": len(records),
            "heightEnergy": meta["heightEnergy"],
            "seed": meta["seed"],
        },
        "cohort_counts": {},
        "mode_inventory": {
            "total_modes_excluding_M00": 15,
            "axial_modes": AXIAL_NAMES,
            "interaction_modes": INTERACTION_NAMES,
            "axial_count": len(AXIAL_NAMES),
            "interaction_count": len(INTERACTION_NAMES),
        },
        "spectral_centroid_note": (
            "spectralCentroid = sum(d * E_d for d in 2..6) / interactionEnergy; "
            "uses interaction modes only, not axial"
        ),
        "low_order_note": "lowOrderEnergy = degreeEnergy['2'] + degreeEnergy['3']",
    }

    for record in records:
        table["cohort_counts"][record["cohort"]] = table["cohort_counts"].get(record["cohort"], 0) + 1

    table["claims_match"] = {
        "880_fundamental": meta["sourceCount"] == 880,
        "7040_oriented": meta["expandedOrientedCount"] == 7040,
        "4400_records": len(records) == 4400,
        "340_energy": meta["heightEnergy"] == 340.0,
        "five_cohorts_880_each": all(count == 880 for count in table["cohort_counts"].values()),
    }

    out = Path(__file__).resolve().parents[1] / "evidence" / "numerical_claims_table.json"
    out.write_text(json.dumps(table, indent=2), encoding="utf-8")
    print(json.dumps(table, indent=2))


if __name__ == "__main__":
    main()
