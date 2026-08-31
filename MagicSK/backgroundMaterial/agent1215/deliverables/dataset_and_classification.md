# Dataset and Classification Recommendations

## Scope and the meaning of 880

A normal order-4 magic square is a row-major 4×4 permutation of `1..16` whose four rows, four columns, and two principal diagonals each sum to 34.

The accepted count is:

- **7,040 oriented squares:** literal placements in a fixed coordinate frame.
- **880 fundamental squares:** equivalence classes under the eight rotations and reflections of the square (the position action of D4).

This quotient does not identify entrywise complements, arbitrary row/column permutations, toroidal translations, or Dudeney types.

For a normal square all 16 entries are distinct. A nonidentity geometric symmetry moves at least one position into a nontrivial cycle, so a fixed grid would require equal values at distinct positions. Therefore every D4 stabilizer is trivial and every orbit has eight members. The local audit also constructed the union of all images and observed exactly `7,040`, rather than relying only on `880×8`.

## Sources and provenance

Recommended evidence chain:

1. K. Ollerenshaw and H. Bondi, “Magic squares of order four,” *Philosophical Transactions of the Royal Society A* 306 (1982), 443–532, <https://doi.org/10.1098/rsta.1982.0093>. This is the strongest modern scholarly reference: it independently proves the 880 count and the 12 complementary-number patterns.
2. Bernard Frénicle de Bessy, “Table générale des quarrez magiques de quatre de costé,” in *Divers ouvrages de mathématique et de physique* (1693). Historical primary enumeration.
3. Harvey Heinz’s Frénicle-indexed machine-readable lists, index at <http://www.recmath.org/Magic%20Squares/order4list.htm>, with pages `order4lista.htm` through `order4listd.htm`. These are a practical ingestion source with Dudeney and complement metadata.

The existing `MagicMomentExplorer/scripts/fetch_source.py` downloads the four Heinz pages, parses IDs and 16 cells, validates IDs 1–880 and all ten magic lines, and writes the local CSV.

Provenance requirements for a release:

- Record exact URLs, retrieval date, parser version, source encoding, and SHA-256 of every downloaded page and normalized CSV.
- Keep the generation recipe beside the generated data.
- Preserve Heinz/Frénicle/Ollerenshaw attribution.
- Resolve redistribution rights. The Heinz pages do not state an explicit license in the inspected text; mathematical facts are not copyrightable, but the compilation/format may carry rights. Prefer generating the set independently or distributing hashes and a fetch recipe if licensing remains unclear.
- Do not describe a successful CSV audit as an independent proof of completeness. It proves internal consistency of the snapshot; completeness also rests on the scholarly enumeration unless a from-scratch generator is executed.

## Reproduced local facts

`coordinator/coordinator_dataset_audit.py` audited the read-only local CSV and wrote `coordinator/coordinator_dataset_audit.json`.

Observed on 2026-07-09:

- 880 rows with ordered IDs 1–880.
- Every row is normal and magic.
- 880 literal grids and 880 distinct lexicographic D4 canonical forms.
- Every source row is already the lexicographically least D4 image.
- Every D4 orbit has size 8; their union contains 7,040 grids.
- Every entrywise complement `v ↦ 17-v`, after D4 canonicalization, is present and matches the declared `complement_id`.
- Dudeney counts by group I–XII are `48,48,48,96,96,304,56,56,56,56,8,8`.

An independent classification audit in M4 reproduced:

- pandiagonal/panmagic: 48
- semi-pandiagonal under the documented bent-diagonal predicate: 48
- associative: 48
- most-perfect under the documented order-4 toroidal predicate: 48
- compact non-toroidal 2×2 predicate: 48
- self-complementary up to D4: 352
- complement orbits on the 880 D4 classes: 352 singleton orbits plus 264 two-class orbits, total 616

Individual class counts do not imply the predicates are disjoint or identical. Store each as an independently computed Boolean unless an intersection has also been tested.

## Canonicalization and validation algorithm

For each row-major tuple:

1. Assert length 16 and `sorted(cells) == [1,...,16]`.
2. Compute the four row sums, four column sums, and two principal diagonal sums; require all ten to equal 34.
3. Generate the eight D4 images using four rotations and one reflection composed with those rotations.
4. Use the lexicographically least 16-tuple as the canonical key.
5. Assert exactly eight distinct images, 880 distinct keys, and 7,040 images in the union.
6. Preserve the source `id` as a stable historical/display identifier; do not silently replace it with array position.

Lexicographic D4 canonicalization is explicit and machine-friendly. “Frénicle form” should be reserved for the historical orientation rule unless it has been shown identical to the chosen key on the actual dataset.

## Classification definitions

- **D4 orbit:** position rotations/reflections only.
- **Entrywise complement:** replace every value `v` by `17-v`, then optionally D4-canonicalize to locate its fundamental partner.
- **Self-complementary up to D4:** the complemented square has the same D4 canonical key.
- **Associative:** every centrally opposite pair sums to 17:
  `a[r,c] + a[3-r,3-c] = 17`.
- **Pandiagonal / panmagic / Nasik:** every length-4 wraparound diagonal in both directions sums to 34, in addition to ordinary magic lines.
- **Most-perfect (order 4):** use the explicitly implemented toroidal definition: every wraparound 2×2 block sums to 34 and entries separated by two steps along a diagonal are complementary. Never infer this flag from “pandiagonal” without checking the predicate.
- **Compact 2×2:** every ordinary contiguous, non-wraparound 2×2 block sums to 34. Keep this separate from most-perfect.
- **Dudeney group:** one of 12 complementary-pair geometry patterns. This is a partition of the 880 source representatives, not an equivalence relation replacing D4.

The Heinz fields have distinct meanings:

- `complement_pair`: source pair/group metadata; `999` marks a self-similar complement case.
- `complement_id`: the source ID of the complemented class’s partner; for a self-similar case it equals the source ID.

## Recommended browser fields

Each primary record should include:

- stable source ID and 16 row-major cells
- Dudeney group and source orientation metadata
- `complement_pair` and `complement_id`
- a versioned collection of explicit class tags or a versioned bit registry
- optional canonical key/hash for integrity checks
- a fixed schema version and provenance reference

Do not encode “ordinary” as an independent property that can conflict with future tags. It is safer to derive it as “none of the displayed special predicates.”

## Known limitations

- The local CSV audit is reproducible but is not a from-scratch census.
- The source-site licensing status is unresolved.
- “Semi-pandiagonal” has competing historical terminology; ship the actual tested line family with the label.
- Counts are orientation-invariant for the listed predicates, but moment coefficients are not. Dataset class selection and moment-orientation policy must be documented separately.
