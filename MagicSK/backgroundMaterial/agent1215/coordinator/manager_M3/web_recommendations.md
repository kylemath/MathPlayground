# Draft Web Recommendations — Magic Moment Explorer

**Owner:** 1215-M3  
**Status:** Proposed integration baseline  
**Date:** 2026-07-09  
**Constraints:** Separate HTML/CSS/JavaScript, zero runtime dependencies, 880 primary records, accessible static delivery

## 1. Recommended product boundary

Ship one static explorer for the 880 canonical magic-square records. Include aggregate statistics for random and 1/2/3-swap controls in the primary bundle; load individual control records only from an optional supplemental bundle if a later requirement needs them. This keeps the initial payload small and the mathematical scope understandable.

The primary document should provide:

1. Combined filtering and deterministic multi-key sorting.
2. Filtered-set summaries.
3. Single-record inspection with an interactive 4×4 square.
4. Comparison of two to four records.
5. Moment-energy graphics with complete numeric alternatives.
6. Explicit loading, ready, partial, empty, and error states.
7. Provenance, schema version, and reproducibility information.

## 2. Static application structure

Recommended production files:

```text
index.html
styles.css
app.js
data-loader.js
state-model.js
diagram.js
energy-viz.js
data/magic-moment-v1.json
data/embedded-data.js        # optional file:// fallback
```

- `index.html` owns semantic landmarks and no application data.
- `styles.css` owns responsive layout, focus styling, contrast, and reduced-motion behavior.
- `data-loader.js` validates bundle kind/version before exposing records.
- `state-model.js` contains pure filter, sort, summary, selection, and URL codecs.
- `diagram.js` and `energy-viz.js` are isolated rendering modules.
- `app.js` binds controls to state and renders only the visible result window.

Use classic deferred scripts or small IIFEs for maximum `file://` compatibility. ES modules are reasonable under HTTP, but local module behavior and CORS differ across browsers.

## 3. Data contract

### 3.1 Versioning

Adopt a top-level envelope with:

- `meta.schemaVersion`: semantic version, initially `1.0.0`.
- `meta.bundleKind`: `magic-moment`.
- `meta.recordLayout.fields`: authoritative tuple-slot names.
- `records`: exactly 880 primary tuples.
- `controlAggregates`: named aggregate cohorts.

Reject unknown major versions with a user-facing error. Minor versions may add metadata or trailing tuple slots only when old readers can safely ignore them. Never infer tuple layout from array length alone.

### 3.2 Compact record

The measured prototype uses this fixed tuple:

```text
[id, cells, dudeneyGroup, groupOrientation, complementPair,
 complementId, classFlags, coefficients, energySummary]
```

- `id`: stable source ID, never the current array index.
- `cells`: 16 row-major integers.
- `dudeneyGroup`: integer 1–12.
- `groupOrientation`, `complementPair`, `complementId`: source structural metadata.
- `classFlags`: provisional classification bitset.
- `coefficients`: 15 non-DC coefficients in `meta.modes` order.
- `energySummary`: `[axial, interaction, lowOrder, highOrder, spectralCentroid]`.

The UI should normalize tuples lazily and index them once with `Map(id → tuple)`.

### 3.3 Required metadata

Include:

- Order, magic sum, record count, oriented-union count, and row-major convention.
- Stable-ID policy and tuple layout.
- Complete mode labels and explicit `p = x/column`, `q = y/row` convention.
- Basis identifier, coordinate vector, normalization identifier, coefficient precision, and energy-summary field names.
- Classification registry with labels, predicates/version, and mutual-exclusion rules.
- Source artifact name, actual SHA-256, pipeline/version, generation time, and license/source URL when known.
- Control RNG name/version, seed, replicate count, pair-sampling policy, across-k design, and summary fields.

Do not freeze the provisional classification bits or energy labels until M1 and M2 reconcile their definitions. In particular:

- M1 must distinguish source `complement_pair` metadata from `complement_id`, settle sentinel semantics, and finalize panmagic/associative/most-perfect predicates.
- M2 must publish one basis/normalization contract. Current sibling drafts disagree on normalization in at least one control artifact, so `basisVersion` and `normalization` must be explicit and tested.
- Store enough coefficient precision for the agreed Parseval tolerance. Four-decimal coefficients are good for display but may be insufficient for client-side identity checks.

### 3.4 Controls

For each `random`, `swap-1`, `swap-2`, and `swap-3` aggregate, store count plus metric summaries such as mean, standard deviation, and selected quantiles. Keep protocol metadata adjacent to the aggregates. If individual controls become inspectable, place them in a separately versioned lazy-loaded bundle rather than expanding the primary 880-record payload.

## 4. Loading and browser feasibility

Preferred HTTP path:

1. Fetch the compact JSON.
2. Check HTTP status and parse JSON once.
3. Validate bundle kind, major version, record count, tuple widths, IDs, and 16-cell shape.
4. Build the ID index and render.

For `file://`, relative `fetch()` is commonly blocked. Support either:

- an embedded `window.__DATA__` fallback generated from the same source and checksum, or
- a labeled `<input type="file" accept=".json,application/json">` using `FileReader`.

Recommend local HTTP for development and reproducible testing:

```bash
python3 -m http.server
```

Observed compact-bundle feasibility:

- 880 records: 152,039 bytes JSON; 32,482 bytes gzip.
- Desktop Node 20 runs observed approximately 0.96–1.17 ms for parse, 0.71–0.79 ms for tuple normalization, and 0.19–0.21 ms for a representative filter/sort/top-10 preparation.
- Full current analysis baseline: 4,391,099 bytes for 4,400 rows.

These results make main-thread processing of 880 records reasonable. They are desktop measurements, not low-end mobile-browser guarantees. Render only visible rows/cards; do not attach thousands of hidden DOM nodes.

## 5. State, filtering, and sorting

Use one canonical state object:

```text
loadStatus
records / expectedCount / error
filters { search, cohorts, groups, classes, classMode, magicOnly, ranges }
sort [{ key, dir }, ...]
view
selection { primary, compare[] }
focusedRecordId
```

Filtering rules:

- AND across filter dimensions.
- OR within cohort and Dudeney-group selections.
- Class tags default to OR, with an explicit AND mode.
- Numeric ranges are inclusive.
- Text search matches a case-insensitive record-ID prefix or exact source ID.
- Empty active filters mean all loaded primary records.

Sorting rules:

- Preserve an ordered list of sort keys.
- Compare keys in order.
- Missing numeric values sort last ascending and first descending.
- If record ID is not an explicit key, append record ID ascending as the deterministic final tie-breaker.
- If record ID is explicitly sorted, respect its direction; its uniqueness already makes the order total.
- Preserve original index only as a final defensive fallback.

Recompute summaries from the filtered set, not the complete dataset. At minimum show visible count, class/cohort/group counts, magic count, and means for chosen energy metrics. Display em dashes rather than misleading zeros for an empty set.

## 6. Selection, comparison, and URL state

- Primary selection drives the inspection panel and has cardinality one.
- Comparison contains zero to four stable IDs; reject a fifth with visible and announced feedback.
- Filtering may hide a selection. Clear the primary inspection if it is no longer visible; either remove hidden comparison entries or clearly mark them as outside the current result set. Choose one policy and test it.
- Comparison layout: two columns for two records and a 2×2 grid for three or four; use compact read-only square labels to avoid 64 unnecessary tab stops.

Use a hash-first URL so deep links work from both HTTP and `file://`:

```text
#/browse?cohort=magic&group=6,12&class=ordinary
&sort=spectralCentroid:desc,dudeneyGroup:asc
&range=interactionEnergy:0:340&sel=42&compare=42,128&view=cards
```

Whitelist URL keys and sortable/range fields. Clamp comparison length, reject non-finite range values, normalize duplicate IDs, and serialize in a deterministic order. Use debounced `history.replaceState`; listen for `hashchange`. `sessionStorage` may remember a hashless last session but must not override an explicit URL.

## 7. Information architecture and UI states

Reading order:

1. Header: product name, schema/load status, provenance link.
2. Filters.
3. Filtered summary.
4. Results table/card grid.
5. Inspection panel.
6. Comparison panel.
7. Footer: source, checksum, methods, keyboard help.

State behavior:

- **Idle:** prompt to load data when no embedded/fetched payload exists.
- **Loading:** status text, `aria-busy="true"`, disabled dependent controls; motion-free skeleton or plain progress copy.
- **Ready:** active controls and results.
- **Partial:** warning with loaded/expected counts; every summary says it covers the loaded subset.
- **Empty:** “No records match” plus reset-filters action; no fake chart data.
- **Error:** concise cause, retry/file-picker action, and last good data retained only if clearly labeled stale.

On mobile, use a single column. A modal `<dialog>` opened with `showModal()` can hold filters; restore focus to its trigger on close. Keep touch targets at least 44×44 CSS pixels. Prefer native controls over custom select/listbox widgets.

## 8. Accessible 4×4 selected-square diagram

Use a labeled `role="grid"` containing 16 native buttons with `role="gridcell"`, `aria-rowindex`, `aria-colindex`, and labels such as “Row 2, column 3, value 13.” Maintain exactly one `tabindex="0"` cell.

Keyboard contract:

- Arrow keys move one cell without wrapping.
- Home/End move to first/last cell in the row.
- Enter/Space toggles the active cell.
- Escape clears cell selection and keeps focus.

Selection may highlight the active row and column, but use border/shape plus color. Announce selection in one polite atomic live region. Provide visible instructions and an adjacent captioned line-sums table; the grid is not the sole representation. When inspection opens from a result, focus the diagram heading by default, with an explicit “Explore cells” control or documented choice before moving focus into the grid.

## 9. Dependency-free moment-energy visualization

Render SVG with native DOM or escaped templates:

- A 4×4 mode heatmap, with M00 visibly omitted/neutral.
- Degree/retained-energy bars when the finalized M2 definition supplies valid bins.
- `<figure>` and `<figcaption>`.
- Unique `<title>` and `<desc>` IDs per rendered SVG, referenced through `aria-labelledby`.
- Per-mark `<title>` values for pointer inspection.

Do not communicate energy by color alone. Show visible values or labeled bars and always provide:

- an HTML summary list for major energies;
- a captioned numeric table of every coefficient and energy;
- explicit units/normalization and mode ordering.

Avoid animation by default. If transitions are added, disable them under `prefers-reduced-motion: reduce`.

## 10. General accessibility

- Use header, nav, main, section, aside, and footer landmarks with unique accessible names.
- Include a skip link and logical heading hierarchy.
- Keep native labels connected with `for`/`id`; group related filters in `fieldset`/`legend`.
- Provide a visible `:focus-visible` indicator with at least 3:1 contrast against adjacent colors.
- Meet WCAG AA text contrast; validate chart fills and selected states separately.
- Never make hover the only discovery path.
- Announce result-count changes after debouncing, not on every keystroke.
- Preserve predictable focus after filter dialogs, result deletion/hiding, retry, and comparison removal.
- Honor zoom, reflow, forced colors where practical, and reduced motion.

## 11. Verification gate

Automated, dependency-free checks should cover:

1. Required files and separate HTML/CSS/JS references.
2. JavaScript syntax and module/global exports.
3. Bundle major version, tuple widths, unique IDs, 16-cell permutations, actual source checksum, and aggregate shape.
4. Combined filter algebra, numeric ranges, null sorting, deterministic tie-breaks, selection limits, and hash round trips.
5. Semantic landmarks, labels, grid/live-region hooks, SVG title/description, table alternatives, focus-visible CSS, and reduced-motion CSS.
6. HTTP serving of all paths and an explicit `file://` fallback test.
7. Loading, partial, empty, and error rendering contracts.

Current independent evidence:

- S1 schema/feasibility harness validates 880 records with zero reported structural errors.
- S2 state-model acceptance suite exercises filtering, sorting, selection, URL state, and summaries.
- S3 static prototype smoke suite passes 45/45 checks after correcting its shared-server-root test.

Manual release checks remain necessary for VoiceOver/NVDA announcements, full keyboard traversal, browser zoom/reflow, forced colors, and low-end-device responsiveness.

## 12. Integration decisions still required

1. Final M1 classification registry, complement semantics, source/license metadata, and any D4 stabilizer fields.
2. Final M2 basis formula, unweighted/weighted normalization, coefficient precision, energy buckets, zero tolerance, and control protocol.
3. Whether v1 shows only 880 primary records plus control aggregates or permits browsing all 4,400 current analysis rows. The recommended default is the former.
4. Whether filtering removes hidden compare entries or retains them with an “outside filters” badge.

Until these are resolved, label the schema and graphics as provisional and bind every mathematical value to explicit versioned metadata.

---

*Draft completed 2026-07-09 by Manager 1215-M3.*
