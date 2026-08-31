#!/usr/bin/env python3
"""Independent audit: control definitions, seed, aggregation, reproducibility."""

from __future__ import annotations

import csv
import json
import random
import subprocess
import sys
from pathlib import Path
from typing import Any

N = 4
SEED = 20260709
PROJECT_ROOT = Path("/Users/kylemathewson/MagicSK/MagicMomentExplorer")
ANALYZE_PY = PROJECT_ROOT / "scripts" / "analyze.py"
SOURCE_CSV = PROJECT_ROOT / "data" / "magic_squares_880.csv"
SHIPPED_JSON = PROJECT_ROOT / "data" / "analysis.json"
OUT_DIR = Path(__file__).resolve().parents[1]
REPRO_DIR = OUT_DIR / "outputs" / "repro_run"


def swapped_copy(cells: list[int], count: int, rng: random.Random) -> list[int]:
    result = cells.copy()
    positions = rng.sample(range(N * N), count * 2)
    for index in range(0, len(positions), 2):
        left, right = positions[index : index + 2]
        result[left], result[right] = result[right], result[left]
    return result


def summarize(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cohorts = sorted({record["cohort"] for record in records})
    summaries: list[dict[str, Any]] = []
    for cohort in cohorts:
        subset = [record for record in records if record["cohort"] == cohort]
        summaries.append(
            {
                "cohort": cohort,
                "count": len(subset),
                "magicCount": sum(record["isMagic"] for record in subset),
                "meanLineDefect": round(
                    sum(record["lineDefectEnergy"] for record in subset) / len(subset), 6
                ),
                "meanAxialEnergy": round(
                    sum(record["axialEnergy"] for record in subset) / len(subset), 6
                ),
                "meanLowOrderEnergy": round(
                    sum(record["lowOrderEnergy"] for record in subset) / len(subset), 6
                ),
                "meanSpectralCentroid": round(
                    sum(record["spectralCentroid"] for record in subset) / len(subset), 6
                ),
            }
        )
    return summaries


def audit_control_generation(source_cells: list[list[int]]) -> dict[str, Any]:
    rng = random.Random(SEED)
    swap_reports: dict[str, Any] = {}
    for swap_count in (1, 2, 3):
        first_source = source_cells[0]
        perturbed = swapped_copy(first_source, swap_count, rng)
        swap_reports[f"swap_{swap_count}_first_source"] = {
            "swap_count": swap_count,
            "positions_sampled": swap_count * 2,
            "still_permutation": sorted(perturbed) == list(range(1, 17)),
            "cells": perturbed,
        }

    random_reports = []
    for index in range(1, 4):
        cells = list(range(1, 17))
        rng.shuffle(cells)
        random_reports.append({"index": index, "cells": cells})

    return {
        "seed": SEED,
        "prng": "random.Random",
        "swap_method": "rng.sample(range(16), 2*count) then pairwise swap",
        "random_method": "rng.shuffle(list(range(1,17)))",
        "swap_examples": swap_reports,
        "random_first_three": random_reports,
    }


def load_source_cells() -> list[list[int]]:
    cells_list: list[list[int]] = []
    with SOURCE_CSV.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            cells_list.append([int(row[f"cell_{index}"]) for index in range(1, 17)])
    return cells_list


def compare_payloads(reference: dict[str, Any], reproduced: dict[str, Any]) -> dict[str, Any]:
    ref_meta = reference["metadata"]
    rep_meta = reproduced["metadata"]
    meta_fields = [
        "order",
        "magicSum",
        "sourceCount",
        "expandedOrientedCount",
        "seed",
        "randomCount",
        "heightEnergy",
        "coordinates",
        "basis",
        "cohortSummary",
        "dudeneyCounts",
    ]
    meta_match = {field: ref_meta[field] == rep_meta[field] for field in meta_fields}

    ref_records = {record["recordId"]: record for record in reference["records"]}
    rep_records = {record["recordId"]: record for record in reproduced["records"]}
    id_match = set(ref_records) == set(rep_records)

    metric_fields = [
        "lineDefectEnergy",
        "axialEnergy",
        "interactionEnergy",
        "lowOrderEnergy",
        "highOrderEnergy",
        "spectralCentroid",
        "isMagic",
        "cells",
    ]
    mismatches = []
    for record_id in sorted(ref_records):
        ref = ref_records[record_id]
        rep = rep_records[record_id]
        for field in metric_fields:
            if ref[field] != rep[field]:
                mismatches.append({"recordId": record_id, "field": field, "ref": ref[field], "rep": rep[field]})
                if len(mismatches) >= 20:
                    break
        if len(mismatches) >= 20:
            break

    return {
        "record_count_ref": len(reference["records"]),
        "record_count_rep": len(reproduced["records"]),
        "metadata_field_match": meta_match,
        "all_metadata_match": all(meta_match.values()),
        "record_ids_match": id_match,
        "metric_mismatches": mismatches,
        "fully_reproducible": all(meta_match.values()) and id_match and not mismatches,
    }


def run_analyze_to(output_dir: Path) -> str:
    output_dir.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable,
        str(ANALYZE_PY),
        "--input",
        str(SOURCE_CSV),
        "--output-dir",
        str(output_dir),
        "--random-count",
        "880",
        "--seed",
        str(SEED),
    ]
    completed = subprocess.run(command, capture_output=True, text=True, check=True)
    return completed.stdout.strip()


def audit_aggregation(payload: dict[str, Any]) -> dict[str, Any]:
    recomputed = summarize(payload["records"])
    shipped = payload["metadata"]["cohortSummary"]
    return {
        "recomputed_summary": recomputed,
        "shipped_summary": shipped,
        "matches": recomputed == shipped,
    }


def main() -> int:
    source_cells = load_source_cells()
    control_report = audit_control_generation(source_cells)

    with SHIPPED_JSON.open(encoding="utf-8") as handle:
        shipped = json.load(handle)

    aggregation_report = audit_aggregation(shipped)

    print("=== Control Definition Audit ===")
    print(f"Seed: {SEED}")
    print(f"Swap method: {control_report['swap_method']}")
    print(f"Random method: {control_report['random_method']}")
    for key, example in control_report["swap_examples"].items():
        print(f"{key}: permutation={example['still_permutation']}, cells={example['cells']}")
    for example in control_report["random_first_three"]:
        print(f"R{example['index']:03d} preview cells: {example['cells']}")

    print("\n=== Aggregation Audit ===")
    print(f"Cohort summary matches shipped: {aggregation_report['matches']}")
    for row in aggregation_report["shipped_summary"]:
        print(row)

    print("\n=== Reproducibility Run ===")
    stdout = run_analyze_to(REPRO_DIR)
    print(stdout)
    with (REPRO_DIR / "analysis.json").open(encoding="utf-8") as handle:
        reproduced = json.load(handle)
    repro_report = compare_payloads(shipped, reproduced)
    print(f"Fully reproducible: {repro_report['fully_reproducible']}")
    print(f"Metadata matches: {repro_report['all_metadata_match']}")
    print(f"Metric mismatches: {len(repro_report['metric_mismatches'])}")

    outputs = OUT_DIR / "outputs"
    outputs.mkdir(parents=True, exist_ok=True)
    report = {
        "control_generation": control_report,
        "aggregation": aggregation_report,
        "reproducibility": repro_report,
        "repro_command": [
            sys.executable,
            str(ANALYZE_PY),
            "--input",
            str(SOURCE_CSV),
            "--output-dir",
            str(REPRO_DIR),
            "--random-count",
            "880",
            "--seed",
            str(SEED),
        ],
        "repro_stdout": stdout,
    }
    (outputs / "control_repro_audit.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote {outputs / 'control_repro_audit.json'}")

    return 0 if aggregation_report["matches"] and repro_report["fully_reproducible"] else 1


if __name__ == "__main__":
    sys.exit(main())
