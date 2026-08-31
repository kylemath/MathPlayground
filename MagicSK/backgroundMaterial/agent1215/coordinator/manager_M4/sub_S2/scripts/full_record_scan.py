#!/usr/bin/env python3
"""Full 4400-record scan for Parseval, coefficient, and energy partition consistency."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

N = 4
MEAN_HEIGHT = 8.5
COORDINATES = (-1.5, -0.5, 0.5, 1.5)
ANALYSIS_JSON = Path("/Users/kylemathewson/MagicSK/MagicMomentExplorer/data/analysis.json")


def dot(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right))


def orthonormal_polynomials() -> list[list[float]]:
    basis: list[list[float]] = []
    for degree in range(N):
        vector = [coordinate**degree for coordinate in COORDINATES]
        for previous in basis:
            projection = dot(vector, previous)
            vector = [value - projection * prior for value, prior in zip(vector, previous)]
        norm = math.sqrt(dot(vector, vector))
        basis.append([value / norm for value in vector])
    return basis


BASIS = orthonormal_polynomials()


def matrix(cells: list[int]) -> list[list[int]]:
    return [cells[offset : offset + N] for offset in range(0, N * N, N)]


def main() -> int:
    with ANALYSIS_JSON.open(encoding="utf-8") as handle:
        records = json.load(handle)["records"]

    parseval_failures = []
    coeff_failures = []
    energy_partition_failures = []
    recon_failures = []
    height_energy_failures = []

    for record in records:
        heights = [[value - MEAN_HEIGHT for value in row] for row in matrix(record["cells"])]
        height_energy = sum(value * value for row in heights for value in row)

        coefficients = {}
        for x_degree in range(N):
            for y_degree in range(N):
                coefficients[(x_degree, y_degree)] = sum(
                    BASIS[x_degree][column] * BASIS[y_degree][row] * heights[row][column]
                    for row in range(N)
                    for column in range(N)
                )

        coeff_energy = sum(value * value for value in coefficients.values())
        if abs(height_energy - coeff_energy) > 1e-6:
            parseval_failures.append(record["recordId"])

        for name, shipped in record["coefficients"].items():
            recomputed = coefficients[(int(name[1]), int(name[2]))]
            if abs(recomputed - shipped) > 1e-5:
                coeff_failures.append(record["recordId"])
                break

        m00_energy = coefficients[(0, 0)] ** 2
        shipped_sum = record["axialEnergy"] + record["interactionEnergy"] + m00_energy
        if abs(shipped_sum - height_energy) > 1e-4:
            energy_partition_failures.append(record["recordId"])

        reconstructed = [
            [
                sum(
                    coefficients[(x_degree, y_degree)]
                    * BASIS[x_degree][column]
                    * BASIS[y_degree][row]
                    for x_degree in range(N)
                    for y_degree in range(N)
                )
                for column in range(N)
            ]
            for row in range(N)
        ]
        max_err = max(
            abs(reconstructed[row][column] - heights[row][column])
            for row in range(N)
            for column in range(N)
        )
        if max_err > 1e-6:
            recon_failures.append(record["recordId"])

        if abs(height_energy - 340.0) > 1e-9:
            height_energy_failures.append(record["recordId"])

    report = {
        "total_records": len(records),
        "parseval_failures": len(parseval_failures),
        "coeff_failures": len(coeff_failures),
        "energy_partition_failures": len(energy_partition_failures),
        "reconstruction_failures": len(recon_failures),
        "height_energy_failures": len(height_energy_failures),
        "sample_parseval_failures": parseval_failures[:10],
        "sample_coeff_failures": coeff_failures[:10],
    }

    out = Path(__file__).resolve().parents[1] / "outputs" / "full_record_scan.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("=== Full Record Scan (4400) ===")
    for key, value in report.items():
        if key.startswith("sample"):
            continue
        print(f"{key}: {value}")
    print(f"Wrote {out}")

    ok = all(value == 0 for key, value in report.items() if key.endswith("_failures"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
