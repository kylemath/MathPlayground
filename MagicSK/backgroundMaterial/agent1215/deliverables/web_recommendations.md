# Zero-Dependency Web Application Recommendations

## Architecture

Use a static application with:

- `index.html` for semantic structure
- `styles.css` for responsive presentation
- `app.js` for state, filtering, sorting, selection, and rendering
- small focused modules where useful (`data-loader.js`, `diagram.js`, `energy-viz.js`)
- a versioned generated data bundle

No framework, CDN, npm package, or build step is required for 880 records. A coordinator rerun of the manager prototype passed 45 zero-dependency static and HTTP smoke checks. Its 20-record vertical slice demonstrates the required interactions; actual keyboard and assistive-technology behavior still needs manual browser testing.

## Data bundle

The primary bundle should contain only the 880 canonical magic-square records plus compact control summaries. Individual random/swap grids belong in an optional detailed bundle.

Required metadata:

- `schemaVersion` and `bundleKind`
- generation timestamp and pipeline version
- source URLs/artifact hashes and retrieval date
- stable ID policy and row-major cell order
- D4/canonicalization policy
- coordinate array, basis ID/vectors, normalization, mode order, and energy definitions
- control PRNG, seed derivation, sample counts, swap policy, and orientation policy
- class-tag registry

Required per-record information:

- stable source ID
- 16 cells
- Dudeney group and source orientation metadata
- complement pair metadata and complement partner ID
- structural class tags
- 15 non-DC coefficients in a fixed order
- axial, interaction, degree-bin, low/high, centroid, and cumulative residual summaries needed by filters/charts
- per-square aggregate controls if selected-square comparisons are supported

Tuple records are appropriate after the layout is frozen. A provisional M3 bundle measured approximately 152 KB uncompressed and 32 KB gzip for 880 records, with desktop Node parse/normalize/filter work under a few milliseconds. Those numbers establish feasibility, not a mobile-browser benchmark.

Recommended corrections to the provisional schema:

- use at least eight decimal digits for coefficients if client Parseval checks are shown
- embed basis vectors or a complete regeneration formula, not only a name
- call only the nine `p,q>0` modes interaction modes
- version the class registry; a string table plus integer tag indices is more extensible than four hard-coded bits
- derive “ordinary” from the absence of displayed special tags
- represent unavailable statistics as `null`, never ambiguous zero

## Application state and interactions

Maintain a single state object containing:

- query text
- selected Dudeney groups and structural tags
- numeric energy ranges
- magic/control cohort, if detailed controls are loaded
- sort key and direction
- selected record ID
- comparison IDs
- active energy cutoff/denominator

Filtering must combine criteria with documented AND/OR semantics. Sorting must be stable with source ID as the final tie-breaker. Keep the selected ID stable across filtering when possible; if hidden, clearly say so and offer “show selected.”

Use URL query/hash parameters for shareable state after the schema is stable. Parse parameters defensively and ignore unsupported values with a visible notice.

Required states:

- loading
- loaded
- empty-filter result
- invalid/unsupported data version
- network/data error with retry
- selected record unavailable

## Page layout

A responsive layout can use:

1. Header with title, short method statement, and data/provenance link.
2. Summary strip: visible/total records, active filters, class counts, and selected energy definition.
3. Filter/sort controls.
4. Record list or compact results table.
5. Selected-square detail with diagram, metadata, line sums, classes, and complement link.
6. Moment-energy panel with degree bars, mode view, and control intervals.
7. Optional two-record comparison panel.
8. Reproducibility/method section.

On narrow screens, stack filters, results, and detail. Keep the selected-square diagram near the top of detail and avoid horizontal page overflow. Tables may scroll within labeled containers.

## Selected-square diagram

Render the 4×4 square as semantic HTML:

- container `role="grid"` with an accessible label naming the square
- four row containers and 16 `role="gridcell"` cells
- announce row, column, and value
- roving `tabindex`: one cell in the grid tab order
- Arrow keys move by cell, Home/End move within a row, and documented modifiers may move to first/last cell
- Enter/Space selects/highlights; Escape clears
- visible `:focus-visible` indicator not conveyed by color alone

Expose row, column, and diagonal sums in a real text table adjacent to the diagram. If hover/focus highlights a line or mode, provide the same relation in text and keyboard behavior. Keep complement and D4 orientation controls outside the grid’s arrow-key navigation.

## Moment-energy visualization

Use dependency-free SVG or styled HTML:

- degree bar chart for `d=2..6`
- optional 3×3 interaction-mode heatmap for `p,q=1..3`
- separate axial-energy indicator for controls
- cutoff selector for `H_all(D)` versus `H_interaction(D)`
- magic/control mean and percentile interval overlays

Every SVG needs a `<title>` and `<desc>`, but those are not sufficient alone. Provide a collapsible numeric table with mode ID, horizontal degree, vertical degree, coefficient, energy, and fraction. Use a perceptually ordered color scale and show numeric values; do not rely on hue alone.

## Filtering and sorting

Useful filters:

- source ID/text search
- Dudeney group
- pandiagonal, associative, most-perfect, compact-2×2, self-complementary
- complement partner/self-complement
- axial, interaction, low/high, spectral centroid, or cumulative residual ranges

Useful sorts:

- source ID
- Dudeney group then ID
- high-interaction share
- spectral centroid
- selected cutoff residual
- distance from a chosen control mean

Label orientation-sensitive moment values as canonical-orientation values. If orbit-averaged statistics are added, make them separate sort keys.

## Accessibility

- Semantic landmarks, one `h1`, logical heading levels, and a skip link.
- Every form control has a persistent visible label.
- Announce result-count and selection changes through a restrained `aria-live="polite"` region; do not announce every keystroke unnecessarily.
- Minimum WCAG AA contrast, visible focus, and noncolor encodings.
- Honor `prefers-reduced-motion`; animation is optional and must not carry unique information.
- Preserve browser zoom and touch targets.
- Ensure comparison controls and chart cutoffs are keyboard operable.
- Test VoiceOver/Safari and at least one Chromium screen reader path.

Static source checks can verify hooks such as labels, roles, and CSS media queries. They cannot prove focus order, spoken output, contrast in all states, or full keyboard behavior.

## Local files and HTTP

`fetch()` of sibling JSON commonly fails under `file://`. Prefer serving locally:

`python3 -m http.server`

For double-click/offline use, either:

- ship an embedded `analysis-data.js` assigning the same versioned payload, or
- provide a file input that reads JSON with `FileReader`.

Do not maintain hand-edited JSON and embedded JavaScript copies. Generate both from one source and test that their content hashes match.

## Verification plan

Automated zero-dependency checks:

- required files and references exist
- JavaScript syntax/module imports succeed
- schema version and all 880 record shapes validate
- IDs are unique and cells are permutations
- coefficient/mode lengths match metadata
- no NaN/infinite numeric fields
- JSON and embedded bundle agree
- local HTTP load succeeds
- filter composition and stable-sort tie cases
- selected/complement links resolve
- chart/table totals agree within tolerance

Manual browser checks:

- keyboard-only traversal and grid navigation
- focus remains visible after filtering/re-render
- loading, empty, and error states
- responsive behavior at 320 CSS px and 200% zoom
- VoiceOver announcements
- reduced motion and high contrast
- Safari/Firefox/Chromium loading

Treat the M3 prototype under `coordinator/manager_M3/sub_S3/prototype` as an interaction reference, not production code. The coordinator's Node smoke rerun was 45 passed, 0 failed.
