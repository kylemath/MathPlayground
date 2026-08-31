# Magic Moment Bundle Schema v1

## Design goals

- **Compact:** tuple records, short metadata keys, no duplicate `modeEnergy` (recomputable from coefficients).
- **Versioned:** `meta.schemaVersion` drives migration; `bundleKind` guards loader dispatch.
- **Stable IDs:** `records[i][0]` is the permanent source id `1..880`.
- **Reproducible:** `meta.provenance.sourceSha256` is required — SHA-256 hex of `sourceArtifact` at build time.
- **Browser-feasible:** ~152 KB raw JSON for 880 records; ~32 KB gzip (measured 2026-07-09).

## Record tuple layout

| Index | Field | Type | Notes |
|------:|-------|------|-------|
| 0 | id | int | Stable 1..880 |
| 1 | cells | int[16] | Row-major grid |
| 2 | dudeneyGroup | int | 1..12 |
| 3 | groupOrientation | int | Source orientation index |
| 4 | complementPair | int | Pair id or `999` self-complement sentinel |
| 5 | complementId | int | Linked record id |
| 6 | classFlags | int | Bitfield (M1 vocabulary) |
| 7 | coefficients | float[15] | Order from `meta.modes` |
| 8 | energySummary | float[5] | axial, interaction, lowOrder, highOrder, spectralCentroid |

## Classification flags (provisional, M1 integration)

| Bit | Label |
|----:|-------|
| 1 | pandiagonal |
| 2 | associative |
| 4 | most-perfect |
| 8 | ordinary (fallback) |

Multiple bits may be set; `ordinary` is mutually exclusive with special classes in current pipeline.

## Version migration sketch

```javascript
function loadBundle(raw) {
  const bundle = JSON.parse(raw);
  const v = bundle.meta.schemaVersion;
  if (v === '1.0.0') return normalizeV1(bundle);
  throw new Error(`Unsupported schemaVersion: ${v}`);
}
```

Future `1.1.0` might add optional per-mode energy arrays or M2 degree bins without breaking v1 readers if new fields are additive in `meta` and trailing tuple slots are version-gated.

## M1 / M2 integration hooks

- **M1** owns `classFlags` vocabulary, complement semantics, Dudeney grouping, and validation of `cells` permutation property.
- **M2** owns `meta.modes`, `meta.coordinates`, `meta.basisRef`, coefficient definition, and energy summary formulas.
- Web app should treat coefficients as opaque until M2 signs off; recompute energies client-side only after basis embedding.
