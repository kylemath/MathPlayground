# Literature and source references — 1215-M1-S3

Primary sources consulted for definitions and count claims. URLs verified 2026-07-09.

## Enumeration and equivalence

| Claim | Source | URL / citation |
|---|---|---|
| 880 essentially different normal order-4 magic squares | Bernard Frénicle de Bessy (1693), posthumous *Des Quarrez Magiques* | [Heinz transform page](http://www.recmath.org/Magic%20Squares/transform.htm); [Wikipedia: Frénicle standard form](https://en.wikipedia.org/wiki/Fr%C3%A9nicle_standard_form) |
| Independent confirmation (880) | Kathleen Ollerenshaw & Hermann Bondi (1982), “Magic squares of order four” | [Phil. Trans. R. Soc. A](https://doi.org/10.1098/rsta.1982.0093) |
| Computer re-verification (1976) | Martin Gardner, *Scientific American* | doi:10.1038/scientificamerican0576-118 |
| 7040 oriented squares (= 880 × 8) | Multiple authors; explicit in Meyer / ROJISA | [Meyer mag4the](http://www.hbmeyer.de/backtrack/mag4the.htm); [ROJISA 2013 PDF](http://www.scitecpub.com/Research%20Open%20Journal%20of%20Information%20Science%20and%20Application/ROJISA_Vol.%201,%20No.%201,%20August%202013/Special%20Magic.pdf) |

## D4 / Frénicle standard form

| Rule | Source |
|---|---|
| Smallest corner in top-left; then cell (1,2) < cell (2,1) | [Wikipedia](https://en.wikipedia.org/wiki/Fr%C3%A9nicle_standard_form); [Heinz transform.htm](http://www.recmath.org/Magic%20Squares/transform.htm) |
| Eight D4 images per class (no nontrivial stabilizer for this dataset) | Reproduced in `count_results.json` |

## Dudeney 12-group classification

| Source | Notes |
|---|---|
| H. E. Dudeney, *The Queen* (15 Jan 1910); *Amusements in Mathematics* (1917) | Pattern of eight complementary pairs (sum 17) |
| [Heinz order4list.htm](http://www.recmath.com/Magic%20Squares/order4list.htm) | Group sizes: I=48, II=48, III=48, IV=96, V=96, VI-P=96, VI-S=208, VII–X=56 each, XI–XII=8 each |
| [Book of Proofs — Dudeney](https://bookofproofs.github.io/branches/fun/dudeney/magic-square-problems/magic-square-problems.html) | Nasik / Semi-Nasik / Simple terminology |

## Property definitions

| Term | Source |
|---|---|
| Pandiagonal / Nasik / panmagic | Dudeney; [MathWorld Associative](https://mathworld.wolfram.com/AssociativeMagicSquare.html) (contrasts with panmagic) |
| Associative (center-symmetric complements) | [MathWorld](https://mathworld.wolfram.com/AssociativeMagicSquare.html); OEIS A081262 (48 for order 4) |
| Most-perfect (2×2 toroidal blocks + diagonal complements) | Kathleen Ollerenshaw & David Bree; [RecMath most-perfect](http://www.recmath.org/Magic%20Squares/most-perfect.htm) |
| Order-4 most-perfect ⟺ pandiagonal | [RecMath most-perfect](http://www.recmath.org/Magic%20Squares/most-perfect.htm); reproduced computationally |
| Semi-pandiagonal / Semi-Nasik (typological) | Dudeney groups II–VI-P; **384 literature total** — pattern-based, not one universal line-sum rule |
| Bent-diagonal semi-pandiagonal (Type II) | [Heinz Group II](http://www.recmath.org/Magic%20Squares/order4list.htm#Group%20II) |

## Reproducible dataset

| Artifact | Provenance |
|---|---|
| `magic_squares_880.csv` (read-only external) | Harvey D. Heinz transcription of Frénicle list: [order4lista–d.htm](http://www.recmath.org/Magic%20Squares/order4lista.htm) |
| Fetch/normalize script (read-only) | `MagicMomentExplorer/scripts/fetch_source.py` |

## Terminology not applied to order 4

| Term | Reason |
|---|---|
| Franklin magic square | Benjamin Franklin’s construction is chiefly cited for 8×8+ bent-diagonal designs; not a standard order-4 equivalence class in Frénicle/Dudeney literature |
| Compact (non-toroidal 2×2) | All **nine** contiguous 2×2 windows sum to 34; distinct from sixteen toroidal windows in most-perfect; for order 4 coincides with pandiagonal on our dataset (48) |
