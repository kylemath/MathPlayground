#!/usr/bin/env python3
"""Reproducible spatial-moment analysis for normal order-4 squares."""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

N = 4
MAGIC_SUM = 34
MEAN_HEIGHT = 8.5
TOTAL_HEIGHT_ENERGY = 340.0
COORDINATES = (-1.5, -0.5, 0.5, 1.5)
GROUP_LABELS = {
    1: "I · pandiagonal",
    2: "II · bent-diagonal semi-pandiagonal",
    3: "III · associative semi-pandiagonal",
    4: "IV · semi-pandiagonal",
    5: "V · semi-pandiagonal",
    6: "VI · semi-pandiagonal/simple",
    7: "VII · simple",
    8: "VIII · simple",
    9: "IX · simple",
    10: "X · simple",
    11: "XI · limited symmetry",
    12: "XII · limited symmetry",
}


def dot(left: Iterable[float], right: Iterable[float]) -> float:
    return sum(a * b for a, b in zip(left, right))


def orthonormal_polynomials() -> list[list[float]]:
    """Gram–Schmidt monomials on the four centered cell coordinates."""
    basis: list[list[float]] = []
    for degree in range(N):
        vector = [coordinate**degree for coordinate in COORDINATES]
        for previous in basis:
            projection = dot(vector, previous)
            vector = [
                value - projection * prior
                for value, prior in zip(vector, previous)
            ]
        norm = math.sqrt(dot(vector, vector))
        basis.append([value / norm for value in vector])
    return basis


BASIS = orthonormal_polynomials()


def matrix(cells: list[int]) -> list[list[int]]:
    return [cells[offset : offset + N] for offset in range(0, N * N, N)]


def line_sums(cells: list[int]) -> tuple[list[int], list[int], list[int]]:
    square = matrix(cells)
    rows = [sum(row) for row in square]
    columns = [sum(square[row][column] for row in range(N)) for column in range(N)]
    diagonals = [
        sum(square[index][index] for index in range(N)),
        sum(square[index][N - 1 - index] for index in range(N)),
    ]
    return rows, columns, diagonals


def is_magic(cells: list[int]) -> bool:
    rows, columns, diagonals = line_sums(cells)
    return sorted(cells) == list(range(1, 17)) and all(
        value == MAGIC_SUM for value in rows + columns + diagonals
    )


def is_pandiagonal(cells: list[int]) -> bool:
    square = matrix(cells)
    lines: list[int] = []
    for offset in range(N):
        lines.append(sum(square[row][(row + offset) % N] for row in range(N)))
        lines.append(sum(square[row][(offset - row) % N] for row in range(N)))
    return is_magic(cells) and all(value == MAGIC_SUM for value in lines)


def is_associative(cells: list[int]) -> bool:
    square = matrix(cells)
    return all(
        square[row][column] + square[N - 1 - row][N - 1 - column] == 17
        for row in range(N)
        for column in range(N)
    )


def is_most_perfect(cells: list[int]) -> bool:
    square = matrix(cells)
    toroidal_blocks = all(
        sum(
            square[(row + dy) % N][(column + dx) % N]
            for dy in range(2)
            for dx in range(2)
        )
        == MAGIC_SUM
        for row in range(N)
        for column in range(N)
    )
    complementary_diagonals = all(
        square[row][column] + square[(row + 2) % N][(column + 2) % N] == 17
        for row in range(N)
        for column in range(N)
    )
    return is_magic(cells) and toroidal_blocks and complementary_diagonals


def transforms(cells: list[int]) -> list[tuple[int, ...]]:
    source = matrix(cells)

    def rotate(square: list[list[int]]) -> list[list[int]]:
        return [list(row) for row in zip(*square[::-1])]

    def flatten(square: list[list[int]]) -> tuple[int, ...]:
        return tuple(value for row in square for value in row)

    variants: list[tuple[int, ...]] = []
    current = source
    for _ in range(4):
        variants.append(flatten(current))
        variants.append(flatten([row[::-1] for row in current]))
        current = rotate(current)
    return variants


def canonical(cells: list[int]) -> tuple[int, ...]:
    return min(transforms(cells))


def moment_metrics(cells: list[int]) -> dict[str, Any]:
    heights = [[value - MEAN_HEIGHT for value in row] for row in matrix(cells)]
    coefficients: dict[str, float] = {}
    mode_energy: dict[str, float] = {}

    for x_degree in range(N):
        for y_degree in range(N):
            if x_degree == y_degree == 0:
                continue
            coefficient = sum(
                BASIS[x_degree][column]
                * BASIS[y_degree][row]
                * heights[row][column]
                for row in range(N)
                for column in range(N)
            )
            name = f"M{x_degree}{y_degree}"
            coefficients[name] = round(coefficient, 8)
            mode_energy[name] = round(coefficient * coefficient, 8)

    axial_names = [
        name
        for name in mode_energy
        if (name[1] == "0") != (name[2] == "0")
    ]
    interaction_names = [
        name for name in mode_energy if name[1] != "0" and name[2] != "0"
    ]
    degree_energy = {
        str(degree): round(
            sum(
                energy
                for name, energy in mode_energy.items()
                if name in interaction_names and int(name[1]) + int(name[2]) == degree
            ),
            8,
        )
        for degree in range(2, 7)
    }
    axial_energy = sum(mode_energy[name] for name in axial_names)
    interaction_energy = sum(mode_energy[name] for name in interaction_names)
    low_order_energy = degree_energy["2"] + degree_energy["3"]
    high_order_energy = sum(degree_energy[str(degree)] for degree in range(4, 7))
    spectral_centroid = (
        sum(float(degree) * degree_energy[str(degree)] for degree in range(2, 7))
        / interaction_energy
        if interaction_energy
        else 0.0
    )

    return {
        "coefficients": coefficients,
        "modeEnergy": mode_energy,
        "degreeEnergy": degree_energy,
        "axialEnergy": round(axial_energy, 8),
        "interactionEnergy": round(interaction_energy, 8),
        "lowOrderEnergy": round(low_order_energy, 8),
        "highOrderEnergy": round(high_order_energy, 8),
        "spectralCentroid": round(spectral_centroid, 8),
    }


def classify(cells: list[int]) -> list[str]:
    labels: list[str] = []
    if is_pandiagonal(cells):
        labels.append("pandiagonal")
    if is_associative(cells):
        labels.append("associative")
    if is_most_perfect(cells):
        labels.append("most-perfect")
    if not labels:
        labels.append("ordinary")
    return labels


def analyze_record(
    cells: list[int],
    *,
    record_id: str,
    cohort: str,
    source_id: int | None = None,
    swaps: int = 0,
    source_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    rows, columns, diagonals = line_sums(cells)
    line_residuals = [value - MAGIC_SUM for value in rows + columns + diagonals]
    metrics = moment_metrics(cells)
    variants = transforms(cells)
    source_metadata = source_metadata or {}

    return {
        "recordId": record_id,
        "cohort": cohort,
        "sourceId": source_id,
        "swaps": swaps,
        "cells": cells,
        "isMagic": is_magic(cells),
        "dudeneyGroup": source_metadata.get("dudeney_group"),
        "dudeneyLabel": (
            GROUP_LABELS[source_metadata["dudeney_group"]]
            if source_metadata.get("dudeney_group")
            else None
        ),
        "groupOrientation": source_metadata.get("group_orientation"),
        "complementPair": source_metadata.get("complement_pair"),
        "complementId": source_metadata.get("complement_id"),
        "selfComplementary": (
            source_metadata.get("complement_pair") == 999
            if source_metadata
            else canonical([17 - value for value in cells]) == canonical(cells)
        ),
        "classes": classify(cells),
        "d4OrbitSize": len(set(variants)),
        "lineSums": {"rows": rows, "columns": columns, "diagonals": diagonals},
        "lineDefectEnergy": sum(value * value for value in line_residuals),
        **metrics,
    }


def load_source(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            cells = [int(row[f"cell_{index}"]) for index in range(1, 17)]
            records.append(
                {
                    "id": int(row["id"]),
                    "dudeney_group": int(row["dudeney_group"]),
                    "group_orientation": int(row["group_orientation"]),
                    "complement_pair": int(row["complement_pair"]),
                    "complement_id": int(row["complement_id"]),
                    "cells": cells,
                }
            )
    return records


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
                    sum(record["spectralCentroid"] for record in subset) / len(subset),
                    6,
                ),
            }
        )
    return summaries


def write_csv(records: list[dict[str, Any]], path: Path) -> None:
    mode_names = [
        f"M{x_degree}{y_degree}"
        for x_degree in range(N)
        for y_degree in range(N)
        if not (x_degree == y_degree == 0)
    ]
    fieldnames = [
        "record_id",
        "cohort",
        "source_id",
        "swaps",
        "is_magic",
        "dudeney_group",
        "classes",
        "cells",
        "line_defect_energy",
        "axial_energy",
        "interaction_energy",
        "low_order_energy",
        "high_order_energy",
        "spectral_centroid",
        *[f"energy_{name}" for name in mode_names],
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            writer.writerow(
                {
                    "record_id": record["recordId"],
                    "cohort": record["cohort"],
                    "source_id": record["sourceId"],
                    "swaps": record["swaps"],
                    "is_magic": record["isMagic"],
                    "dudeney_group": record["dudeneyGroup"],
                    "classes": "|".join(record["classes"]),
                    "cells": " ".join(str(value) for value in record["cells"]),
                    "line_defect_energy": record["lineDefectEnergy"],
                    "axial_energy": record["axialEnergy"],
                    "interaction_energy": record["interactionEnergy"],
                    "low_order_energy": record["lowOrderEnergy"],
                    "high_order_energy": record["highOrderEnergy"],
                    "spectral_centroid": record["spectralCentroid"],
                    **{
                        f"energy_{name}": record["modeEnergy"][name]
                        for name in mode_names
                    },
                }
            )


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input", type=Path, default=root / "data" / "magic_squares_880.csv"
    )
    parser.add_argument("--output-dir", type=Path, default=root / "data")
    parser.add_argument("--random-count", type=int, default=880)
    parser.add_argument("--seed", type=int, default=20260709)
    args = parser.parse_args()

    source = load_source(args.input)
    if len(source) != 880:
        raise ValueError(f"Expected 880 source records, got {len(source)}")
    canonical_forms = [canonical(record["cells"]) for record in source]
    if len(set(canonical_forms)) != 880:
        raise ValueError("Source contains duplicate D4 equivalence classes")
    if not all(is_magic(record["cells"]) for record in source):
        raise ValueError("Every source record must be a normal order-4 magic square")

    rng = random.Random(args.seed)
    results: list[dict[str, Any]] = []
    for record in source:
        results.append(
            analyze_record(
                record["cells"],
                record_id=f"M{record['id']:03d}",
                cohort="magic",
                source_id=record["id"],
                source_metadata=record,
            )
        )

    for swap_count in (1, 2, 3):
        for record in source:
            perturbed = swapped_copy(record["cells"], swap_count, rng)
            results.append(
                analyze_record(
                    perturbed,
                    record_id=f"S{swap_count}-{record['id']:03d}",
                    cohort=f"swap-{swap_count}",
                    source_id=record["id"],
                    swaps=swap_count,
                    source_metadata=record,
                )
            )

    for index in range(1, args.random_count + 1):
        cells = list(range(1, 17))
        rng.shuffle(cells)
        results.append(
            analyze_record(
                cells,
                record_id=f"R{index:03d}",
                cohort="random",
            )
        )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "metadata": {
            "order": N,
            "magicSum": MAGIC_SUM,
            "sourceCount": len(source),
            "expandedOrientedCount": len(source) * 8,
            "seed": args.seed,
            "randomCount": args.random_count,
            "heightEnergy": TOTAL_HEIGHT_ENERGY,
            "coordinates": COORDINATES,
            "basis": [[round(value, 10) for value in row] for row in BASIS],
            "groupLabels": GROUP_LABELS,
            "cohortSummary": summarize(results),
            "dudeneyCounts": dict(
                sorted(Counter(record["dudeney_group"] for record in source).items())
            ),
        },
        "records": results,
    }
    json_path = args.output_dir / "analysis.json"
    csv_path = args.output_dir / "analysis.csv"
    serialized = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
    json_path.write_text(serialized, encoding="utf-8")
    (args.output_dir / "analysis-data.js").write_text(
        f"window.MAGIC_ANALYSIS={serialized};\n",
        encoding="utf-8",
    )
    write_csv(results, csv_path)
    print(
        f"Wrote {len(results)} records to {json_path}, {csv_path}, "
        "and analysis-data.js"
    )


if __name__ == "__main__":
    main()
