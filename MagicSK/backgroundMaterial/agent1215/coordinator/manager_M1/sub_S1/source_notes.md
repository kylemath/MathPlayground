# Source Notes — Normal Order-4 Magic Squares (1215-M1-S1)

Working bibliography and acquisition pointers. Count labels: **literature claim** vs **reproduced observation** (this agent's scripts).

---

## Tier 1 — Primary / canonical enumeration

### Frénicle de Bessy (1693) — original 880 claim

- **Title:** *Table générale des quarrez magiques de quatre de costé* (also spelled *carrez*)
- **In:** *Divers ouvrages de mathématique et de physique par Messieurs de l'Académie Royale des Sciences* (Paris, 1693)
- **Pages:** 484–503 (OEIS links pp. 484–503; ResearchGate cites 484–507)
- **URL (OEIS link):** https://oeis.org/A006052 (references section links to scanned ouvrages)
- **Claim (literature):** 880 essentially different normal 4×4 magic squares under rotation/reflection equivalence.
- **Provenance:** Posthumous publication; enumeration by exhaustion / complete table.
- **Licensing:** Public-domain historical text (17th c.); scan rights depend on hosting library.
- **Caveat:** Original indexing is not modern CSV; Frénicle standard form predates lexicographic canonicalization used in software.

### Ollerenshaw & Bondi (1982) — analytical re-proof + full list

- **Authors:** Kathleen Ollerenshaw, Hermann Bondi
- **Title:** *Magic squares of order four*
- **Journal:** Philosophical Transactions of the Royal Society of London. Series A, Mathematical and Physical Sciences
- **Volume / pages:** Vol. 306, pp. 443–532 (October 15, 1982)
- **DOI:** https://doi.org/10.1098/rsta.1982.0093
- **Claim (literature):** Confirms 880; first analytical proof of 12 Dudeney complement-pair types; appendix lists all 880 in symmetrical form.
- **Provenance:** Royal Society; peer-reviewed; widely cited successor to Frénicle.
- **Licensing:** Paywalled via publisher; abstract/metadata open. Reuse of tabular data requires publisher terms.
- **Integrity check:** Cross-check appendix rows against Frénicle index / RecMath list.

### OEIS A006052 — sequence registry

- **URL:** https://oeis.org/A006052
- **Definition:** Number of **normal** magic squares of order *n* on {1,…,n²}, **counted up to rotations and reflections**.
- **a(4) = 880** (literature claim, attributed to Frénicle 1693).
- **References:** Winning Ways II (Berlekamp–Conway–Guy), Gardner 1976/1988, Frénicle scans.
- **Licensing:** OEIS text CC BY-SA 4.0 (attribution required); sequence values are facts.
- **Caveat:** Sequence quotients **D4 only** — not complement, row/column swap, or toroidal equivalence.

---

## Tier 2 — Oriented count 7,040 and secondary verification

### Dudeney (1917) — 7,040 oriented / 880 fundamental

- **Title:** *Amusements in Mathematics*
- **Publisher:** Nelson (1917); also Wikisource
- **URL:** https://en.wikisource.org/wiki/Amusements_in_Mathematics (Ch. XXII; page ~133 in djvu)
- **Claim (literature):** "7,040 squares of this order, 880 of which are fundamentally different" from reversals and reflections.
- **Also classifies 880 into 12 graphic types** (complement-pair link patterns) — **not** the same as D4 quotient.
- **Licensing:** Public domain (US/Wikisource).

### Gardner (1976) — computer confirmation

- **Title:** Mathematical Games, Scientific American Vol. 249 No. 1 (1976), p. 118
- **Claim (literature):** Computer re-enumeration confirms 880 (cited in OEIS, Bondi abstract).
- **Caveat:** Popular exposition; use for historiography, not machine ingestion.

### Lehmer (1933) — census note

- **Title:** *A census of squares of order 4, magic in rows, columns, and diagonals*
- **Journal:** Bull. AMS 39(12):981–982
- **DOI:** https://doi.org/10.1090/s0002-9904-1933-05790-7
- **Role:** Early 20th-c. recount in the Frénicle tradition.

### Berlekamp, Conway & Guy — *Winning Ways* Vol. II

- **Pages:** 778–783
- **Claim (literature):** Presents all 880 (D4 classes).
- **Licensing:** Copyrighted book; fair-use citation only.

### Schroeppel (1973) — order-5; cited for order-4 tradition

- OEIS notes Schroeppel for order 5; order-4 line remains Frénicle/Ollerenshaw chain.

---

## Tier 3 — Machine-readable datasets (ingestion)

### RecMath (Harvey Heinz) — 880 Frénicle-indexed lists

- **Index page:** http://www.recmath.org/Magic%20Squares/order4list.htm
- **Downloads:**
  - http://www.recmath.org/Magic%20Squares/Downloads/MS4_List-Index.zip (880 squares, Frénicle index order)
  - http://www.recmath.org/Magic%20Squares/Downloads/MS4_List-Group.zip (same, sorted by Dudeney group)
- **Format:** Text inside ZIP; one square per line with metadata (group, complement partner).
- **Provenance:** Compiled from Frénicle/Ollerenshaw line; site maintainer Harvey Heinz (deceased 2013); mirror status uncertain.
- **Integrity checks:** (1) 880 lines, (2) each is normal magic, (3) unique Frénicle forms, (4) D4 orbit size 8 each, (5) union size 7,040.
- **Licensing:** Not explicitly stated; treat as research reference — contact Successors / mirror maintainers before commercial reuse.

### MagicMomentExplorer CSV (read-only cross-check, not modified)

- **Path (read-only):** `/Users/kylemathewson/MagicSK/MagicMomentExplorer/data/magic_squares_880.csv`
- **Columns:** id, dudeney_group, group_orientation, cell_1..cell_16, complement_pair, complement_id
- **Coordinator audit (reproduced observation, 2026-07-09):** 880 rows, all magic, all D4 orbits size 8, oriented union 7,040.
- **Caveat:** Project-local derivative; provenance chain should cite Frénicle/Ollerenshaw/RecMath.

### arXiv 2601.06131 (2026) — CSV + code

- **Title:** *Algebraic Classification of All 880 Fourth-Order Magic Squares…*
- **URL:** https://arxiv.org/abs/2601.06131
- **Data:** `magic_squares_4x4.csv` (IDs 1–880, row-major 16-tuples)
- **Code:** Author GitHub repository linked in paper (search paper HTML for repository URL at ingest time).
- **Licensing:** arXiv preprint license; code license per repository LICENSE file.
- **Caveat:** Preprint (2026); independent verification advised before treating as authoritative over Ollerenshaw.

### Kazunosekai — CSV mirror

- **URL:** https://www.kazunosekai.com/magicsquares/magic_squares_4x4/
- **Format:** CSV, 16 integers per row.
- **Licensing:** Not stated; verify before redistribution.

### Gizmoscope/magic-square — algorithm reference for 7,040

- **URL:** https://github.com/Gizmoscope/magic-square
- **Claim (literature/code comment):** Enumerates 7,040 oriented order-4 magic squares via linear constraints.
- **Use:** Algorithmic verification pattern, not canonical indexing.

---

## Equivalence relations — do not conflate

| Relation | Typical count | Group / rule | Same as D4? |
|----------|---------------|--------------|-------------|
| D4 (rotations + reflections) | 880 classes; 7,040 oriented | \|D4\| = 8 | — |
| Complement x ↦ 17−x (on D4 classes) | 616 complement-orbits: **352** fixed classes + **264** two-cycles (528 classes) | ℤ₂ on values, then D4 re-canonicalize | No |
| Dudeney 12 types | Partition of 880 | Complement-pair geometry | No |
| Row/column interchange | Different group (order 32 for order 4) | Burns / Gaspalou | No |
| Toroidal / magic torus | 255 magic tori (literature) | Torus quotient | No |

**Complement detail (reproduced observation, read-only CSV audit):** Entrywise complement induces an involution on the 880 D4 classes. A class is **fixed** if C̄(S) = S (352 cases). Otherwise it forms a **two-cycle** with its complement partner (264 pairs covering 528 classes). Total complement-orbits = 352 + 264 = **616**. This is **not** “440 unordered pairs.”

---

## Recommended ingestion pipeline

1. **Acquire** RecMath `MS4_List-Index.zip` or Ollerenshaw appendix (manual transcription).
2. **Parse** to row-major 16-tuples on {1,…,16}.
3. **Validate:** `sorted(cells)==1..16`, all 10 lines sum to 34.
4. **Canonicalize:** apply D4; keep lex-min or Frénicle form (document choice).
5. **Assert:** 880 unique canonical keys; orbit size 8 for every stored representative.
6. **Derive oriented set:** union of D4 images → expect 7,040.
7. **Optional:** map complement orbits (`verify_complement.py`: expect 352 fixed, 264 two-cycles, 616 total) and Dudeney groups from RecMath metadata columns.

---

*Compiled 2026-07-09 by agent 1215-M1-S1; revised same day per manager review (complement counts, OEIS license).*
