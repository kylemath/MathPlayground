# Magic Moment Explorer

A reproducible, zero-dependency analysis and browser for the 880 fundamental
normal order-4 magic squares, their spatial-moment spectra, and deterministic
control cohorts.

## What “880” means

There are 880 equivalence classes of normal 4×4 magic squares after rotations
and reflections by the dihedral group D4 are identified. Every square contains
the integers 1–16 exactly once and has row, column, and main-diagonal sum 34.
Because all entries are distinct, every class has eight oriented forms, giving
7,040 oriented squares.

The checked-in source list is the Frénicle-indexed census compiled by Harvey
Heinz:

- Introduction and classification:
  <http://www.recmath.org/Magic%20Squares/order4list.htm>
- Records 1–200:
  <http://www.recmath.org/Magic%20Squares/order4lista.htm>
- Records 201–400:
  <http://www.recmath.org/Magic%20Squares/order4listb.htm>
- Records 401–600:
  <http://www.recmath.org/Magic%20Squares/order4listc.htm>
- Records 601–880:
  <http://www.recmath.org/Magic%20Squares/order4listd.htm>

`scripts/fetch_source.py` downloads those pages, parses their tabular records,
and rejects the result unless it contains IDs 1–880 in order and every record
is a valid normal magic square.

## Moment definition

Let the centered height field be

```text
z(i,j) = a(i,j) - 8.5
```

on cell coordinates `x,y = (-1.5, -0.5, 0.5, 1.5)`. Gram–Schmidt
orthonormalization of the monomials `1, x, x², x³` gives four discrete basis
vectors `P₀,…,P₃`. The complete two-dimensional coefficients are

```text
M[p,q] = Σᵢⱼ Pₚ(xⱼ) P_q(yᵢ) z(i,j),     0 ≤ p,q ≤ 3.
```

Because every arrangement uses 1–16, `M[0,0] = 0` and the total centered
height energy is fixed:

```text
Σᵢⱼ z(i,j)² = 340.
```

The six axial coefficients `M[p,0]` and `M[0,q]`, for nonzero `p` or `q`,
encode every row and column residual. They all vanish for a magic square.
The nine coefficients with `p,q > 0` are mixed spatial interactions. Their
squared values are the displayed mode energies.

The degree bins are

```text
E[d] = Σ M[p,q]² over p,q > 0 and p+q=d,    d = 2,…,6.
```

For a magic square, `E[2]+…+E[6] = 340`: magic does not remove variation; it
moves all variance out of the axial modes. “Low-order energy” is `E[2]+E[3]`.
It is a proposed multipole-balance score, not a traditional magic-square
classification. Lower values mean less variation in the broadest mixed modes,
with the unavoidable energy shifted to finer modes.

Signed moments are not compared as “energy”; their squares are. The CSV
contains every individual mode energy so alternative objectives can be built
without rerunning the census.

## Groupings

The application exposes:

- The twelve Dudeney complement-pattern groups supplied by the source.
- Frénicle index and the source’s group-orientation code.
- D4 orbit size.
- Complement partner and self-complementarity.
- Computed associative, pandiagonal, and most-perfect flags.

The 48 fundamental pandiagonal order-4 squares are also most-perfect under the
toroidal 2×2 and complementary-diagonal definition used by the script.

## Controls

The default seed is `20260709`.

- `random`: 880 independent uniform shuffles of 1–16.
- `swap-1`: one pair of distinct positions swapped in each source square.
- `swap-2`: two disjoint position pairs swapped in each source square.
- `swap-3`: three disjoint position pairs swapped in each source square.

Each perturbation level starts from the original source square. They are not a
cumulative trajectory. A perturbed square retains its parent’s Dudeney label
for provenance, not as a claim that the damaged square is itself in that
magic-square group.

## Reproduce

Python 3.10 or newer is sufficient. There are no third-party packages and no
installation step.

```bash
python3 scripts/fetch_source.py
python3 scripts/analyze.py
python3 -m unittest discover -s tests -v
```

Generated artifacts:

- `data/magic_squares_880.csv` — normalized known source list.
- `data/analysis.csv` — flat 4,400-record analysis table.
- `data/analysis.json` — structured analysis.
- `data/analysis-data.js` — the same data wrapped for offline browser use.

Open `index.html` directly in a modern browser. Because the generated data is
loaded as a local JavaScript file, no web server, build process, CDN, or network
connection is required.

The distribution panel provides violin plots for line defects, axial and
interaction energies, degree bins E₂–E₆, spectral degree, and every individual
mixed-mode energy. Distributions can be grouped by cohort, Dudeney group, or
structural class and displayed on linear or `log(1 + value)` axes. Violin width
is normalized within each category; the thick line and dot show the
interquartile range and median.

Useful options:

```bash
python3 scripts/fetch_source.py --output path/to/source.csv
python3 scripts/analyze.py --input path/to/source.csv \
  --output-dir path/to/output --random-count 880 --seed 20260709
```

## Files

```text
MagicMomentExplorer/
├── index.html
├── styles.css
├── moments.js
├── app.js
├── README.md
├── data/
│   ├── magic_squares_880.csv
│   ├── analysis.csv
│   ├── analysis.json
│   └── analysis-data.js
├── scripts/
│   ├── fetch_source.py
│   └── analyze.py
└── tests/
    └── test_analysis.py
```
