#!/usr/bin/env python3
"""S1 independent verification: provenance, D4 orbits, 880/7040, classification.

Standard library only. Reads MagicMomentExplorer artifacts read-only.
"""

from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from itertools import permutations
from pathlib import Path
from typing import Iterable

N = 4
MAGIC = 34
COMPLEMENT = 17
Grid = tuple[int, ...]

REPO = Path("/Users/kylemathewson/MagicSK")
SOURCE_CSV = REPO / "MagicMomentExplorer/data/magic_squares_880.csv"
ANALYSIS_JSON = REPO / "MagicMomentExplorer/data/analysis.json"
FETCH_SCRIPT = REPO / "MagicMomentExplorer/scripts/fetch_source.py"


# --- D4 via explicit 2x2 matrix ops (independent of coordinator indexing) ---


def as_matrix(g: Grid) -> tuple[tuple[int, ...], ...]:
    return tuple(g[r * N : (r + 1) * N] for r in range(N))


def from_matrix(m: tuple[tuple[int, ...], ...]) -> Grid:
    return tuple(v for row in m for v in row)


def rot90(m: tuple[tuple[int, ...], ...]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(m[N - 1 - c][r] for c in range(N)) for r in range(N))


def flip_h(m: tuple[tuple[int, ...], ...]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(reversed(row)) for row in m)


def d4_orbit(g: Grid) -> frozenset[Grid]:
    seen: set[Grid] = set()
    m = as_matrix(g)
    cur = m
    for _ in range(4):
        seen.add(from_matrix(cur))
        seen.add(from_matrix(flip_h(cur)))
        cur = rot90(cur)
    return frozenset(seen)


def frenicle_min(g: Grid) -> Grid:
    return min(d4_orbit(g))


def is_magic(g: Grid) -> bool:
    if sorted(g) != list(range(1, 17)):
        return False
    m = as_matrix(g)
    rows = [sum(r) for r in m]
    cols = [sum(m[r][c] for r in range(N)) for c in range(N)]
    d1 = sum(m[i][i] for i in range(N))
    d2 = sum(m[i][N - 1 - i] for i in range(N))
    return all(x == MAGIC for x in rows + cols + [d1, d2])


def broken_diagonals(g: Grid) -> list[tuple[int, ...]]:
    m = as_matrix(g)
    out: list[tuple[int, ...]] = []
    for off in range(N):
        out.append(tuple(m[r][(r + off) % N] for r in range(N)))
        out.append(tuple(m[r][(off - r) % N] for r in range(N)))
    return out


def opposite_short_diagonals(g: Grid) -> list[tuple[int, ...]]:
    m = as_matrix(g)
    return [
        (m[0][0], m[1][1], m[2][3], m[3][2]),
        (m[0][3], m[1][2], m[2][1], m[3][0]),
        (m[0][1], m[1][0], m[2][2], m[3][3]),
        (m[0][2], m[1][3], m[2][0], m[3][1]),
    ]


def is_pandiagonal(g: Grid) -> bool:
    return is_magic(g) and all(sum(d) == MAGIC for d in broken_diagonals(g))


def is_semi_pandiagonal(g: Grid) -> bool:
    return is_magic(g) and all(sum(d) == MAGIC for d in opposite_short_diagonals(g))


def is_associative(g: Grid) -> bool:
    m = as_matrix(g)
    return all(
        m[r][c] + m[N - 1 - r][N - 1 - c] == COMPLEMENT
        for r in range(N)
        for c in range(N)
    )


def classify_structural(g: Grid) -> dict[str, bool]:
    return {
        "pandiagonal": is_pandiagonal(g),
        "semi_pandiagonal": is_semi_pandiagonal(g),
        "associative": is_associative(g),
    }


def load_csv(path: Path) -> list[tuple[dict[str, str], Grid]]:
    with path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    return [
        (row, tuple(int(row[f"cell_{i}"]) for i in range(1, 17)))
        for row in rows
    ]


def audit_csv(path: Path) -> dict[str, object]:
    records = load_csv(path)
    grids = [g for _, g in records]
    canon = {frenicle_min(g) for g in grids}
    oriented_union: set[Grid] = set()
    for g in grids:
        oriented_union |= set(d4_orbit(g))

    orbit_sizes = Counter(len(d4_orbit(g)) for g in grids)
    by_canon = {frenicle_min(g): row for row, g in records}

    comp_ok = 0
    for row, g in records:
        comp_key = frenicle_min(tuple(COMPLEMENT - x for x in g))
        declared = int(row["complement_id"])
        sid = int(row["id"])
        if declared == 999 and comp_key == frenicle_min(g):
            comp_ok += 1
        elif comp_key in by_canon and declared == int(by_canon[comp_key]["id"]):
            comp_ok += 1

    dudeney = Counter(int(r["dudeney_group"]) for r, _ in records)

    mismatches: list[dict[str, object]] = []
    for row, g in records:
        props = classify_structural(g)
        grp = int(row["dudeney_group"])
        if grp == 1 and not props["pandiagonal"]:
            mismatches.append({"id": row["id"], "issue": "group I not pandiagonal"})
        if grp == 3 and not props["associative"]:
            mismatches.append({"id": row["id"], "issue": "group III not associative"})
        if props["pandiagonal"] and props["associative"]:
            mismatches.append({"id": row["id"], "issue": "both pandiagonal and associative"})

    prop_counts = Counter()
    for g in grids:
        for k, v in classify_structural(g).items():
            if v:
                prop_counts[k] += 1

    return {
        "source": str(path.resolve()),
        "record_count": len(records),
        "ids_1_to_880": [int(r["id"]) for r, _ in records] == list(range(1, 881)),
        "all_magic": all(is_magic(g) for g in grids),
        "unique_literal": len(set(grids)),
        "unique_d4_canonical": len(canon),
        "all_rows_frenicle_canonical": sum(g == frenicle_min(g) for g in grids),
        "d4_orbit_size_distribution": dict(sorted(orbit_sizes.items())),
        "oriented_union_count": len(oriented_union),
        "complement_declarations_consistent": comp_ok,
        "dudeney_group_distribution": dict(sorted(dudeney.items())),
        "structural_property_counts": dict(sorted(prop_counts.items())),
        "dudeney_label_mismatches": mismatches,
    }


def enumerate_frenicle_oriented() -> list[Grid]:
    """Backtracking with Frénicle anchor: cell_1=1, cell_2 < cell_5."""
    results: list[Grid] = []
    cells: list[int | None] = [None] * 16
    used = [False] * 17

    def row_ok(r: int) -> bool:
        row = cells[r * 4 : (r + 1) * 4]
        if any(v is None for v in row):
            return True
        return sum(v for v in row if v is not None) == MAGIC  # type: ignore[misc]

    def col_ok(c: int) -> bool:
        col = [cells[r * 4 + c] for r in range(4)]
        if any(v is None for v in col):
            return True
        return sum(v for v in col if v is not None) == MAGIC  # type: ignore[misc]

    def go(idx: int) -> None:
        if idx == 16:
            g = tuple(cells)  # type: ignore[misc]
            if is_magic(g):
                results.append(g)
            return
        r, c = divmod(idx, 4)
        cands: Iterable[int]
        if idx == 0:
            cands = (1,)
        elif idx == 1:
            cands = range(2, 17)
        elif idx == 4:
            upper = cells[1]
            cands = range(2, upper) if upper is not None else range(2, 17)
        else:
            cands = range(1, 17)
        for v in cands:
            if used[v]:
                continue
            cells[idx] = v
            used[v] = True
            if row_ok(r) and col_ok(c):
                go(idx + 1)
            cells[idx] = None
            used[v] = False

    go(0)
    return results


def verify_enumeration() -> dict[str, object]:
    frenicle_list = enumerate_frenicle_oriented()
    canon_set = set(frenicle_list)
    oriented_from_canon: set[Grid] = set()
    for g in frenicle_list:
        oriented_from_canon |= set(d4_orbit(g))

    csv_records = load_csv(SOURCE_CSV)
    csv_grids = {frenicle_min(g) for _, g in csv_records}

    return {
        "enumerated_frenicle_count": len(frenicle_list),
        "enumerated_unique_frenicle": len(canon_set),
        "enumerated_oriented_via_d4_expansion": len(oriented_from_canon),
        "csv_frenicle_set_matches_enumeration": csv_grids == canon_set,
        "csv_missing_from_enum": len(csv_grids - canon_set),
        "enum_extra_not_in_csv": len(canon_set - csv_grids),
        "orbit_sizes_on_enumerated": dict(
            sorted(Counter(len(d4_orbit(g)) for g in frenicle_list).items())
        ),
    }


def verify_analysis_metadata() -> dict[str, object]:
    meta = json.loads(ANALYSIS_JSON.read_text(encoding="utf-8"))["metadata"]
    csv_audit = audit_csv(SOURCE_CSV)
    cohort_total = sum(c["count"] for c in meta["cohortSummary"])
    return {
        "analysis_sourceCount": meta["sourceCount"],
        "analysis_expandedOrientedCount": meta["expandedOrientedCount"],
        "analysis_dudeneyCounts": meta["dudeneyCounts"],
        "dudeney_matches_csv": meta["dudeneyCounts"] == csv_audit["dudeney_group_distribution"],
        "sourceCount_matches_csv": meta["sourceCount"] == csv_audit["record_count"],
        "expanded_is_8x_source": meta["expandedOrientedCount"] == meta["sourceCount"] * 8,
        "cohort_record_total": cohort_total,
        "expected_cohort_total": 880 * 5,
        "cohort_counts": {c["cohort"]: c["count"] for c in meta["cohortSummary"]},
    }


def provenance_notes() -> dict[str, object]:
    text = FETCH_SCRIPT.read_text(encoding="utf-8")
    return {
        "fetch_script_present": FETCH_SCRIPT.is_file(),
        "source_urls_in_fetch_script": [
            line.strip().strip('",')
            for line in text.splitlines()
            if "recmath.org" in line and "order4list" in line
        ],
        "local_csv_exists": SOURCE_CSV.is_file(),
        "local_csv_bytes": SOURCE_CSV.stat().st_size if SOURCE_CSV.is_file() else 0,
    }


def main() -> int:
    out_dir = Path(__file__).resolve().parents[1] / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)

    report = {
        "provenance": provenance_notes(),
        "csv_audit": audit_csv(SOURCE_CSV),
        "enumeration": verify_enumeration(),
        "analysis_crosscheck": verify_analysis_metadata(),
    }

    out_json = out_dir / "s1_independent_verify.json"
    out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
