# Sub-subagent Report — 1215-M1-S1

**Agent:** 1215-M1-S1  
**Task:** Provenance, authoritative sources, and 880-versus-7040 interpretation  
**Manager:** 1215-M1  
**Status:** Complete

## Work Product

### Executive summary

Normal order-4 magic squares use labels {1,…,16} with magic constant 34 (all rows, columns, and both main diagonals sum to 34). The classical **880** count is a **D4 quotient**: one representative per orbit of the dihedral group of order 8 (four rotations + four reflections). The **7,040** count is the **oriented** total before quotienting — every distinct labeled placement.

The identity **7,040 = 880 × 8** holds because every normal square has **trivial D4 stabilizer** (only the identity transformation fixes the grid). Orbit–stabilizer therefore gives orbit size 8 for all 880 classes. This was confirmed by **reproduced observation** in this folder (independent enumeration and CSV audit), not merely cited from literature.

**Do not conflate** D4 with complement (x ↦ 17−x), Dudeney’s 12 link-line types, row/column interchange groups, or toroidal equivalence — each yields different counts. Complement is a **separate ℤ₂ involution on values**: applied entrywise, then re-canonicalized under D4, it partitions the 880 D4 classes into **616 complement-orbits** — **352** fixed classes plus **264** two-cycles among the remaining **528** classes (**reproduced observation** on read-only CSV).

---

### Authoritative sources (tiered)

#### Tier 1 — Primary / canonical

| Source | Bibliography | URL | Claim type |
|--------|--------------|-----|------------|
| **Frénicle de Bessy (1693)** | *Table générale des quarrez magiques de quatre de costé*, in *Divers ouvrages de mathématique et de physique* (Académie Royale des Sciences, Paris 1693), pp. 484–503 | OEIS entry links: https://oeis.org/A006052 | **Literature:** 880 classes under rotation/reflection |
| **Ollerenshaw & Bondi (1982)** | *Magic squares of order four*, Phil. Trans. R. Soc. Lond. A **306**, 443–532 | https://doi.org/10.1098/rsta.1982.0093 | **Literature:** analytical re-proof of 880; appendix lists all squares; proves 12 Dudeney types |
| **OEIS A006052** | Sloane et al.; “counted up to rotations and reflections” | https://oeis.org/A006052 | **Literature/registry:** a(4)=880 |

#### Tier 2 — Oriented count & historiography

| Source | Bibliography | URL | Claim type |
|--------|--------------|-----|------------|
| **Dudeney (1917)** | *Amusements in Mathematics* (Nelson); Ch. on 4×4 squares | https://en.wikisource.org/wiki/Amusements_in_Mathematics | **Literature:** 7,040 oriented; 880 fundamental under “reversals and reflections” |
| **Gardner (1976)** | Sci. Amer. 249(1):118 | via OEIS refs | **Literature:** computer confirmation of 880 |
| **Lehmer (1933)** | Bull. AMS 39(12):981–982 | https://doi.org/10.1090/s0002-9904-1933-05790-7 | **Literature:** early 20th-c. census |
| **Berlekamp–Conway–Guy** | *Winning Ways* Vol. II, pp. 778–783 | (book) | **Literature:** tabulates 880 D4 classes |

#### Tier 3 — Machine-readable datasets

| Source | URL | Format | Provenance notes |
|--------|-----|--------|------------------|
| **RecMath / Harvey Heinz** | http://www.recmath.org/Magic%20Squares/order4list.htm | HTML + ZIP | **MS4_List-Index.zip**, **MS4_List-Group.zip** — Frénicle index, Dudeney group metadata |
| **RecMath downloads** | http://www.recmath.org/Magic%20Squares/downloads.htm | ZIP | Same 880 squares; group-sorted variant |
| **MagicMomentExplorer CSV** (read-only) | `/Users/kylemathewson/MagicSK/MagicMomentExplorer/data/magic_squares_880.csv` | CSV | Project derivative; audited here |
| **arXiv 2601.06131 (2026)** | https://arxiv.org/abs/2601.06131 | CSV + code (repo linked in PDF) | `magic_squares_4x4.csv`; preprint — verify before production |
| **Kazunosekai** | https://www.kazunosekai.com/magicsquares/magic_squares_4x4/ | CSV | Community mirror; license unstated |
| **Gizmoscope/magic-square** | https://github.com/Gizmoscope/magic-square | C source | Algorithm reference for 7,040 enumeration |

Extended bibliography and ingestion checklist: `source_notes.md`.

---

### 880 versus 7,040 — precise definitions

| Term | Definition | Count | Label |
|------|------------|-------|-------|
| **Normal** | 4×4 bijection from cells to {1,…,16} with all 10 line sums = 34 | — | Definition |
| **Oriented** | Distinct labeled matrix; no symmetry identification | **7,040** | **Reproduced observation** (this agent) |
| **D4 class / fundamental** | Orbit under dihedral group of order 8 | **880** | **Reproduced observation** + **literature claim** (Frénicle 1693) |
| **Frénicle standard form** | Canonical representative: smallest corner at (1,1); tie-break (1,2) < (2,1) | **880** classes | **Literature convention** |
| **Lex-min D4 canonical** | Lexicographically smallest tuple among 8 D4 images | **880** classes | **Reproduced observation** (matches project CSV) |

**Literature claim (Dudeney 1917, Wikisource):** “every one of these squares will produce seven others by mere reversals and reflections … 7,040 squares … 880 fundamentally different.”

**Literature claim (OEIS A006052):** a(4) = 880 “counted up to rotations and reflections.”

**Reproduced observation (`verify_enumeration.py`):** oriented_count = 7,040; d4_canonical_lex_count = 880; product 880×8 = 7,040.

---

### Orbit–stabilizer logic (D4 action)

Let **G = D4**, |G| = 8, acting on the set **X** of oriented normal 4×4 magic squares by rotating/reflecting the physical grid (equivalently: conjugating cell positions).

For S ∈ X:

- **Orbit:** orb(S) = {g·S : g ∈ G}
- **Stabilizer:** stab(S) = {g ∈ G : g·S = S}
- **Orbit–stabilizer theorem:** |orb(S)| · |stab(S)| = |G|

Hence:

- If |stab(S)| = 1 (trivial stabilizer), then |orb(S)| = 8.
- If |stab(S)| = 2, then |orb(S)| = 4 (would reduce oriented total below 880×8).
- If |stab(S)| = 4, then |orb(S)| = 2.
- If |stab(S)| = 8, then |orb(S)| = 1 (fully symmetric square).

**Sum over representatives:** |X| = Σ_C |orb(C)| where C ranges over D4 classes. If every orbit has size 8, |X| = 880 × 8 = 7,040.

**Reproduced observation:** stabilizer histogram on all 7,040 oriented squares is {1: 7040}; orbit size on all 880 canonical reps is {8: 880}.

---

### Can nontrivial D4 stabilizers occur for normal 4×4 squares?

**Answer: No** — for squares using each of 1,…,16 exactly once.

**Proof sketch (group theory + distinctness):**

1. Any non-identity element of D4 acts nontrivially on cell positions, partitioning cells into orbits of size 2 or 4 (for reflections / 90°-rotation type elements) under the non-identity element.
2. If g·S = S, then entries at positions in each g-orbit must be **equal** (the same label occupies all cells in the orbit).
3. Distinct labels 1,…,16 cannot repeat on two cells; therefore no orbit of size > 1 can be monochromatic under S.
4. Thus only the identity fixes S, and |stab(S)| = 1.

**Skeptic note:** “Symmetric magic square” in Ollerenshaw’s sense means **complementary pairs** (a, 17−a) occupy centrosymmetric **positions** — not that the matrix is invariant under a nontrivial D4 motion. Dürer’s Melancholia square is “symmetrical” in that sense but still has trivial D4 stabilizer as a labeled matrix.

**Naming caveat:** Sources alternately write **D4** (dihedral group of degree 4, order 8) or **D8** (order 8). This report uses **D4** consistently with OEIS / manager brief wording; the group is always the 8-element square symmetry group.

---

### Complement involution (separate from D4)

Entrywise complement **C(S)** replaces each label x with 17−x (magic constant 34). This is **not** a D4 motion; it commutes with grid symmetries but induces a separate equivalence on **D4-class representatives**.

Workflow for class-level analysis:

1. Start from a D4-canonical representative S.
2. Apply C entrywise to obtain C(S).
3. Re-canonicalize C(S) under D4 to obtain a class representative C̄(S).

Because C∘C = identity on values, this induces an **involution** on the set of 880 D4 classes:

| Complement orbit type | D4 classes involved | Count | Label |
|-----------------------|---------------------|-------|-------|
| **Fixed class** (C̄(S) = S) | 1 per orbit | **352** | **Reproduced observation** |
| **Two-cycle** {S, C̄(S)}, S ≠ C̄(S) | 2 per orbit | **264** orbits → **528** classes | **Reproduced observation** |
| **Total complement-orbits** | 352 + 264 | **616** | **Reproduced observation** |

Check: 352 + 528 = 880 D4 classes. **Not** 440 unordered pairs — that count would wrongly assume every non-fixed class pairs cleanly without accounting for the 352 fixed classes.

**Reproduced observation (`verify_complement.py` on read-only CSV):** fixed=352, two_cycles=264, complement_orbits=616; all `complement_id` metadata consistent.

---

### Equivalence relations — explicit non-conflation

| Relation | Typical count on order 4 | Same as D4? |
|----------|--------------------------|-------------|
| **D4** (rotations + reflections) | 880 classes / 7,040 oriented | — |
| **Complement** x ↦ 17−x (on D4 classes) | 616 complement-orbits: 352 fixed + 264 two-cycles | **No** |
| **Dudeney 12 types** (complement-pair link geometry) | partition of 880 (48+48+…=880) | **No** |
| **Row/column interchange** (order-32 subgroup for order 4) | different classification | **No** |
| **Magic tori** (toroidal quotient) | **255** essentially different tori (literature) | **No** |

The 880 count is **only** the D4 orbit-space cardinality for normal squares.

---

### Reproducible acquisition & ingestion

**Recommended pipeline:**

1. **Acquire:** RecMath `MS4_List-Index.zip` (http://www.recmath.org/Magic%20Squares/Downloads/MS4_List-Index.zip) or transcribe Ollerenshaw appendix.
2. **Parse:** row-major 16-tuples, IDs 1–880.
3. **Validate:** sorted cells = 1..16; ten line sums = 34.
4. **Canonicalize:** D4 images → lex-min or Frénicle form (document choice).
5. **Integrity asserts:** 880 unique canonical keys; each representative has |orb| = 8; union of orbits has 7,040 elements.
6. **Optional metadata:** Dudeney group, complement_id (from CSV schema or RecMath lines).

**Integrity checks implemented here:**

| Check | Script | Result |
|-------|--------|--------|
| Independent oriented enumeration | `verify_enumeration.py` | 7,040 unique oriented; 880 D4 classes |
| Project CSV audit (read-only) | `cross_validate_dataset.py` | 880 rows, all magic, orbit 8 each, union 7,040 |
| Stabilizer scan | both scripts | all stabilizers trivial |
| Complement involution on D4 classes | `verify_complement.py` | 352 fixed, 264 two-cycles, 616 orbits |

**Commands:**

```bash
cd /Users/kylemathewson/MagicSK/backgroundMaterial/agent1215/coordinator/manager_M1/sub_S1
python3 verify_enumeration.py          # ~72 s; writes verify_enumeration_results.json
python3 cross_validate_dataset.py \
  /Users/kylemathewson/MagicSK/MagicMomentExplorer/data/magic_squares_880.csv \
  --output cross_validate_results.json
python3 verify_complement.py \
  /Users/kylemathewson/MagicSK/MagicMomentExplorer/data/magic_squares_880.csv \
  --output complement_verify_results.json
```

---

### Licensing & reuse caveats

| Asset | Caveat |
|-------|--------|
| Frénicle (1693) | Public-domain mathematics; scan rights depend on host |
| Ollerenshaw & Bondi (1982) | Royal Society — paywalled; tabular reuse subject to publisher terms |
| OEIS A006052 | CC BY-SA 4.0 for text; attribute OEIS |
| RecMath ZIPs | No explicit license; research reference; verify mirror longevity |
| Dudeney / Wikisource | Public domain |
| arXiv 2601.06131 | Preprint license; code per repo LICENSE |
| MagicMomentExplorer CSV | Internal derivative — chain provenance to Tier 1 |

---

### Count label summary

| Count | Value | Status |
|-------|-------|--------|
| D4 classes (880) | 880 | **Literature claim** (Frénicle 1693, Ollerenshaw 1982, OEIS) + **reproduced observation** |
| Oriented normal squares (7,040) | 7,040 | **Literature claim** (Dudeney 1917) + **reproduced observation** |
| D4 orbit size for every class | 8 | **Reproduced observation** |
| Nontrivial stabilizer exists | false | **Proof** (distinct labels) + **reproduced observation** |
| Dudeney 12-type partition | sums to 880 | **Literature claim** (Dudeney; proved Ollerenshaw 1982) |
| Complement fixed D4 classes | 352 | **Reproduced observation** |
| Complement two-cycles (among remaining 528 classes) | 264 | **Reproduced observation** |
| Complement-orbits total | 616 | **Reproduced observation** |

## Files

| File | Purpose |
|------|---------|
| `S1_report.md` | This deliverable — provenance, equivalence logic, acceptance checklist |
| `source_notes.md` | Extended bibliography, URLs, ingestion pipeline, non-conflation table |
| `verify_enumeration.py` | Independent 7-parameter enumeration of all oriented normal squares |
| `verify_enumeration_results.json` | Machine output: 7040 oriented, 880 D4 classes, stabilizer/orbit histograms |
| `cross_validate_dataset.py` | Audits an 880-row CSV for magic property, D4 orbits, oriented union |
| `cross_validate_results.json` | Audit of read-only `magic_squares_880.csv` |
| `verify_complement.py` | Audits complement involution on D4 classes (fixed / two-cycle counts) |
| `complement_verify_results.json` | Complement orbit audit: 352 fixed, 264 two-cycles, 616 orbits |

## Acceptance Criteria Check

| Criterion | Met? | Evidence |
|-----------|------|----------|
| Authoritative primary/scholarly sources identified | Yes | Frénicle 1693, Ollerenshaw–Bondi 1982, OEIS A006052, Dudeney 1917 |
| 880 vs 7,040 explained with orbit–stabilizer | Yes | Work Product sections above; 880×8=7040 |
| Nontrivial D4 stabilizers addressed | Yes | Proof + histogram {1:7040} |
| Reproducible acquisition/ingestion options | Yes | RecMath ZIPs, Ollerenshaw DOI, CSV audit path |
| Exact URLs & bibliographic details | Yes | `source_notes.md` + tables above |
| Provenance, integrity checks, licensing | Yes | Dedicated sections |
| Counts labeled reproduced vs literature | Yes | Count label summary table |
| D4 not conflated with complement/other equivalences | Yes | Complement section + non-conflation table; 616 orbits verified |
| Supporting artifacts created | Yes | Two Python scripts + three JSON/MD outputs |
| File boundary respected | Yes | All writes under `sub_S1/` only |

## Questions for Manager

No questions — task was clear.

## Self-Assessment

- **Craftsperson says:** Manager corrections applied: complement is now described as a separate involution with 352 fixed D4 classes, 264 two-cycles, and 616 total orbits — verified independently on the read-only CSV. OEIS license corrected to CC BY-SA 4.0. D4/oriented counts remain reproduced from scratch enumeration.
- **Skeptic says:** The erroneous “440 pairs” conflation is removed, but complement counts are still CSV-dependent here (not re-derived from the 7,040 oriented enumeration). RecMath mirror longevity and arXiv GitHub URL resolution remain open. Frénicle index ordering vs lex-min canonicalization not proven identical.
- **Mover says:** Corrected report ships with a new `verify_complement.py` artifact so downstream agents can re-audit complement metadata without re-deriving the logic. Remaining provenance gaps stay flagged for M1 ingestion.

*Dated footer: 2026-07-09 — 1215-M1-S1*
