# Manager Report — Dataset Provenance, Enumeration, D4, and Classification

**Agent:** 1215-M1  
**Stream:** Normal order-4 magic-square dataset and mathematical semantics  
**Coordinator:** 1215-C  
**Status:** Complete  
**Iteration:** 2 — initial research plus manager review/correction

## Stream Summary

This stream delivered authoritative-source notes, two independent complete
enumerators, D4 validation/canonicalization, an audited classification layer,
and a coordinator-ready dataset/classification draft. No file in
`MagicMomentExplorer` was edited.

The central result is both proved and reproduced: there are **880 D4
equivalence classes** and **7,040 oriented normal order-4 magic squares**.
Orbit–stabilizer is essential here. A nonidentity D4 motion moves at least one
cell; an invariant labeled grid would repeat the moved cell's value, impossible
because a normal square uses 1,…,16 once each. Every stabilizer is therefore
trivial, every orbit has size 8, and `880 × 8 = 7,040` is justified rather
than assumed.

The manager enumerator observed:

- 7,040 unique oriented squares and 880 lex-min D4 representatives;
- orbit histogram `{8: 880}` and stabilizer histogram `{1: 880}`;
- all normality and ten magic-line checks passing;
- canonical SHA-256
  `1197628441f1fe0e5af38b85dd8eb17d0c72bf037e41fe44db219fe90de4f576`;
- oriented SHA-256
  `6c034e5a28a21d7c9d7c61405ae7b1d6920c94d65fd1f182b17201ac656ee3ad`.

The independently recovered S2 enumerator produced the same counts and
checksums and matched the read-only 880-row project CSV with zero canonical-set
differences. S1 independently reproduced 7,040/880 using a different
seven-free-parameter linear enumeration. The coordinator's separate
[dataset audit](../coordinator_dataset_audit.json) also reports exact agreement
between its from-scratch canonical set and the read-only CSV.

## Sub-subagent Status

| Sub-subagent | Assignment | Status | Reviewed result |
|---|---|---|---|
| [1215-M1-S1](sub_S1/S1_report.md) | Provenance, sources, 880 versus 7,040 | Complete after correction | Authoritative hierarchy, stabilizer proof, independent enumeration, acquisition/licensing notes; complement counts and OEIS license corrected |
| [1215-M1-S2](sub_S2/S2_report.md) | Enumeration, validation, D4 canonicalization | Complete after recovery | Initial launcher aborted; resumed child delivered efficient row-mask enumerator, 11 passing tests, checksums, and exact CSV cross-check |
| [1215-M1-S3](sub_S3/S3_report.md) | Structural classes and count checks | Complete after correction | Precise predicates and reproduced class counts; attribution, commutation, complement invariance, and compact definition corrected |

## Collected Outputs

### Provenance and historical verification

- [S1 report](sub_S1/S1_report.md)
- [Extended source notes](sub_S1/source_notes.md)
- [Independent linear enumerator](sub_S1/verify_enumeration.py)
- [Linear enumeration results](sub_S1/verify_enumeration_results.json)
- [Read-only CSV audit](sub_S1/cross_validate_dataset.py)
- [Complement-orbit verification](sub_S1/verify_complement.py)

### Deterministic enumeration and D4 implementation

- [S2 report](sub_S2/S2_report.md)
- [Usage and algorithm notes](sub_S2/README.md)
- [Row-mask enumerator](sub_S2/enumerate.py)
- [Validation predicates](sub_S2/validate.py)
- [D4 transforms and canonicalization](sub_S2/d4.py)
- [CLI](sub_S2/main.py)
- [Invariant tests](sub_S2/test_invariants.py)
- [Observed enumeration results](sub_S2/enumeration_results.json)
- [Enumeration/CSV cross-check](sub_S2/crosscheck_results.json)

### Structural classification

- [S3 report](sub_S3/S3_report.md)
- [Classification prototype](sub_S3/classify_counts.py)
- [Observed classification results](sub_S3/count_results.json)
- [Classification bibliography](sub_S3/literature_references.md)

### Manager integration artifacts

- [Independent manager enumerator](manager_validate.py)
- [Manager observed results](manager_validation_results.json)
- [Coordinator-ready dataset/classification draft](dataset_and_classification.md)

All Python prototypes use only the standard library; no pip install or virtual
environment was needed.

## Integration Notes

### Provenance and acquisition

The source hierarchy should be retained in downstream documentation:

1. Bernard Frénicle de Bessy, “Table générale des carrez de quatre,” in
   *Divers ouvrages de mathématique et de physique* (1693), pp. 484–503:
   historical 880-class enumeration.
2. Kathleen Ollerenshaw and Hermann Bondi, “Magic squares of order four,”
   *Philosophical Transactions of the Royal Society A* 306 (1982), 443–532,
   https://doi.org/10.1098/rsta.1982.0093: peer-reviewed analytical treatment.
3. OEIS A006052: registry definition explicitly modulo rotations/reflections.
4. Harvey Heinz / RecMath:
   http://www.recmath.org/Magic%20Squares/Downloads/MS4_List-Index.zip for a
   machine-ingestible secondary transcription.

Licensing must not be inferred from accessibility. Frénicle's historical work
is public domain, while scan-host terms may apply; the Royal Society article is
copyrighted; OEIS content is CC BY-SA 4.0; RecMath's downloadable list has no
clear redistribution license. The safest product path is to generate the
corpus independently and cite historical sources rather than redistribute an
unclearly licensed transcription.

### Deterministic validation and canonicalization

The recommended ingestion contract is:

1. require exactly the integers 1,…,16;
2. require all four rows, four columns, and both main diagonals to sum to 34;
3. generate four rotations and four reflections;
4. choose the row-major lexicographic minimum as the D4 key;
5. assert 880 unique keys, orbit size 8 for each, and a 7,040-element orbit
   union;
6. record deterministic checksums and recompute classifications from cells.

Frénicle standard form and lex-min are both unique D4 conventions here, but
the chosen convention must be named. “Fundamental” must not silently include
complement, arbitrary row/column permutations, or toroidal translations.

### Complement is separate from D4

Entrywise complement is `C(x)=17-x`. It commutes with D4 positional actions
but is not a geometric motion. On the reproduced 880-class quotient:

- 352 D4 classes are complement-fixed;
- 528 classes form 264 complement two-cycles;
- total complement-orbits are therefore 616.

The earlier “440 unordered pairs” shortcut was rejected because it ignores
fixed points. Associativity is preserved by complement; for an associative
square, complement equals its 180° rotation.

The imported metadata columns have distinct semantics, reproduced across all
880 rows:

- `complement_id` is the actual partner square ID and is an involution;
- `complement_pair` is a pairing label only for non-fixed two-cycles: 264
  non-`999` labels each occur exactly twice;
- `complement_pair = 999` is a sentinel on all 352 fixed classes, not one
  352-member pairing group; exactly those rows have `complement_id = id`.

These observations agree with the coordinator's independent
[`coordinator_dataset_audit.py`](../coordinator_dataset_audit.py) and
[`coordinator_dataset_audit.json`](../coordinator_dataset_audit.json), which
report all 880 declared partner IDs and sentinel cases consistent.

### Reproduced structural counts

Counts below are reproduced on D4 representatives, not merely literature
claims:

| Predicate | Precise working definition | Observed D4 classes |
|---|---|---:|
| Associative | center-opposite entries sum to 17 | 48 |
| Panmagic / pandiagonal / Nasik | all wrap-around diagonals in both slopes sum to 34 | 48 |
| Most-perfect | all 16 toroidal 2×2 blocks sum to 34 and half-diagonal pairs sum to 17 | 48 |
| Associative and panmagic | intersection of the two predicates | 0 |
| Complement-fixed modulo D4 | `canon(C(S)) = canon(S)` | 352 |

At order 4, the observed panmagic and most-perfect sets are identical. This
order-specific equality must not be generalized. A non-toroidal compact flag,
if exposed, should mean all nine contiguous 2×2 windows sum to 34 and should
remain separately named.

Dudeney's 12 groups are complement-pair pattern types, not D4 classes. The
broad historical “semi-pandiagonal” grouping is also not equivalent to a
single broken-diagonal count predicate; downstream code should store sourced
Dudeney metadata separately from explicitly named geometric tests.

## Escalated Questions

1. **Corpus distribution:** Should the application bundle a newly generated
   880-representative corpus (recommended) or continue shipping a RecMath-
   derived transcription whose redistribution license is unstated?
2. **Canonical naming:** Should public IDs promise Frénicle indexing, or should
   the product expose only a stable lex-min D4 key and retain Frénicle IDs as
   sourced metadata?
3. **Semi-pandiagonal UI:** Should the product omit the ambiguous broad label
   until a specific Dudeney-pattern implementation is approved (recommended),
   or expose only narrowly defined bent/broken-diagonal predicates?
4. **Source archival:** Is legal review required before preserving RecMath ZIP
   bytes internally, even if the production dataset is independently generated?

## Issues Encountered

- The first S2 launcher was aborted after a slow backtracking test and produced
  no report. It was resumed with a row-mask/forced-fourth-row algorithm and
  completed successfully.
- Initial child brute-force implementations were impractical. S1 replaced its
  search with a seven-free-parameter method; S2 and the manager used the
  deterministic 86-row-mask method.
- Manager review caught and corrected: a false 440 complement-pair claim,
  incorrect OEIS license shorthand, incorrect Ollerenshaw–Bondi attribution,
  the false claim that D4 and complement do not commute, the false claim that
  complement does not preserve associativity, and an inconsistent compact
  2×2 definition.
- S3's reproduced class counts initially depended on the read-only project CSV.
  Independent manager and S2 enumeration, plus exact canonical-set comparison,
  removed count uncertainty while preserving the provenance caveat.
- RecMath availability and licensing remain operational/legal risks rather than
  mathematical blockers.

## Self-Assessment

- **Craftsperson says:** The integrated result is technically strong: two
  complete enumeration paths agree exactly, checksums are recorded, D4
  stabilizer logic is proved, child reports were audited rather than accepted
  blindly, and classification predicates are explicitly separated.
- **Skeptic says:** Historical transcription rights remain unclear, Dudeney's
  broad semi-pandiagonal typology is not fully re-derived from first principles,
  and long-term public IDs require a product decision between Frénicle indexing
  and lex-min canonical keys.
- **Mover says:** The mathematical and reproducibility requirements are met.
  The unresolved items are clearly escalated policy/interface decisions, so the
  stream is ready for coordinator integration.

*Dated footer: 2026-07-09 — Manager 1215-M1*
