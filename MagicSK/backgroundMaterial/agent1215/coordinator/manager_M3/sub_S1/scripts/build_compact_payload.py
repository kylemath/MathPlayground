#!/usr/bin/env python3
"""Build compact magic-moment bundle v1 from read-only upstream analysis artifacts."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import statistics
from pathlib import Path
from typing import Any

MODES = [f"M{x}{y}" for x in range(4) for y in range(4) if not (x == 0 and y == 0)]
CLASS_FLAGS = {
    "pandiagonal": 1,
    "associative": 2,
    "most-perfect": 4,
    "ordinary": 8,
}
SCHEMA_VERSION = "1.0.0"


def class_flags(classes: list[str]) -> int:
    return sum(CLASS_FLAGS.get(label, 0) for label in classes)


def stat_block(values: list[float]) -> dict[str, Any]:
    return {
        "n": len(values),
        "mean": round(statistics.mean(values), 2),
        "min": round(min(values), 2),
        "max": round(max(values), 2),
    }


def compact_record(record: dict[str, Any]) -> list[Any]:
    coefficients = [round(record["coefficients"][mode], 4) for mode in MODES]
    energy = [
        round(record["axialEnergy"], 2),
        round(record["interactionEnergy"], 2),
        round(record["lowOrderEnergy"], 2),
        round(record["highOrderEnergy"], 2),
        round(record["spectralCentroid"], 4),
    ]
    return [
        record["sourceId"],
        record["cells"],
        record["dudeneyGroup"],
        record["groupOrientation"],
        record["complementPair"],
        record["complementId"],
        class_flags(record["classes"]),
        coefficients,
        energy,
    ]


def control_aggregates(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[tuple[str, int], list[dict[str, Any]]] = {}
    for record in records:
        if record["cohort"] == "magic" and record["swaps"] == 0:
            continue
        buckets.setdefault((record["cohort"], record["swaps"]), []).append(record)

    aggregates: list[dict[str, Any]] = []
    for (cohort, swaps), group in sorted(buckets.items()):
        aggregates.append(
            {
                "cohort": cohort,
                "swaps": swaps,
                "interactionEnergy": stat_block([r["interactionEnergy"] for r in group]),
                "highOrderEnergy": stat_block([r["highOrderEnergy"] for r in group]),
                "lowOrderEnergy": stat_block([r["lowOrderEnergy"] for r in group]),
                "isMagicRate": round(sum(1 for r in group if r["isMagic"]) / len(group), 4),
            }
        )
    return aggregates


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_bundle(analysis_path: Path, source_csv: Path) -> dict[str, Any]:
    if not source_csv.is_file():
        raise FileNotFoundError(f"Source CSV required for provenance checksum: {source_csv}")

    with analysis_path.open(encoding="utf-8") as handle:
        analysis = json.load(handle)

    magic_records = [r for r in analysis["records"] if r["cohort"] == "magic"]
    if len(magic_records) != 880:
        raise ValueError(f"Expected 880 magic records, found {len(magic_records)}")

    provenance: dict[str, Any] = {
        "sourceArtifact": source_csv.name,
        "sourceSha256": sha256_file(source_csv),
        "pipeline": "analyze.py",
        "generatedAt": "2026-07-09T00:00:00Z",
        "checksumPolicy": "sha256-of-source-csv-at-build",
        "reproducibility": {
            "randomControlCount": analysis["metadata"].get("randomCount", 880),
            "swapPerturbationCounts": [1, 2, 3],
            "swapPolicy": "sequential-distinct-pairs-seeded",
        },
    }

    meta = {
        "schemaVersion": SCHEMA_VERSION,
        "bundleKind": "magic-moment",
        "order": 4,
        "magicSum": 34,
        "recordCount": 880,
        "orientedUnionCount": 7040,
        "idRange": [1, 880],
        "idPolicy": "stable-source-id-1-based",
        "modes": MODES,
        "modeCount": 15,
        "classFlags": CLASS_FLAGS,
        "recordLayout": {
            "type": "tuple",
            "fields": [
                "id",
                "cells",
                "dudeneyGroup",
                "groupOrientation",
                "complementPair",
                "complementId",
                "classFlags",
                "coefficients",
                "energySummary",
            ],
            "energySummaryFields": [
                "axial",
                "interaction",
                "lowOrder",
                "highOrder",
                "spectralCentroid",
            ],
        },
        "coordinates": analysis["metadata"]["coordinates"],
        "basisRef": "orthonormal-monomials-gram-schmidt-v1",
        "heightEnergy": analysis["metadata"]["heightEnergy"],
        "controlSeed": analysis["metadata"]["seed"],
        "provenance": provenance,
    }

    return {
        "meta": meta,
        "records": [compact_record(record) for record in magic_records],
        "controlAggregates": control_aggregates(analysis["records"]),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--analysis",
        type=Path,
        default=Path("/Users/kylemathewson/MagicSK/MagicMomentExplorer/data/analysis.json"),
        help="Read-only upstream analysis JSON",
    )
    parser.add_argument(
        "--source-csv",
        type=Path,
        default=Path("/Users/kylemathewson/MagicSK/MagicMomentExplorer/data/magic_squares_880.csv"),
        help="Read-only source CSV for checksum provenance",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "data" / "magic_moment_v1_880.json",
    )
    parser.add_argument("--gzip", action="store_true", help="Also write .json.gz sibling")
    parser.add_argument(
        "--example-out",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "data" / "magic_moment_v1_example.json",
        help="Readable example bundle (first 3 records, same provenance)",
    )
    parser.add_argument(
        "--example-count",
        type=int,
        default=3,
        help="Number of records in the example bundle",
    )
    args = parser.parse_args()

    bundle = build_bundle(args.analysis, args.source_csv)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(bundle, separators=(",", ":")).encode("utf-8")
    args.out.write_bytes(payload)
    print(f"wrote {args.out} ({len(payload)} bytes)")
    print(f"sourceSha256 {bundle['meta']['provenance']['sourceSha256']}")
    if args.gzip:
        gz_path = args.out.with_suffix(args.out.suffix + ".gz")
        gz_path.write_bytes(gzip.compress(payload, compresslevel=9))
        print(f"wrote {gz_path} ({gz_path.stat().st_size} bytes)")

    example = {
        "meta": bundle["meta"],
        "records": bundle["records"][: args.example_count],
        "controlAggregates": bundle["controlAggregates"],
    }
    args.example_out.write_text(json.dumps(example, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {args.example_out} ({args.example_count} records)")


if __name__ == "__main__":
    main()
