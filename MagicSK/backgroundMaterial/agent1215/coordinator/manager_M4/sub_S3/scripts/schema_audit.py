#!/usr/bin/env python3
"""Schema, field-semantics, and cross-stream alignment audit (stdlib only)."""

from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path("/Users/kylemathewson/MagicSK/MagicMomentExplorer")
M3_SAMPLE = Path(
    "/Users/kylemathewson/MagicSK/backgroundMaterial/agent1215/"
    "coordinator/manager_M3/sub_S3/prototype/sample-data.json"
)

# Likely M1 classification / provenance fields (from M1 brief + analyze.py)
M1_RECORD_FIELDS = {
    "recordId": "str",
    "sourceId": "int|null",
    "cells": "int[16]",
    "isMagic": "bool",
    "dudeneyGroup": "int|null",
    "dudeneyLabel": "str|null",
    "groupOrientation": "int|null",
    "complementPair": "int|null",
    "complementId": "int|null",
    "selfComplementary": "bool",
    "classes": "str[]",
    "d4OrbitSize": "int",
    "lineSums": "object",
}

# Likely M2 moment / energy fields
M2_RECORD_FIELDS = {
    "coefficients": "dict[str,float] (15 modes)",
    "modeEnergy": "dict[str,float] (15 modes)",
    "degreeEnergy": "dict[str,float] keys 2..6",
    "axialEnergy": "float",
    "interactionEnergy": "float",
    "lowOrderEnergy": "float",
    "highOrderEnergy": "float",
    "spectralCentroid": "float",
    "lineDefectEnergy": "float",
}

M2_METADATA_FIELDS = {
    "order": "int",
    "magicSum": "int",
    "sourceCount": "int",
    "expandedOrientedCount": "int",
    "seed": "int",
    "randomCount": "int",
    "heightEnergy": "float",
    "coordinates": "float[4]",
    "basis": "float[4][4]",
    "groupLabels": "dict[int,str]",
    "cohortSummary": "object[]",
    "dudeneyCounts": "dict[int,int]",
}

M3_REQUIRED_RECORD = [
    "recordId",
    "cells",
    "modeEnergy",
    "degreeEnergy",
    "interactionEnergy",
]

MODE_NAMES = [
    f"M{x}{y}"
    for x in range(4)
    for y in range(4)
    if not (x == 0 and y == 0)
]


def load_analysis() -> dict[str, Any]:
    path = ROOT / "data" / "analysis.json"
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def type_name(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        return "str"
    if isinstance(value, list):
        return f"list(len={len(value)})"
    if isinstance(value, dict):
        return f"dict(keys={len(value)})"
    return type(value).__name__


def check_record_schema(record: dict[str, Any]) -> dict[str, Any]:
    issues: list[str] = []
    for field, expected in {**M1_RECORD_FIELDS, **M2_RECORD_FIELDS}.items():
        if field not in record:
            issues.append(f"missing:{field}")
            continue
        val = record[field]
        if field == "cells":
            if not isinstance(val, list) or len(val) != 16:
                issues.append("cells:not_len_16")
        if field == "classes" and not isinstance(val, list):
            issues.append("classes:not_array")
        if field in ("coefficients", "modeEnergy"):
            if set(val.keys()) != set(MODE_NAMES):
                issues.append(f"{field}:mode_key_mismatch")
        if field == "degreeEnergy":
            if set(val.keys()) != {str(d) for d in range(2, 7)}:
                issues.append("degreeEnergy:degree_key_mismatch")

    # Energy conservation: all 15 modes sum to fixed height energy (340)
    mode_sum = sum(record["modeEnergy"].values())
    if abs(mode_sum - 340.0) > 1e-3:
        issues.append(f"mode_energy_total_mismatch:{mode_sum:.6f}")

    interaction = record["interactionEnergy"]
    degree_sum = sum(record["degreeEnergy"].values())
    if abs(degree_sum - interaction) > 1e-4:
        issues.append(f"degree_energy_sum_mismatch:{degree_sum:.6f}!={interaction:.6f}")

    total = record["axialEnergy"] + record["interactionEnergy"]
    if abs(total - 340.0) > 1e-3:
        issues.append(f"axial_plus_interaction_mismatch:{total:.6f}")

    if record["isMagic"] and record["axialEnergy"] > 1e-6:
        issues.append("magic_record_nonzero_axial")

    return {"recordId": record["recordId"], "issues": issues}


def compare_m3_sample(app_record: dict[str, Any], m3_record: dict[str, Any]) -> dict[str, Any]:
    shared = sorted(set(app_record) & set(m3_record))
    app_only = sorted(set(app_record) - set(m3_record))
    m3_only = sorted(set(m3_record) - set(app_record))
    cohort_app = app_record.get("cohort")
    cohort_m3 = m3_record.get("cohort")
    return {
        "app_recordId": app_record["recordId"],
        "m3_recordId": m3_record["recordId"],
        "shared_field_count": len(shared),
        "app_only_fields": app_only,
        "m3_only_fields": m3_only,
        "cohort_app": cohort_app,
        "cohort_m3": cohort_m3,
        "cells_match": app_record.get("cells") == m3_record.get("cells"),
        "interaction_match": app_record.get("interactionEnergy")
        == m3_record.get("interactionEnergy"),
    }


def main() -> int:
    payload = load_analysis()
    metadata = payload["metadata"]
    records = payload["records"]

    meta_issues: list[str] = []
    if "schemaVersion" not in metadata and "schemaVersion" not in payload:
        meta_issues.append("missing:schemaVersion (M3 prototype expects top-level)")
    for field in M2_METADATA_FIELDS:
        if field not in metadata:
            meta_issues.append(f"missing_metadata:{field}")

    cohorts = Counter(r["cohort"] for r in records)
    record_issues = [check_record_schema(r) for r in records]
    bad = [r for r in record_issues if r["issues"]]

    m3 = json.loads(M3_SAMPLE.read_text(encoding="utf-8"))
    m3_ids = {r["recordId"]: r for r in m3["records"]}
    overlaps = []
    for rec in records:
        if rec["recordId"] in m3_ids:
            overlaps.append(compare_m3_sample(rec, m3_ids[rec["recordId"]]))

    # Source CSV header check (M1)
    with (ROOT / "data" / "magic_squares_880.csv").open(newline="", encoding="utf-8") as f:
        source_fields = csv.DictReader(f).fieldnames

    # App file presence for browser E2E
    expected_app_files = [
        "index.html",
        "styles.css",
        "app.js",
        "moments.js",
        "data/analysis-data.js",
        "data/analysis.json",
        "README.md",
    ]
    file_status = {
        name: (ROOT / name).exists() for name in expected_app_files
    }

    report = {
        "record_count": len(records),
        "cohort_counts": dict(sorted(cohorts.items())),
        "metadata_fields_present": sorted(metadata.keys()),
        "metadata_issues": meta_issues,
        "records_with_schema_issues": len(bad),
        "first_bad_records": bad[:5],
        "m3_schema_version": m3.get("schemaVersion"),
        "m3_cohort_values_in_sample": sorted({r["cohort"] for r in m3["records"]}),
        "app_cohort_values": sorted(cohorts.keys()),
        "m3_overlap_comparisons": overlaps[:3],
        "source_csv_fields": source_fields,
        "browser_file_status": file_status,
        "sample_record_field_types": {
            k: type_name(records[0][k]) for k in sorted(records[0].keys())
        },
    }

    out = Path(__file__).resolve().parents[1] / "evidence" / "schema_audit.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 1 if bad or any(not v for k, v in file_status.items() if k.endswith(".js")) else 0


if __name__ == "__main__":
    sys.exit(main())
