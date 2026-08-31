# Accessible 4×4 Diagram & Moment-Energy Visualization Semantics

**Agent:** 1215-M3-S2  
**Applies to:** Selected-square inspection panel and comparison mini-diagrams.

---

## 1. Selected-square 4×4 diagram

### 1.1 DOM structure (required)

```html
<div id="square-diagram"
     role="grid"
     aria-labelledby="diagram-heading"
     aria-describedby="diagram-instructions diagram-status"
     aria-rowcount="4"
     aria-colcount="4">
  <!-- 16 cells -->
  <button type="button" role="gridcell"
          aria-rowindex="1" aria-colindex="1"
          aria-label="Row 1, column 1, value 8"
          class="square-cell" data-index="0" tabindex="0">8</button>
  <!-- … -->
</div>
<p id="diagram-instructions" class="visually-hidden">
  Arrow keys move between cells. Enter or Space selects a cell and highlights its row and column.
  Home and End jump to the first or last column in the current row. Escape clears cell selection.
</p>
<p id="diagram-status" role="status" aria-live="polite" aria-atomic="true"></p>
```

**Grid vs gridcell:** Container carries `role="grid"`; each cell is a **focusable** `<button role="gridcell">` (not roving `div`). This gives native focus ring and activation for free.

### 1.2 Roving tabindex

- Exactly one cell has `tabindex="0"`; others `tabindex="-1"`.
- Arrow keys move focus and update tabindex.
- Container **may** have `tabindex="0"` only if it acts as entry point that forwards focus to cell 0 on Enter; prefer focusing first cell directly when inspect opens.

### 1.3 Visual states (CSS classes)

| Class | Meaning | Required contrast |
|-------|---------|-------------------|
| `.is-focused` | `:focus-visible` ring | 3:1 against adjacent |
| `.is-selected` | Active cell (Enter/Space) | Fill + 3:1 border |
| `.is-row-col-highlight` | Row/col of selected or focused-without-selection | Subtle background |
| `.is-complement` | Optional: complement partner cells | Pattern + hue |
| `.is-magic-sum-ok` | Line sum equals 34 | No color-only cue; use weight + ✓ in `aria-label` when line overlay mode |

### 1.4 Keyboard behavior (normative)

| Key | Behavior |
|-----|----------|
| `ArrowUp/Down/Left/Right` | Move focus; `preventDefault` |
| `Home` | Focus col 1 same row |
| `End` | Focus col 4 same row |
| `Enter` / `Space` | Toggle select focused cell; announce |
| `Escape` | Clear selection; keep focus |
| `PageUp/Down` | Optional: jump row ±1 (same col) |

**On inspect open:** `focusFirst()` → cell 0, announce `Square for record M042. Row 1 column 1 value 1.`

### 1.5 Screen reader announcements

`diagram-status` updates on focus and selection:

```text
Cell row 2 column 3 value 13. Selected.
```

When selection clears:

```text
Selection cleared. Cell row 2 column 3 value 13.
```

Do not spam on mouse hover; pointer users get `title` tooltips optional.

### 1.6 Text alternative (line sums table)

Always render adjacent `<table>` with caption **“Line sums for {recordId}”**:

| Kind | Values | Defect |
|------|--------|--------|
| Rows | 34, 34, 34, 34 | 0 |
| Columns | … | — |
| Diagonals | … | — |

Table is **not** hidden; diagram is supplemental graphics.

### 1.7 Comparison mini-diagrams

- `role="img"` with `aria-label="4 by 4 square for M042: row 1 values 1 2 15 16, …"` **or** shrunken interactive grid with `aria-readonly="true"` and no selection (focus allowed for parity).
- Prefer readonly label for compare tiles to reduce tab stops; full diagram only in inspect panel.

---

## 2. Moment-energy visualization (SVG + HTML)

### 2.1 Purpose

Show **where** interaction energy lives across orthonormal modes `Mxy` (excluding `M00`) and aggregated **degree** buckets.

### 2.2 Mode energy heatmap (SVG)

```html
<figure class="energy-figure">
  <svg role="img"
       aria-labelledby="mode-heatmap-title mode-heatmap-desc"
       class="energy-svg" viewBox="…">
    <title id="mode-heatmap-title">Mode energy heatmap for M042</title>
    <desc id="mode-heatmap-desc">
      Four by four grid of spatial mode energies. Cell M00 is omitted (mean height mode).
      Higher energy cells use darker blue. Maximum mode energy 156.8 in M12.
    </desc>
    <!-- rects with <title>M12: 156.80</title> per cell -->
  </svg>
  <figcaption>Interaction mode energies (excluding M00)</figcaption>
</figure>
```

**Cell semantics:**

| Position | Label | Special |
|----------|-------|---------|
| (0,0) | `M00` | Render neutral “—”; not part of energy scale |
| (x,y) | `M{x}{y}` | Fill ∝ `modeEnergy[name]`; text label `xy` monospace |

**Color:** Do not rely on color alone; each cell shows numeric `title` and visible 2-digit energy in high-contrast label when space permits.

**Patterns:** Optional `fill="url(#hatch-high)"` for top quartile when `prefers-contrast: more`.

### 2.3 Degree energy bar chart (SVG)

```html
<svg role="img" aria-labelledby="degree-bar-title degree-bar-desc" …>
  <title id="degree-bar-title">Degree energy bars for M042</title>
  <desc id="degree-bar-desc">Bar heights show total energy for polynomial degrees 2 through 6.</desc>
</svg>
```

Bars map `degreeEnergy["2"]` … `["6"]`; y-axis implicit (no unlabeled axis in v1); each bar has `<title>degree 3: 156.80</title>` and text label above bar.

### 2.4 Summary list (HTML)

Unordered list pairing label + `<strong>` value for:

- Axial energy, Interaction energy, Low-order, High-order, Spectral centroid, Line defect energy

Ensures SR users get totals without parsing SVG.

### 2.5 Numeric fallback table (required)

Inside `<details>` default **closed**:

```html
<details>
  <summary>Show numeric energy table</summary>
  <table>
    <caption>Coefficients and energies for M042</caption>
    <thead><tr><th>Mode</th><th>Coefficient</th><th>Energy</th></tr></thead>
    <tbody>… all Mxy + degree rows …</tbody>
  </table>
</details>
```

This satisfies “SVG/HTML semantics” — SVG is primary graphic; HTML table is equivalent content.

### 2.6 Reduced motion

No bar height CSS transitions; static SVG. If animating load, respect `prefers-reduced-motion`.

### 2.7 Data binding

| Visual | Record fields |
|--------|---------------|
| Heatmap cell | `modeEnergy.Mxy`, `coefficients.Mxy` (tooltip) |
| Degree bars | `degreeEnergy["2"]`…`["6"]` |
| Summary | `axialEnergy`, `interactionEnergy`, `lowOrderEnergy`, `highOrderEnergy`, `spectralCentroid`, `lineDefectEnergy` |

---

## 3. Integration checklist for implementers

- [ ] Diagram uses 16 buttons, roving tabindex, documented keys.
- [ ] `diagram-status` is `aria-live="polite"`.
- [ ] Line sums table adjacent and captioned.
- [ ] Each SVG has `<title>` + `<desc>` referenced by `aria-labelledby`.
- [ ] Per-shape `<title>` tooltips for values.
- [ ] Collapsible full numeric table present.
- [ ] Compare tiles use compact `aria-label` unless full grid requested.

---

*End of diagram & energy semantics.*
