#!/usr/bin/env python3
"""End-to-end reproducibility and control-protocol alignment audit."""

from __future__ import annotations

import hashlib
import json
import random
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path("/Users/kylemathewson/MagicSK/MagicMomentExplorer")
OUT = Path(__file__).resolve().parents[1] / "evidence"
N = 4


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def swapped_copy_analyze(cells: list[int], count: int, rng: random.Random) -> list[int]:
    """Mirror MagicMomentExplorer/scripts/analyze.py swapped_copy."""
    result = cells.copy()
    positions = rng.sample(range(N * N), count * 2)
    for index in range(0, len(positions), 2):
        left, right = positions[index : index + 2]
        result[left], result[right] = result[right], result[left]
    return result


def compare_control_protocols() -> dict:
    """Document PRNG / swap semantics divergence vs M2 Mulberry32 sequential protocol."""
    base = list(range(1, 17))
    seed = 20260709

    py_rng = random.Random(seed)
    app_swap1 = swapped_copy_analyze(base, 1, py_rng)
    py_rng2 = random.Random(seed)
    app_random = base.copy()
    py_rng2.shuffle(app_random)

    return {
        "app_uses_python_random": True,
        "m2_recommends_mulberry32": True,
        "app_swap_semantics": "simultaneous k disjoint pairs via rng.sample(16, 2k)",
        "m2_default_swap_semantics": "sequential k transpositions; uniform pair with replacement",
        "seed": seed,
        "example_swap1_first8_cells_app": app_swap1[:8],
        "example_random_first8_cells_app": app_random[:8],
        "cross_stream_risk": "Control cohorts will not match M2 control_ensembles.py unless protocols aligned",
    }


def run_analyze_regen() -> dict:
    with tempfile.TemporaryDirectory(prefix="s3_audit_") as tmp:
        out_dir = Path(tmp) / "out"
        cmd = [
            sys.executable,
            str(ROOT / "scripts" / "analyze.py"),
            "--input",
            str(ROOT / "data" / "magic_squares_880.csv"),
            "--output-dir",
            str(out_dir),
            "--seed",
            "20260709",
            "--random-count",
            "880",
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        result = {
            "command": " ".join(cmd),
            "returncode": proc.returncode,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip()[:2000],
        }
        if proc.returncode != 0:
            return result

        existing = ROOT / "data" / "analysis.json"
        regenerated = out_dir / "analysis.json"
        result["existing_sha256"] = sha256_file(existing)
        result["regenerated_sha256"] = sha256_file(regenerated)
        result["json_identical"] = result["existing_sha256"] == result["regenerated_sha256"]

        # Spot-check first magic record metrics
        with existing.open(encoding="utf-8") as f:
            old = json.load(f)["records"][0]
        with regenerated.open(encoding="utf-8") as f:
            new = json.load(f)["records"][0]
        result["first_record_id_match"] = old["recordId"] == new["recordId"]
        result["first_record_interaction_match"] = (
            old["interactionEnergy"] == new["interactionEnergy"]
        )
        return result


def check_basis_alignment() -> dict:
    m2_basis_path = Path(
        "/Users/kylemathewson/MagicSK/backgroundMaterial/agent1215/"
        "coordinator/manager_M2/sub_S1/S1_basis_numeric.json"
    )
    m2 = json.loads(m2_basis_path.read_text(encoding="utf-8"))
    with (ROOT / "data" / "analysis.json").open(encoding="utf-8") as f:
        app_basis = json.load(f)["metadata"]["basis"]

    diffs = []
    for i, row in enumerate(app_basis):
        for j, val in enumerate(row):
            ref = m2["basis_1d"][i][j]
            if abs(val - ref) > 1e-6:
                diffs.append({"i": i, "j": j, "app": val, "m2": ref})

    return {
        "coordinates_match": m2["coords_1d"]
        == json.load((ROOT / "data" / "analysis.json").open(encoding="utf-8"))[
            "metadata"
        ]["coordinates"],
        "basis_max_abs_diff": max(
            (abs(a - b) for a, b in zip(sum(app_basis, []), sum(m2["basis_1d"], []))),
            default=0.0,
        ),
        "basis_mismatch_count": len(diffs),
        "basis_aligned": len(diffs) == 0,
    }


def main() -> int:
    report = {
        "control_protocol_comparison": compare_control_protocols(),
        "analyze_regeneration": run_analyze_regen(),
        "basis_alignment_with_m2": check_basis_alignment(),
        "fetch_source_note": (
            "fetch_source.py requires network; not re-run in this audit "
            "(existing magic_squares_880.csv audited by coordinator_dataset_audit.json)"
        ),
    }
    out_path = OUT / "reproducibility_audit.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["analyze_regeneration"].get("json_identical") else 1


if __name__ == "__main__":
    sys.exit(main())
