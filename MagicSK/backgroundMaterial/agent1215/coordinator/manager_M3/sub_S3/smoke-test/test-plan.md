# Smoke Test Plan — Magic Moment Records Static Prototype

**Agent:** 1215-M3-S3  
**Artifact:** `smoke-test/run-smoke.mjs` (Node built-ins) + `smoke-test/smoke-test.html` (browser runner)  
**Target:** `../prototype/` (HTML/CSS/JS, zero npm dependencies)

---

## Objectives

1. Verify prototype files exist and parse without syntax errors.
2. Assert DOM/accessibility contracts required by the brief.
3. Validate embedded dataset schema and record shape.
4. Compare **local file (`file://`)** vs **HTTP serving** behavior for JSON loading.
5. Record payload size observations for scaling to 880+ records.

---

## Preconditions

- Node.js ≥ 18 (for native `fetch` in smoke runner).
- Modern browser (Safari 16+, Firefox 102+, Chromium 100+) for manual/browser-runner checks.

---

## Automated checks (`run-smoke.mjs`)

| # | Category | Check |
|---|----------|-------|
| 1 | Files | All required prototype files present |
| 2 | HTML | Semantic landmarks, skip link, external CSS/JS only |
| 3 | A11y hooks | `role="grid"`, `aria-live`, `lang="en"`, `#square-diagram`, `#energy-viz` |
| 4 | CSS | `prefers-reduced-motion`, `:focus-visible`, contrast-oriented dark theme |
| 5 | JS exports | `RecordDataLoader`, `SquareDiagram`, `EnergyViz` load in vm sandbox |
| 6 | Schema | `validatePayload` accepts embedded + sample JSON |
| 7 | Records | 20 sample records, each with 16 cells |
| 8 | HTTP | Ephemeral local server; `fetch('/sample-data.json')` succeeds |
| 9 | HTTP sub_S3 root | `/smoke-test/smoke-test.html` and `/prototype/*` sibling assets reachable |
| 10 | HTTP prototype-only | Sibling `smoke-test/` **not** reachable (404) — documents defect if serving wrong root |
| 11 | file:// | Documented fallback via `embedded-data.js` when fetch fails |

### Run command

```bash
node /Users/kylemathewson/MagicSK/backgroundMaterial/agent1215/coordinator/manager_M3/sub_S3/smoke-test/run-smoke.mjs
```

Results are written to `smoke-test/smoke-results.json`.

---

## Browser runner (`smoke-test.html`)

Serve the **`sub_S3` folder root** so both `prototype/` and `smoke-test/` are reachable under one HTTP origin (do **not** serve only `prototype/` — sibling paths like `/../smoke-test/` are blocked by the server):

```bash
cd /Users/kylemathewson/MagicSK/backgroundMaterial/agent1215/coordinator/manager_M3/sub_S3
python3 -m http.server 8765
```

Then open:

- **Browser runner:** http://127.0.0.1:8765/smoke-test/smoke-test.html
- **Full prototype:** http://127.0.0.1:8765/prototype/index.html

`smoke-test.html` loads prototype modules via relative paths (`../prototype/*.js`), which resolve correctly when the page URL is under `/smoke-test/`.

Double-clicking `smoke-test.html` via `file://` still works for module checks, but `loadDataset()` fetch may fall back to embedded data (same as the prototype).

The browser runner validates:
- Embedded dataset available on `window.__EMBEDDED_RECORDS__`.
- Diagram grid renders 16 cells when sample record injected.
- Energy SVG contains `<svg` and `<title>` elements.

---

## Manual accessibility spot checks

| Check | Method | Expected |
|-------|--------|----------|
| Keyboard grid | Tab to diagram, arrow keys | Focus moves across 4×4 cells |
| Selection | Enter on cell | Status text updates, cell highlighted |
| Screen reader labels | VoiceOver/NVDA spot check | Cells announce row/column/value |
| Reduced motion | OS setting ON | No meaningful animation (CSS disables transitions) |
| Contrast | Visual / DevTools | Body text `#e6edf3` on `#0d1117` (~high contrast) |
| Table fallback | Expand energy table details | Numeric mode/degree values present |

---

## Local-file vs HTTP matrix

| Scenario | JSON via fetch | Embedded fallback | Prototype usable |
|----------|----------------|-------------------|------------------|
| `file://` open `prototype/index.html` | Usually **blocked** (browser CORS) | **Yes** (`embedded-data.js`) | Yes (20 records) |
| `http://localhost` serve **`sub_S3/` root** | **Yes** (`/prototype/sample-data.json`) | Also present | Yes; prototype at `/prototype/index.html`, runner at `/smoke-test/smoke-test.html` |
| `http://localhost` serve **`prototype/` only** | **Yes** for prototype | Also present | Prototype yes; **smoke-test sibling not reachable** |
| Missing JSON over HTTP | Fails fetch | Falls back if embedded loaded | Yes with warning in status |

---

## Scaling notes (880 records)

- Reference full dataset: `analysis.json` ≈ 4.4 MiB / 4400 records.
- Prototype sample: ≈ 38 KiB JSON / 20 records.
- Linear extrapolation for 880 magic records only: ~0.8–1.0 MiB JSON — feasible for HTTP fetch; heavy for inline embed on `file://`.
- Recommendation: ship compact bundle + optional lazy fetch for production; keep embedded slice for offline demo.

---

## Exit criteria

- Automated runner exits 0.
- `smoke-results.json` captured with timestamp and payload bytes.
- Manual keyboard diagram check documented in S3 report.
