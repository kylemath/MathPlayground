# M1 / M2 Integration Requirements (S1 provisional)

## Scope

This document states assumptions and integration contracts for Sub-subagent 1215-M3-S1 schema v1. It is **provisional** until M1 classification and M2 moment definitions are finalized.

## M1 — Dataset and classification (required inputs)

| Topic | S1 assumption | M1 must confirm or revise |
|-------|---------------|---------------------------|
| Record identity | `id` = CSV `id`, range `1..880`, never reindexed | Canonical ordering policy after D4 reduction |
| Grid encoding | `cells` row-major, values `1..16` permutation | Same convention as enumeration source |
| Dudeney group | Integer `1..12` in tuple slot 2 | Label strings live in UI dictionary, not payload |
| Complement | `complementPair` + `complementId`; `999` = self-complementary | Exact complement graph semantics |
| Class flags | Bitfield slot 6 with provisional bits `{1,2,4,8}` | Final taxonomy; avoid conflating panmagic vs associative |
| D4 orbit | Not stored per record (always 8 for this list) | Stabilizer caveats for special classes |
| Validation | Client checks permutation + id uniqueness | Server/build-time invariants M1 script enforces |

### M1 deliverables that change schema

1. **`classFlags` registry** — authoritative bit map + mutual-exclusion rules.
2. **Optional fields** (v1.1 candidates): `d4CanonicalKey`, `complementOrbitId`, `mostPerfectToroidalCheck`.
3. **Build hook** — M1 verification script output consumed by `build_compact_payload.py`.

## M2 — Moment basis and energies (required inputs)

| Topic | S1 assumption | M2 must confirm or revise |
|-------|---------------|---------------------------|
| Coordinates | `[-1.5,-0.5,0.5,1.5]` centered on 4×4 grid | Weighted inner product definition |
| Basis | `orthonormal-monomials-gram-schmidt-v1` referenced, not embedded | Full basis vectors or regeneration recipe |
| Modes | 15 non-DC tensor products `Mxy`, `x,y ∈ {0..3}`, skip `M00` | Higher-moment subset vs complete basis |
| Coefficients | Slot 7, rounded 4 dp, fixed `meta.modes` order | Normalization and Parseval identity |
| Energy summary | Slot 8: axial, interaction, lowOrder, highOrder, spectralCentroid | Degree cutoffs for low/high split |
| Controls | Only **aggregates** in browser bundle | Per-control record policy (likely server-side only) |

### M2 deliverables that change schema

1. **`meta.basisRef` document** — embeddable 4-vector polynomials or code snippet for browser recompute.
2. **Energy formulas** — document mapping coefficient index → mode energy = c².
3. **Control generation** — seed, swap policy, cohort ids for optional expanded bundle `v1.full`.
4. **Migration note** if mode ordering or rounding changes (bump `schemaVersion`).

## Web application consumption contract

```text
Load → validate schemaVersion → parse records
     → index by id (Map)
     → filter on classFlags / dudeneyGroup / energy thresholds
     → sort on energySummary fields
     → selected-square diagram reads cells[16]
     → moment-energy chart reads coefficients[15] or precomputed energySummary
```

## Reproducibility metadata (present in v1)

- `meta.controlSeed` — ties to random/swap cohorts in full analysis pipeline.
- `meta.provenance.sourceArtifact` + required `sourceSha256` (SHA-256 of CSV at build).
- `controlAggregates` — summary stats for comparison UI without shipping 3520 control rows.

## Open risks flagged for manager

1. **Rounding:** 4 dp coefficients may drift Parseval checks in client recompute.
2. **Class bitfield:** Insufficient for future multi-label fine-grained types; may need string table.
3. **Full control detail:** If UI requires inspecting individual swap/random squares, add lazy-loaded supplemental bundle.
4. **Basis omission:** Offline file:// app cannot recompute moments without embedded basis or WASM module.
