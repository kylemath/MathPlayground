# S1 Verification Evidence Tables

## Table A — Central 880 / 7,040 claims

| Check | Method | Observed | Expected | Pass |
|-------|--------|----------|----------|------|
| CSV row count | `wc -l` / CSV load | 880 | 880 | ✓ |
| Unique literal grids | Independent D4 audit | 880 | 880 | ✓ |
| Unique D4-canonical grids | `frenicle_min()` over rows | 880 | 880 | ✓ |
| D4 orbit size per row | `len(d4_orbit(g))` | all 8 | all 8 | ✓ |
| Oriented union (measured) | Union of all D4 orbits | 7,040 | 7,040 | ✓ |
| Sum of orbit sizes | Σ \|orbit\| | 7,040 | 7,040 | ✓ |
| analyze.py expanded count | metadata field | 7,040 (=880×8) | 7,040 | ✓ (formula) |

## Table B — Dudeney group distribution (CSV vs analysis.json)

| Group | CSV count | analysis.json `dudeneyCounts` | Sum check |
|-------|-----------|-------------------------------|-----------|
| 1 | 48 | 48 | pandiagonal (I) |
| 2 | 48 | 48 | bent-diagonal semi-pandiagonal |
| 3 | 48 | 48 | associative semi-pandiagonal |
| 4 | 96 | 96 | semi-pandiagonal |
| 5 | 96 | 96 | semi-pandiagonal |
| 6 | 304 | 304 | semi-pandiagonal/simple |
| 7–10 | 56 each | 56 each | simple |
| 11–12 | 8 each | 8 each | limited symmetry |
| **Total** | **880** | **880** | ✓ |

**Key-type artifact:** `s1_independent_verify.json` reports `dudeney_matches_csv: false` because the runtime comparison used integer keys from `Counter(int(...))` against string keys from `json.loads`. After `str()` normalization (`outputs/s1_dudeney_key_normalize.json`), histograms are identical (`normalized_comparison_equal: true`).

## Table C — Structural classification cross-check

| Property | Count on CSV rows | Dudeney expectation |
|----------|-------------------|---------------------|
| pandiagonal | 48 | Group I only (48) |
| associative | 48 | Group III only (48) |
| semi_pandiagonal (opposite short diagonals) | 48 | Partial; groups II–VI use broader semi-Nasik tests |
| Group I not pandiagonal | 0 mismatches | — |
| Group III not associative | 0 mismatches | — |
| Both pandiagonal and associative | 0 | — |

## Table D — Provenance (Harvey Heinz / recmath.org)

| Source page | Parsed records |
|-------------|----------------|
| order4lista.htm | 200 |
| order4listb.htm | 200 |
| order4listc.htm | 200 |
| order4listd.htm | 280 |
| **Total live fetch** | **880** |

Local CSV: 49,409 bytes; `fetch_source.py` documents same four URLs.

## Table E — analysis.csv cohort recount (independent)

| Cohort | Rows | `is_magic=True` |
|--------|------|-----------------|
| magic | 880 | 880 |
| swap-1 | 880 | 0 |
| swap-2 | 880 | 0 |
| swap-3 | 880 | 0 |
| random | 880 | 0 |
| **Total** | **4,400** | **880** |

## Table F — Source-census verification vs failed from-scratch prototype

| Script | Oriented | D4-canonical | Notes |
|--------|----------|--------------|-------|
| S1 `s1_independent_verify.py` (anchored backtrack) | 1,664 | 208 | **Failed prototype** — `cell_1=1` is invalid D4 anchor (1 may occupy any cell after rotation/reflection); not a census contradiction |
| M1 `sub_S2/enumerate.py` (read-only cross-run, not rerun) | 1,664 | 208 | Same incomplete prototype count |
| CSV audit + measured D4 expansion | 7,040 | 880 | **Authoritative for this repo** — verifies supplied census without metadata multiplication |

## Table G — Reproduced vs inferred counts

| Quantity | How stated in repo | Genuinely reproduced? |
|----------|-------------------|-------------------------|
| 880 representatives | CSV length + uniqueness checks | **Yes** — recomputed |
| 7,040 oriented union | D4 expansion of CSV | **Yes** — measured, not copied |
| 7,040 in analysis.json | `sourceCount * 8` in analyze.py | **Inferred** — formula matches measured union |
| Dudeney counts | CSV aggregation | **Yes** — matches analysis.json |
| Cohort totals (4,400) | analysis.csv row count | **Yes** — independently counted |
