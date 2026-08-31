#!/usr/bin/env python3
"""Data size and browser performance feasibility audit (stdlib only)."""

from __future__ import annotations

import gzip
import json
import sys
import time
from pathlib import Path

ROOT = Path("/Users/kylemathewson/MagicSK/MagicMomentExplorer")
OUT = Path(__file__).resolve().parents[1] / "evidence"


def human(n: int) -> str:
    if n < 1024:
        return f"{n} B"
    if n < 1024 * 1024:
        return f"{n / 1024:.2f} KB"
    return f"{n / (1024 * 1024):.2f} MB"


def main() -> int:
    files = {
        "magic_squares_880.csv": ROOT / "data" / "magic_squares_880.csv",
        "analysis.csv": ROOT / "data" / "analysis.csv",
        "analysis.json": ROOT / "data" / "analysis.json",
    }

    sizes: dict[str, dict[str, str | int]] = {}
    for name, path in files.items():
        raw = path.read_bytes()
        gz = gzip.compress(raw, compresslevel=9)
        sizes[name] = {
            "bytes": len(raw),
            "human": human(len(raw)),
            "gzip_bytes": len(gz),
            "gzip_human": human(len(gz)),
        }

    # Simulate analysis-data.js wrapper size
    json_text = files["analysis.json"].read_text(encoding="utf-8")
    js_wrapper = f"window.MAGIC_ANALYSIS={json_text};\n"
    sizes["analysis-data.js (projected)"] = {
        "bytes": len(js_wrapper.encode("utf-8")),
        "human": human(len(js_wrapper.encode("utf-8"))),
        "gzip_bytes": len(gzip.compress(js_wrapper.encode("utf-8"), 9)),
        "gzip_human": human(len(gzip.compress(js_wrapper.encode("utf-8"), 9))),
    }

    # Parse / filter timing (proxy for in-browser work)
    t0 = time.perf_counter()
    payload = json.loads(json_text)
    parse_ms = (time.perf_counter() - t0) * 1000

    records = payload["records"]
    t0 = time.perf_counter()
    filtered = [r for r in records if r["cohort"] == "magic" and r["dudeneyGroup"] == 6]
    filter_ms = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    sorted_recs = sorted(records, key=lambda r: r["spectralCentroid"], reverse=True)
    sort_ms = (time.perf_counter() - t0) * 1000

    # Compact schema estimate: drop coefficients, keep summaries
    compact_records = []
    for r in records:
        compact_records.append(
            {
                "recordId": r["recordId"],
                "cohort": r["cohort"],
                "sourceId": r["sourceId"],
                "cells": r["cells"],
                "isMagic": r["isMagic"],
                "dudeneyGroup": r["dudeneyGroup"],
                "classes": r["classes"],
                "lineDefectEnergy": r["lineDefectEnergy"],
                "axialEnergy": r["axialEnergy"],
                "degreeEnergy": r["degreeEnergy"],
                "interactionEnergy": r["interactionEnergy"],
                "spectralCentroid": r["spectralCentroid"],
            }
        )
    compact_json = json.dumps(
        {"metadata": payload["metadata"], "records": compact_records},
        separators=(",", ":"),
    )
    compact_bytes = len(compact_json.encode("utf-8"))

    report = {
        "file_sizes": sizes,
        "record_count": len(records),
        "timing_python_proxy_ms": {
            "json_parse": round(parse_ms, 2),
            "filter_magic_group6": round(filter_ms, 2),
            "sort_by_spectral_centroid": round(sort_ms, 2),
        },
        "compact_schema_no_coefficients_bytes": compact_bytes,
        "compact_schema_human": human(compact_bytes),
        "compact_gzip_human": human(len(gzip.compress(compact_json.encode("utf-8"), 9))),
        "feasibility_notes": [
            "Full 4.4MB JSON inline in analysis-data.js is viable on modern desktop browsers over HTTP.",
            "file:// loading of multi-MB fetch targets is unreliable; inline script or local server required.",
            "Pagination (index.html uses page controls) recommended for 4400-row DOM tables.",
            "Dropping coefficients saves roughly half payload if detail view recomputes or lazy-loads.",
        ],
    }

    out_path = OUT / "size_performance_audit.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
