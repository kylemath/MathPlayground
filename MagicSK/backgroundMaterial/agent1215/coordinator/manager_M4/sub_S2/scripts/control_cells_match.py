#!/usr/bin/env python3
"""Verify shipped control cell arrays match deterministic replay of analyze.py RNG stream."""

from __future__ import annotations

import csv
import json
import random
import sys
from pathlib import Path

N = 4
SEED = 20260709
PROJECT_ROOT = Path("/Users/kylemathewson/MagicSK/MagicMomentExplorer")
SOURCE_CSV = PROJECT_ROOT / "data" / "magic_squares_880.csv"
SHIPPED_JSON = PROJECT_ROOT / "data" / "analysis.json"


def swapped_copy(cells: list[int], count: int, rng: random.Random) -> list[int]:
    result = cells.copy()
    positions = rng.sample(range(N * N), count * 2)
    for index in range(0, len(positions), 2):
        left, right = positions[index : index + 2]
        result[left], result[right] = result[right], result[left]
    return result


def load_source() -> list[list[int]]:
    cells_list: list[list[int]] = []
    with SOURCE_CSV.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            cells_list.append([int(row[f"cell_{index}"]) for index in range(1, 17)])
    return cells_list


def main() -> int:
    with SHIPPED_JSON.open(encoding="utf-8") as handle:
        shipped = {record["recordId"]: record for record in json.load(handle)["records"]}

    source = load_source()
    rng = random.Random(SEED)
    mismatches: list[dict] = []

    for swap_count in (1, 2, 3):
        for record in source:
            record_id = f"S{swap_count}-{record['id']:03d}" if isinstance(record, dict) else None

    # source is list of cells only from load_source - fix
    source_ids = []
    with SOURCE_CSV.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            source_ids.append(int(row["id"]))

    for swap_count in (1, 2, 3):
        for source_id, cells in zip(source_ids, source):
            perturbed = swapped_copy(cells, swap_count, rng)
            record_id = f"S{swap_count}-{source_id:03d}"
            if shipped[record_id]["cells"] != perturbed:
                mismatches.append({"recordId": record_id, "kind": "swap"})

    for index in range(1, 881):
        cells = list(range(1, 17))
        rng.shuffle(cells)
        record_id = f"R{index:03d}"
        if shipped[record_id]["cells"] != cells:
            mismatches.append({"recordId": record_id, "kind": "random"})

    report = {
        "seed": SEED,
        "swap_checks": 880 * 3,
        "random_checks": 880,
        "mismatches": mismatches[:20],
        "mismatch_count": len(mismatches),
        "all_match": len(mismatches) == 0,
    }

    out = Path(__file__).resolve().parents[1] / "outputs" / "control_cells_match.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["all_match"] else 1


if __name__ == "__main__":
    sys.exit(main())
