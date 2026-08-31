# UX & Interaction Specification — Magic Moment Records Explorer (880 + controls)

**Agent:** 1215-M3-S2  
**Schema baseline:** `analysis.json` v0.1.0-prototype (4,400 expanded records; 880 magic representatives)  
**Constraint:** Zero npm/CDN dependencies; `file://` and local HTTP must both work.

---

## 1. Information architecture

### 1.1 Primary regions (landmark map)

| Region | Element | Role | Purpose |
|--------|---------|------|---------|
| Global | `<header>` | banner | Title, schema version, global load status |
| Global | `<nav aria-label="View mode">` | navigation | Table / cards toggle; optional summary tab |
| Primary | `#filters` | complementary **or** first `<section>` | Combined filters, sort keys, reset, share |
| Primary | `#summary` | region | Aggregates over **filtered** set |
| Primary | `#results` | main (if not wrapping all) | Scrollable result list (table or card grid) |
| Primary | `#inspect` | region | Selected-square diagram + moment-energy viz |
| Primary | `#compare` | region | Side-by-side comparison (2–4 records) |
| Global | `<footer>` | contentinfo | Data provenance, keyboard cheat sheet link |

**Reading order (desktop):** Header → Filters (left or top) → Summary strip → Results → Inspect → Compare.  
**Mobile:** Filters collapse into a bottom sheet or full-screen drawer; results occupy full width; inspect/compare become stacked tabs.

### 1.2 Page modes (single-page, no router library)

Three **view intents** share one document:

1. **Browse** — default; filters + results + optional inspect panel.
2. **Inspect** — deep link with `sel` or `inspect` param; auto-scroll/focus inspect region.
3. **Compare** — `compare` param with 2–4 IDs; compare panel expanded, inspect shows primary only.

Mode is derived from URL state, not a separate route file.

### 1.3 Record identity & cohort model

| Field | Filterable | Sortable | Display |
|-------|------------|----------|---------|
| `recordId` | prefix search | yes (tie-breaker) | Primary label (`M001` …) |
| `sourceId` | range, exact | yes | Magic rep # (1–880) |
| `cohort` | multi-select | yes | `magic`, `random`, `swap-1` … `swap-3` |
| `swaps` | 0–3 | yes | Badge on card |
| `dudeneyGroup` | multi-select 1–12 | yes | Roman + label from metadata |
| `classes[]` | AND/OR toggle | no (derived) | Tag chips |
| `isMagic` | boolean | yes | Icon + filter |
| `selfComplementary` | boolean | yes | Tooltip |
| `lineDefectEnergy` | range | yes | Conditional formatting |
| `lowOrderEnergy`, `highOrderEnergy` | range | yes | Summary + sort |
| `spectralCentroid` | range | yes | Summary + sort |
| `interactionEnergy` | range | yes | Default sort candidate |

**Cohort naming:** Use dataset literals (`swap-1`, not `swapped-1`) everywhere in UI labels, URL params, and tests.

### 1.4 Filter composition semantics

Filters combine with **AND** across dimensions; within a dimension:

| Dimension | Combination |
|-----------|-------------|
| Cohort | OR (multi-select) |
| Dudeney group | OR |
| Class tags | **Configurable:** default OR (“any selected class”), optional AND (“must have all”) |
| Numeric ranges | AND (each active range must pass) |
| Text search | AND with others; matches `recordId` prefix (case-insensitive) or exact `sourceId` |
| Magic only | AND (`isMagic === true`) |

**Empty filter set** = show all loaded records (subject to cohort bundle if user loads magic-only subset).

**Partial data:** If load returns fewer than expected records, banner shows `Loaded 412 / 4400 records — filters apply to loaded set only` and summary footnotes `based on partial dataset`.

### 1.5 Stable multi-key sorting

Sort state is an **ordered array** of keys, each with `dir: 'asc' | 'desc'`.

```text
sort: [
  { key: 'spectralCentroid', dir: 'desc' },
  { key: 'dudeneyGroup', dir: 'asc' },
  { key: 'recordId', dir: 'asc' }   // implicit tie-breaker when recordId not already listed
]
```

**Stability rule:** JavaScript `Array.prototype.sort` is stable in all target browsers; comparator returns 0 only when all keys equal.

**`recordId` behavior:**

- If the sort array **already includes** `recordId` (asc **or** desc), that entry is a **complete unique ordering** — do **not** append another `recordId` key.
- Otherwise, **append** `{ key: 'recordId', dir: 'asc' }` as deterministic final tie-breaker.

**UI:** Explicit `recordId` column sorts serialize to URL as `sort=recordId:asc` or `sort=recordId:desc` only; implicit tie-breaker is applied at runtime but omitted from the hash unless the user explicitly sorted by ID.

**Comparator nulls:** Missing numeric fields sort **after** present values in `asc`, **before** present values in `desc` (tested in `acceptance-tests.js`).

### 1.6 Selection model

| Concept | Cardinality | Persistence |
|---------|-------------|-------------|
| **Focus** | one row/card in results | session only (not URL) |
| **Primary selection** (`sel`) | one `recordId` | URL + `sessionStorage` fallback |
| **Compare set** (`compare`) | 0–4 `recordId`s | URL; primary may be member |

**Interactions:**

- **Inspect** button or row click → sets `sel`, opens inspect panel, does not add to compare.
- Compare checkbox → toggles membership in `compare` (max 4); checking 5th shows inline error and ignores.
- Shift+click row → range select compare slots between last compare anchor and clicked row (within filtered list only).
- Cmd/Ctrl+click → toggle compare without changing primary.
- Double-click row → set `sel` and scroll to inspect.

**Focus restoration:**

- After filter/sort change: if `sel` still visible, keep; else clear `sel` and move focus to results status (`aria-live`).
- After closing mobile filter drawer: return focus to trigger button.
- After compare removal: focus moves to removed row’s successor or previous.

### 1.7 Summary panel (filtered aggregates)

Recompute on every filter/sort change (sort does not affect aggregates; only filter does).

| Stat | Formula |
|------|---------|
| Visible count | `filtered.length` |
| Magic count | `filtered.filter(r => r.isMagic).length` |
| Mean interaction E | arithmetic mean |
| Mean spectral centroid | arithmetic mean |
| Mean line defect | arithmetic mean |
| Dudeney distribution | histogram 1–12 with % |
| Cohort breakdown | counts per cohort |
| Class breakdown | count per tag (record may increment multiple) |

Empty filtered set: all stats show `—` and distribution bars hidden.

### 1.8 Comparison view

Activated when `compare.length >= 2`.

**Layout:**

- Desktop: 2-column grid for 2 records; 2×2 for 3–4.
- Each cell: mini 4×4 diagram (read-only, still keyboard-focusable), key metrics table, sparkline degree bars.
- Diff row: highlight metrics where |Δ| > threshold (default 5% of max across compared).

**Keyboard:** Tab order goes compare cell 1 diagram → cell 2 diagram → … → back to results.

### 1.9 URL / state persistence & shareable deep links

**Strategy:** Hash-first for `file://` compatibility; query string mirror when served over HTTP (optional enhancement reading both, writing hash).

**Canonical hash format:**

```text
#/browse?cohort=magic,swap-1&group=6,12&class=ordinary&magic=1&sort=spectralCentroid:desc,dudeneyGroup:asc&sel=M042&compare=M042,M128
```

| Param | Encoding |
|-------|----------|
| `cohort` | comma-separated |
| `group` | comma-separated ints |
| `class` | comma-separated slugs |
| `magic` | `1` or `0` |
| `q` | URI-encoded search prefix |
| `sort` | `key:dir` pairs comma-separated |
| `sel` | single `recordId` |
| `compare` | comma-separated `recordId`s (max 4) |
| `view` | `table` \| `cards` |
| `range` | Compact numeric ranges (see §1.10) |

**UI affordances:**

- Click column header: toggle that key as **primary** (shift preserves secondary keys).
- Shift+click header: add/toggle key as **next** secondary sort.
- Sort chip row shows active keys in order; `×` removes a key; drag reorders (optional v2; v1: remove + re-add).
- Card view: same sort dropdown + “Advanced sort” disclosure listing secondary keys.

### 1.10 Numeric range URL encoding

Allowed range keys (validated on decode): `sourceId`, `swaps`, `dudeneyGroup`, `spectralCentroid`, `interactionEnergy`, `lineDefectEnergy`, `lowOrderEnergy`, `highOrderEnergy`.

**Param:** `range` — comma-separated segments, **keys sorted alphabetically** for deterministic serialization.

**Segment format:** `{key}:{min}~{max}` where omitted bound is empty:

```text
range=interactionEnergy:300~,spectralCentroid:3.4~4.0,lineDefectEnergy:~100
```

| Segment | Meaning |
|---------|---------|
| `spectralCentroid:3.4~4.0` | 3.4 ≤ value ≤ 4.0 |
| `interactionEnergy:300~` | value ≥ 300 |
| `lineDefectEnergy:~100` | value ≤ 100 |

Unknown keys in `range` are **silently dropped** on hydrate. Invalid numbers are ignored per bound.

**Sync rules:**

- `popstate` / `hashchange` → rehydrate app state, re-run pipeline, restore scroll if `sel` present.
- Any user change debounced 150ms → `history.replaceState` (avoid cluttering back stack).
- Invalid `sel` / `compare` IDs silently dropped; if all invalid, show empty inspect/compare with message.

**Share:** Copy-link button serializes current hash to clipboard; toast confirms.

**sessionStorage key:** `mm-explorer-state-v1` stores last hash when user navigates away without hash (progressive enhancement).

---

## 2. UI states

### 2.1 State machine (data layer)

```text
idle → loading → ready
         ↓           ↓
       error      partial (ready + banner)
```

| State | User-visible | Results | Inspect |
|-------|--------------|---------|---------|
| **initial / idle** | “Load dataset to begin” | hidden | hidden |
| **loading** | Skeleton rows + `aria-busy="true"` | disabled controls | disabled |
| **ready** | Full UI | live | live |
| **empty filter** | “No records match filters” + reset CTA | empty illustration | prior sel cleared if not in empty set |
| **error** | Error banner with retry | last good data if any, else empty | frozen |
| **partial** | Warning banner | filters on loaded subset | live |

### 2.2 Responsive layout

| Breakpoint | Layout |
|------------|--------|
| ≥ 1024px | CSS Grid: filters 280px column; results + inspect split 1fr / 360px |
| 768–1023px | Filters collapsible top; inspect below results |
| < 768px | Single column; sticky filter FAB; results cards default; inspect in tab |

**Touch:** 44×44px minimum targets; compare checkboxes enlarged; swipe on card optional (not v1).

### 2.3 Mobile controls

- Filter drawer: full-screen `<dialog>` or `role="dialog"` with focus trap; Esc closes.
- Bottom tab bar: Results | Inspect | Compare | Filters (badge = active filter count).
- Sort: native `<select>` primary + “More sorts” sheet.

### 2.4 Progressive enhancement & local-file constraints

| Feature | file:// | http:// |
|---------|---------|---------|
| Hash URL state | ✓ | ✓ |
| `fetch('analysis.json')` | ✗ (CORS) | ✓ |
| Embedded `embedded-data.js` | ✓ | ✓ |
| Clipboard copy link | may need fallback `prompt()` | ✓ |

**Load order:** try `fetch`; on failure show “Using embedded sample” or prompt file picker (`<input type="file">`) for user-supplied JSON.

**No service worker** in v1 (breaks file:// expectations).

### 2.5 Reduced motion

`prefers-reduced-motion: reduce` disables skeleton shimmer, bar grow animations, and smooth scroll.

---

## 3. Keyboard map (global)

| Key | Context | Action |
|-----|---------|--------|
| `/` | body | Focus search |
| `f` | body | Open filters |
| `?` | body | Open shortcuts help |
| `↑/↓` | results table | Move row focus |
| `Enter` | focused row | Set primary `sel` |
| `Space` | focused row | Toggle compare |
| `Esc` | dialog / diagram | Close / clear cell selection |
| Arrow keys | 4×4 diagram | Move cell focus (roving tabindex) |
| `Home`/`End` | diagram row | First/last column |

---

## 4. Acceptance criteria (UX)

- [ ] Combined filters use AND-across-dimension semantics with documented OR within cohort/group/class.
- [ ] Multi-key sort is stable; `recordId` asc appended only when not explicitly present.
- [ ] URL hash round-trips filter, sort, range, sel, compare, and view fields.
- [ ] Loading, empty, error, and partial states each have distinct banner + `aria-live` messaging.
- [ ] 4×4 diagram is fully operable without pointer; see `diagram-energy-semantics.md`.
- [ ] Moment-energy SVG has titled/described semantics + collapsible numeric table.
- [ ] Mobile filter drawer restores focus to trigger on close.
- [ ] Compare enforces max 4 with user-visible feedback.

---

*End of UX interaction specification.*
