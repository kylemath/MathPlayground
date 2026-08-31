#!/usr/bin/env python3
"""CLI: enumerate or ingest normal 4x4 magic squares with D4 canonicalization."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import time
from collections import Counter
from pathlib import Path

from d4 import canonical, d4_orbit, d4_transforms, is_d4_canonical, orbit_size, stabilizer_size
from enumerate import enumerate_oriented_magic_squares, row_mask_count
from validate import is_magic, is_normal, validate


def grid_checksum(grids: tuple[tuple[int, ...], ...]) -> str:
    """SHA-256 over sorted newline-separated flat grids (manager-compatible)."""
    payload = "\n".join(",".join(str(v) for v in grid) for grid in sorted(grids)) + "\n"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load_csv(path: Path) -> tuple[tuple[int, ...], ...]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    grids = []
    for row in rows:
        grids.append(tuple(int(row[f"cell_{index}"]) for index in range(1, 17)))
    return tuple(grids)


def analyze_oriented(oriented: tuple[tuple[int, ...], ...]) -> dict[str, object]:
    canonical_set: dict[tuple[int, ...], list[tuple[int, ...]]] = {}
    for grid in oriented:
        canon = canonical(grid)
        canonical_set.setdefault(canon, []).append(grid)

    canonical_grids = tuple(sorted(canonical_set))
    orbit_sizes = Counter(orbit_size(grid) for grid in oriented)
    stabilizers = Counter(stabilizer_size(grid) for grid in oriented)
    canonical_orbit_sizes = Counter(orbit_size(grid) for grid in canonical_grids)
    canonical_stabilizers = Counter(stabilizer_size(grid) for grid in canonical_grids)

    oriented_union = frozenset(
        image for grid in oriented for image in d4_orbit(grid)
    )

    return {
        "oriented_count": len(oriented),
        "canonical_count": len(canonical_grids),
        "oriented_union_count": len(oriented_union),
        "all_oriented_magic": all(is_magic(grid) for grid in oriented),
        "all_oriented_normal": all(is_normal(grid) for grid in oriented),
        "all_canonical_are_canonical_form": all(is_d4_canonical(grid) for grid in canonical_grids),
        "orbit_size_distribution_oriented": dict(sorted(orbit_sizes.items())),
        "stabilizer_size_distribution_oriented": dict(sorted(stabilizers.items())),
        "orbit_size_distribution_canonical": dict(sorted(canonical_orbit_sizes.items())),
        "stabilizer_size_distribution_canonical": dict(sorted(canonical_stabilizers.items())),
        "canonical_checksum_sha256": grid_checksum(canonical_grids),
        "oriented_checksum_sha256": grid_checksum(oriented),
        "first_canonical_grid": list(canonical_grids[0]) if canonical_grids else [],
        "last_canonical_grid": list(canonical_grids[-1]) if canonical_grids else [],
    }


def run_enumerate(output: Path | None) -> dict[str, object]:
    start = time.perf_counter()
    oriented = enumerate_oriented_magic_squares()
    elapsed = time.perf_counter() - start

    report = analyze_oriented(oriented)
    report["mode"] = "enumerate"
    report["algorithm"] = "sum-34 row masks; first three rows force fourth by columns"
    report["row_mask_count"] = row_mask_count()
    report["enumeration_seconds"] = round(elapsed, 6)
    report["literature_oriented_expected"] = 7040
    report["literature_canonical_expected"] = 880

    if output:
        output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def run_ingest(csv_path: Path, output: Path | None) -> dict[str, object]:
    start = time.perf_counter()
    ingested = load_csv(csv_path)
    elapsed = time.perf_counter() - start

    report = analyze_oriented(ingested)
    report["mode"] = "ingest"
    report["source"] = str(csv_path.resolve())
    report["ingest_seconds"] = round(elapsed, 6)
    report["record_count"] = len(ingested)
    report["rows_already_lexicographically_canonical"] = sum(
        grid == canonical(grid) for grid in ingested
    )

    oriented_from_canonical = frozenset(
        image for grid in ingested for image in d4_orbit(grid)
    )
    report["oriented_union_from_ingested_canonical"] = len(oriented_from_canonical)

    if output:
        output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def run_crosscheck(csv_path: Path, output: Path | None) -> dict[str, object]:
    enum_report = run_enumerate(None)
    ingest_report = run_ingest(csv_path, None)

    enum_canonical = set()
    oriented = enumerate_oriented_magic_squares()
    for grid in oriented:
        enum_canonical.add(canonical(grid))

    ingested = load_csv(csv_path)
    ingest_canonical = {canonical(grid) for grid in ingested}

    report = {
        "mode": "crosscheck",
        "enumeration": {
            "oriented_count": enum_report["oriented_count"],
            "canonical_count": enum_report["canonical_count"],
            "canonical_checksum_sha256": enum_report["canonical_checksum_sha256"],
        },
        "ingestion": {
            "record_count": ingest_report["record_count"],
            "canonical_checksum_sha256": grid_checksum(tuple(sorted(ingested))),
            "source": ingest_report["source"],
        },
        "canonical_sets_match": enum_canonical == ingest_canonical,
        "enum_only_count": len(enum_canonical - ingest_canonical),
        "ingest_only_count": len(ingest_canonical - enum_canonical),
        "all_ingested_in_enum_oriented_union": all(
            grid in frozenset(oriented) for grid in ingested
        ),
        "all_ingested_are_canonical": ingest_report["rows_already_lexicographically_canonical"],
    }

    if output:
        output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    enum_p = sub.add_parser("enumerate", help="Row-mask enumeration of all oriented squares")
    enum_p.add_argument("--output", type=Path, help="JSON results path")

    ingest_p = sub.add_parser("ingest", help="Load and validate a CSV of canonical squares")
    ingest_p.add_argument("csv_path", type=Path)
    ingest_p.add_argument("--output", type=Path)

    cross_p = sub.add_parser("crosscheck", help="Compare enumeration against an external CSV")
    cross_p.add_argument("csv_path", type=Path)
    cross_p.add_argument("--output", type=Path)

    inspect_p = sub.add_parser("inspect", help="Validate one grid from 16 integers")
    inspect_p.add_argument("cells", type=int, nargs=16)

    args = parser.parse_args()

    if args.command == "enumerate":
        report = run_enumerate(args.output)
    elif args.command == "ingest":
        report = run_ingest(args.csv_path, args.output)
    elif args.command == "crosscheck":
        report = run_crosscheck(args.csv_path, args.output)
    elif args.command == "inspect":
        grid = tuple(args.cells)
        report = {
            "grid": list(grid),
            "validate": validate(grid),
            "canonical": list(canonical(grid)),
            "orbit_size": orbit_size(grid),
            "stabilizer_size": stabilizer_size(grid),
            "d4_transforms": [list(image) for image in d4_transforms(grid)],
        }
    else:
        parser.error(f"unknown command {args.command}")
        return 2

    json.dump(report, sys.stdout, indent=2, sort_keys=True)
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
