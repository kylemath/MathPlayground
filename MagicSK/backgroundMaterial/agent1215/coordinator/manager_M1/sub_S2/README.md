# S2 — Normal 4×4 Magic Square Enumeration

Deterministic prototype for enumerating, validating, and D4-canonicalizing all normal order-4 magic squares. Standard library only; no virtual environment required.

## Quick start

```bash
cd /Users/kylemathewson/MagicSK/backgroundMaterial/agent1215/coordinator/manager_M1/sub_S2

# Run invariant tests (re-enumerates ~74s)
python3 test_invariants.py -v

# Full enumeration with JSON report
python3 main.py enumerate --output enumeration_results.json

# Cross-check against external 880-row CSV (read-only)
python3 main.py crosscheck /Users/kylemathewson/MagicSK/MagicMomentExplorer/data/magic_squares_880.csv \
  --output crosscheck_results.json

# Inspect one grid
python3 main.py inspect 1 2 15 16 12 14 3 5 13 7 10 4 8 11 6 9
```

## Algorithm

1. **Row masks** — Precompute the 86 four-element subsets of `{1..16}` summing to 34.
2. **Disjoint triples** — Select three pairwise-disjoint masks; the fourth mask is forced by bitmask complement.
3. **Row permutations** — Permute values within each of the first three rows.
4. **Column closure** — Derive row 4 from `34 − (row0[col] + row1[col] + row2[col])`.
5. **Diagonal filter** — Keep grids whose main and anti-diagonals also sum to 34.

**D4 canonicalization** — `canonical(grid) = min(d4_orbit(grid))` over 8 rotations/reflections. Complement `17 − x` is **not** treated as D4.

## Observed counts (2026-07-09 run)

| Quantity | Observed |
|---|---|
| Oriented squares | 7,040 |
| Unique oriented | 7,040 |
| D4 representatives (lex-min) | 880 |
| Orbit histogram (canonical) | `{8: 880}` |
| Stabilizer histogram (canonical) | `{1: 880}` |
| All valid (normal + magic) | true |
| Enumeration time | ~74 s |
| Oriented SHA-256 | `6c034e5a28a21d7c9d7c61405ae7b1d6920c94d65fd1f182b17201ac656ee3ad` |
| Canonical SHA-256 | `1197628441f1fe0e5af38b85dd8eb17d0c72bf037e41fe44db219fe90de4f576` |

Cross-check against `magic_squares_880.csv`: canonical sets match exactly (`canonical_sets_match: true`).

## Limitations

- Enumeration is O(many permutations) over row-mask triples; ~74 s on this machine. Not suited for order 5+.
- D4 only; complement pairing and other classifications (associative, panmagic) are out of scope here.
- No D4-symmetric squares exist in the order-4 normal magic set (all stabilizers trivial), but the code handles smaller orbits if they appeared.

## Module layout

| Module | Role |
|---|---|
| `enumerate.py` | Row-mask generator |
| `validate.py` | Normality and magic checks |
| `d4.py` | D4 transforms, orbit, canonical form |
| `main.py` | CLI: enumerate / ingest / crosscheck / inspect |
| `test_invariants.py` | Unit tests and count invariants |
