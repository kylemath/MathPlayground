# Coordinator Independent Source Notes

Date checked: 2026-07-09

## Primary/Scholarly References

- K. Ollerenshaw and H. Bondi, “Magic squares of order four,” *Philosophical Transactions of the Royal Society of London. Series A*, 1982. DOI: <https://doi.org/10.1098/rsta.1982.0093>. The abstract states that the paper independently confirms 880 essentially different order-4 squares and analytically establishes the 12 complementary-number patterns.
- J. Conway, S. Norton, and A. Ryba, “Frenicle’s 880 Magic Squares,” Princeton University Press, 2017. DOI: <https://doi.org/10.23943/princeton/9780691171920.003.0005>. Historical secondary source confirming Frénicle’s enumeration and subsequent repetitions.

## Reproducible Dataset Source

- Harvey Heinz, “Order4 Squares-List”: <http://www.recmath.org/Magic%20Squares/order4list.htm>.
- Four source pages used by the existing fetch script:
  - <http://www.recmath.org/Magic%20Squares/order4lista.htm>
  - <http://www.recmath.org/Magic%20Squares/order4listb.htm>
  - <http://www.recmath.org/Magic%20Squares/order4listc.htm>
  - <http://www.recmath.org/Magic%20Squares/order4listd.htm>
- Heinz downloads page: <http://www.recmath.com/Magic%20Squares/downloads.htm>. It advertises both complete 880-square archives and `FourSqr.txt`, source code described as finding all 880 order-4 squares.

The Heinz list says the squares are in Frénicle index order, gives Dudeney group metadata, and documents the complement-pair fields. It is a practical acquisition source, but no explicit license was found in the inspected page text. A released application should preserve attribution, record retrieval date and source URLs, distribute only if rights are acceptable, and ideally store source hashes or a generated-data recipe.

## Independent Local Reproduction

The standard-library script `coordinator_dataset_audit.py` audited the existing read-only CSV in `MagicMomentExplorer/data/magic_squares_880.csv`. Its captured result is `coordinator_dataset_audit.json`.

Observed:

- 880 records with IDs 1–880.
- Every record is a permutation of 1–16 with all rows, columns, and main diagonals summing to 34.
- 880 distinct literal grids and 880 distinct D4 canonical forms.
- Every D4 orbit has size 8, so the union of all oriented images has exactly 7,040 grids.
- All rows are already the lexicographically least D4 orientation.
- The complemented grid (`v ↦ 17-v`) of every record canonicalizes to another record, and every declared `complement_id` matches.
- Dudeney group counts: I–III each 48; IV–V each 96; VI 304; VII–X each 56; XI–XII each 8.

These are observed properties of the local snapshot, not by themselves proof of historical completeness. Completeness is supported by the scholarly enumeration and can be strengthened by an independent generator.

## Interpretation

“880” means equivalence classes under the eight position symmetries of the square (D4 rotations and reflections). For this normal 4×4 dataset, all entries are distinct, so no grid can be fixed by a nonidentity position symmetry: each such symmetry would force at least one pair of distinct positions in the same cycle to contain equal values. Hence every orbit has size exactly 8 and the oriented total is `880 × 8 = 7,040`. The local audit also directly constructs and counts that union, avoiding reliance on multiplication alone.
