# Dataset and Classification Draft — Normal Order-4 Magic Squares

**Scope:** normal 4×4 squares using 1,…,16 exactly once, with all four
rows, four columns, and two main diagonals summing to 34.

## Recommended dataset basis

Use one lexicographically minimal representative from each orbit of the
8-element square-symmetry group D4. Keep the equivalence relation explicit:
D4 moves cell positions; it does not complement values, permute arbitrary
rows/columns, or translate on a torus.

Recommended reproducible routes:

1. **Deterministic enumeration:** run `python3 manager_validate.py --output
   manager_validation_results.json`. This standard-library prototype generates
   the 86 four-element subsets of 1,…,16 summing to 34, selects disjoint
   ordered row sets, permutes the first three rows, and derives the fourth from
   column sums. It then validates all ten magic lines and D4-canonicalizes.
2. **Authoritative-list ingestion:** acquire Harvey Heinz's Frénicle-indexed
   `MS4_List-Index.zip` from
   http://www.recmath.org/Magic%20Squares/Downloads/MS4_List-Index.zip, parse
   each square as a row-major 16-tuple, and apply the same validation and
   canonicalization. Treat this as a secondary transcription of the historical
   list, not as the primary mathematical authority.
3. **Local cross-check only:** the read-only project CSV at
   `/Users/kylemathewson/MagicSK/MagicMomentExplorer/data/magic_squares_880.csv`
   has 880 data rows plus a header and SHA-256
   `86e36c20faf36514985cd9c1e886a01aba54fd88bc3038f33b06ff783781b8b2`
   as observed on 2026-07-09. It is a derivative artifact; its provenance must
   point upstream.

## Observed verification results

The independent manager prototype completed without third-party dependencies:

- 7,040 unique oriented normal squares;
- 880 lex-min D4 representatives;
- orbit-size histogram `{8: 880}`;
- stabilizer-size histogram `{1: 880}`;
- every enumerated square passed normality and all ten line-sum checks;
- oriented SHA-256
  `6c034e5a28a21d7c9d7c61405ae7b1d6920c94d65fd1f182b17201ac656ee3ad`;
- canonical SHA-256
  `1197628441f1fe0e5af38b85dd8eb17d0c72bf037e41fe44db219fe90de4f576`.

These are reproduced observations from `manager_validation_results.json`, not
counts copied from the literature.

## Why 880 and 7,040 are both correct

For a square `S`, orbit–stabilizer gives

`|D4·S| = |D4| / |Stab(S)| = 8 / |Stab(S)|`.

Every normal square has distinct entries. Any nonidentity D4 motion moves at
least one cell. If it fixed the labeled grid, the moved cell and its image
would have to contain the same value, contradicting distinctness. Thus every
stabilizer is trivial and every orbit has exactly eight members. Consequently
the 880 D4 classes expand to exactly `880 × 8 = 7,040` oriented squares. This
is a proof, not an assumption that all orbits happen to be full; the observed
histograms independently confirm it.

## Canonicalization

For each row-major tuple, generate:

- identity and rotations by 90°, 180°, and 270°;
- one reflection composed with each rotation.

Deduplicate defensively and choose the lexicographic minimum. For these
distinct-entry squares, all eight images are distinct. Frénicle standard form
(smallest corner at top left, then top neighbor smaller than left neighbor) is
also a unique D4 representative, but lex-min should be named separately even
though it selects the same orientation here.

## Classification predicates

All predicates below are properties of a validated normal magic square.

### D4 equivalence

`S ~ T` iff `T = g·S` for some rotation or reflection `g ∈ D4`. Magicness and
all structural predicates below are invariant under D4. D4 is the only
equivalence used by the terms “880 fundamental squares” and “7,040 oriented
squares.”

### Complement

`C(S)` replaces each value `x` by `17-x`. Complement acts on values and is not
a D4 motion, although it commutes with every D4 motion:
`C(g·S) = g·C(S)`. Therefore D4 together with complement gives a separate
`D4 × C2` action.

Observed on the 880 D4 classes:

- 352 classes are fixed by complement modulo D4;
- the remaining 528 classes form 264 two-cycles;
- hence there are 616 complement-orbits on the D4 quotient.

Do not describe this as “440 unordered pairs”; that ignores fixed classes.

For the current CSV schema, `complement_id` is the partner's square ID. It is
an involution on IDs and equals the row's own `id` for all 352 fixed classes.
`complement_pair` has different semantics: each of 264 non-`999` labels occurs
on the two rows of one non-fixed cycle, while `999` is a sentinel repeated on
all 352 fixed rows. It must not be interpreted as one complement-orbit ID.

### Associative

For every cell `(r,c)`,

`S[r,c] + S[3-r,3-c] = 17`.

“Associated,” “centrosymmetric complementary,” and sometimes “regular” are
used for this property, but “regular” is author-dependent and should not be a
database label without a cited convention. Complement preserves
associativity; in fact, for an associative square `C(S)` is its 180° rotation.

Observed count: 48 D4 classes.

### Panmagic / pandiagonal / Nasik

Every length-4 broken diagonal in both slope directions, with indices taken
modulo 4, sums to 34. This means four cyclic offsets in each direction,
including the two ordinary main diagonals.

Observed count: 48 D4 classes. Observed intersection with associative: zero.

### Most-perfect

Use the Ollerenshaw–Brée definition for doubly-even order:

1. every one of the 16 toroidal 2×2 adjacent blocks sums to 34; and
2. entries separated by `n/2 = 2` steps along a diagonal sum to 17.

Observed at order 4: 48 D4 classes, exactly the same set as the 48 panmagic
classes. Do not generalize that equality to arbitrary orders.

### Compact, non-toroidal 2×2

If retained as a separate exploratory flag, define it as: all nine contiguous
non-wrapping 2×2 windows sum to 34. This is weaker in wording than the
toroidal-block clause of most-perfect and should remain a separately named
predicate even where the observed order-4 sets coincide.

### Semi-pandiagonal and Dudeney groups

Do not create a broad `semi_pandiagonal` Boolean without a precise source
definition. Dudeney's semi-Nasik grouping is a complement-pair pattern
typology, not simply “at least four broken diagonals sum to 34.” If needed,
store:

- the sourced Dudeney group ID as metadata; and
- separately named geometric predicates such as a documented bent-diagonal
  line-sum test.

Likewise, do not infer a Franklin class for order 4 merely from the presence
of bent lines; Franklin-square terminology is normally used for different
constructions at larger orders.

## Source hierarchy and caveats

1. **Primary historical enumeration:** Bernard Frénicle de Bessy, “Table
   générale des carrez de quatre,” in *Divers ouvrages de mathématique et de
   physique* (Paris, 1693), pp. 484–503. Public-domain mathematical work;
   individual scan hosts may impose terms.
2. **Peer-reviewed analytical treatment:** Kathleen Ollerenshaw and Hermann
   Bondi, “Magic squares of order four,” *Philosophical Transactions of the
   Royal Society of London A* 306 (1982), 443–532,
   https://doi.org/10.1098/rsta.1982.0093. Publisher copyright applies.
3. **Registry:** OEIS A006052 defines the count modulo rotations/reflections;
   A027567 records panmagic counts; A081262 records associative counts.
   OEIS content is CC BY-SA 4.0 and requires attribution/share-alike compliance.
4. **Most-perfect definition:** Kathleen Ollerenshaw and David S. Brée,
   *Most-perfect Pandiagonal Magic Squares: Their Construction and
   Enumeration*, Institute of Mathematics and its Applications, 1998,
   ISBN 0-905091-06-X.
5. **Machine-readable secondary source:** Harvey Heinz / RecMath list and ZIP.
   No explicit dataset license was found; validate technically and obtain
   permission or regenerate independently before redistribution.

Facts such as counts and mathematical definitions are not themselves
copyrightable in many jurisdictions, but scans, transcriptions, annotations,
and database selection/arrangement may carry rights. Preserve source URLs,
retrieval date, parser version, and checksums.

## Minimum validation contract

For every ingested row:

1. exactly 16 integer cells;
2. sorted cells equal `1,…,16`;
3. all four row sums, four column sums, and two main diagonal sums equal 34;
4. D4 canonical key generated from exactly eight transforms;
5. no duplicate canonical key.

For the complete corpus:

1. 880 canonical keys;
2. every D4 orbit has size 8;
3. orbit union has 7,040 elements;
4. deterministic canonical and oriented checksums recorded;
5. classifications recomputed from cell values rather than trusted from
   imported labels.

The coordinator's independent implementation and results are available at
`../coordinator_dataset_audit.py` and `../coordinator_dataset_audit.json`;
they reproduce all 880 canonical rows, the 7,040-member D4 union, full orbit
size 8, and consistency of every declared `complement_id`/`999` sentinel case.

*Drafted 2026-07-09 by Manager 1215-M1.*
