| Domain | Field | Type / semantics | App (`analysis.json`) | M3 prototype (`sample-data.json`) | M1 source CSV | Notes |
|--------|-------|------------------|----------------------|-----------------------------------|---------------|-------|
| Provenance | `schemaVersion` | semver string | **Absent** (top-level) | `0.1.0-prototype` | — | Add for versioned browser bundles |
| Provenance | `metadata.seed` | int | `20260709` | — (sample only) | — | Matches `analyze.py --seed` default |
| Provenance | `metadata.sourceCount` | int | `880` | — | 880 rows | Frénicle representatives |
| Provenance | `metadata.expandedOrientedCount` | int | `7040` | — | — | 880×8 D₄ images |
| Provenance | `metadata.heightEnergy` | float | `340.0` | — | — | Σ(a−8.5)² fixed for 1..16 |
| Provenance | `metadata.basis` | float[4][4] | Present | — | — | Aligns with M2 `S1_basis_numeric.json` (max Δ≈5×10⁻¹¹) |
| Provenance | `metadata.coordinates` | float[4] | `[-1.5,-0.5,0.5,1.5]` | — | — | Matches M2 |
| M1 ID | `recordId` | string | `M001`, `S1-001`, `R001` | Same pattern | — | Stable display key |
| M1 ID | `sourceId` | int\|null | int for derived cohorts | int | `id` | Null only if absent in random? Actually random has null |
| M1 ID | `cells` | int[16] row-major | ✓ | ✓ | `cell_1..16` | Permutation of 1..16 |
| M1 class | `isMagic` | bool | ✓ | ✓ | derived | All 880 source magic |
| M1 class | `dudeneyGroup` | int 1..12 | camelCase | camelCase | `dudeney_group` | Counts match coordinator audit |
| M1 class | `dudeneyLabel` | string | ✓ | ✓ | derived | From `GROUP_LABELS` |
| M1 class | `groupOrientation` | int | ✓ | ✓ | `group_orientation` | Heinz list field |
| M1 class | `complementPair` | int | ✓ | ✓ | `complement_pair` | `999` = self-complementary sentinel |
| M1 class | `complementId` | int | ✓ | ✓ | `complement_id` | 880/880 validated |
| M1 class | `selfComplementary` | bool | ✓ | ✓ | derived | |
| M1 class | `classes` | string[] | `ordinary`, `pandiagonal`, … | same slugs | derived | Multi-label allowed |
| M1 class | `d4OrbitSize` | int | always `8` in sample | ✓ | derived | Stabilizer caveat: all 880 have size 8 here |
| M1 class | `lineSums` | `{rows,columns,diagonals}` | ✓ | ✓ | derived | Text alt needed in UI |
| M2 moment | `coefficients` | dict Mxy ×15 | ✓ (8 dp) | ✓ | derived | Optional in compact browser schema |
| M2 moment | `modeEnergy` | dict Mxy ×15 | ✓ | ✓ | derived | Sum = 340 for all records |
| M2 moment | `degreeEnergy` | keys `"2"`..`"6"` | ✓ | ✓ | derived | Sums to `interactionEnergy` |
| M2 moment | `axialEnergy` | float | ✓ | ✓ | derived | Zero for magic cohort |
| M2 moment | `interactionEnergy` | float | ✓ | ✓ | derived | Mixed modes only |
| M2 moment | `lowOrderEnergy` | float | E₂+E₃ | ✓ | derived | |
| M2 moment | `highOrderEnergy` | float | E₄+E₅+E₆ | ✓ | derived | |
| M2 moment | `spectralCentroid` | float | ✓ | ✓ | derived | Degree-weighted mean |
| M2 moment | `lineDefectEnergy` | float/int | ✓ | ✓ | derived | Σ(line−34)² |
| M2 control | `cohort` | enum string | `magic`, `swap-1..3`, `random` | `magic`, `swap-1` | — | **M3 UI prototype uses `swapped-1` (mismatch)** |
| M2 control | `swaps` | int 0..3 | ✓ | ✓ | — | Count of pair swaps |
