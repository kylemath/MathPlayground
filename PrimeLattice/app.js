/*
 * app.js — UI wiring for the Prime Lattice Explorer.
 *
 * Owns the list of layer "definitions" (each one is a recipe pointing at a
 * Lattice generator with knobs), keeps the renderer's layer array in sync,
 * and reacts to control changes. Heavy regenerations are debounced so
 * dragging a slider doesn't sieve 10⁷ integers per frame.
 */

(function () {
  const canvas = document.getElementById('view');
  const renderer = new Renderer(canvas);

  /* ── state ─────────────────────────────────────────────────────────── */

  const state = {
    nExp: 5.0,
    L: 101,
    // Default to stacked 2D Ulam: each Z-slab is a genuine 2D Ulam spiral,
    // so the Z-slice tool (also on by default) shows clean prime diagonals.
    mapping: 'stackedUlam',  // 'ulamSnake' | 'cubicShell' | 'raster' | 'stackedUlam'
    layers: defaultLayers(),
  };

  const MAPPING_HINTS = {
    ulamSnake:
      'Continuous 3D Ulam snake: a true Hamiltonian path winding outward ' +
      'from the origin — every consecutive pair of integers is one ' +
      'Chebyshev step apart (verified), the 3D analogue of the classic ' +
      'Ulam spiral. This is the mapping where prime polynomial spokes appear.',
    cubicShell:
      'Cubic shells: n=0 sits at the cube centre, then each successive ' +
      'integer fills the next cell of the smallest enclosing cubic shell ' +
      '— the 3D generalisation of the 2D Ulam spiral.',
    stackedUlam:
      'Stacked 2D Ulam: each Z-slab is a classical 2D Ulam spiral with ' +
      'n=0 at the slab centre; slabs stack along Z in increasing order. ' +
      'Slice the cube along Z to see the original Ulam diagonals.',
    raster:
      'Row-major: n = (n mod L, ⌊n/L⌋ mod L, ⌊n/L²⌋), starting at the ' +
      'corner. Diagonals you see in orthographic come from L mod p ≠ 0 ' +
      'for small primes p — a Chinese-Remainder artefact, not Ulam.',
  };

  function defaultLayers() {
    return [
      {
        id: 'primes',
        name: 'Primes',
        gen: 'primes',
        color: '#d29922',
        alpha: 1.0,
        visible: true,
        params: {},
      },
      {
        id: 'every-100',
        name: 'Every 100th integer',
        gen: 'everyKth',
        color: '#58a6ff',
        alpha: 0.75,
        visible: false,
        params: { k: 100 },
      },
      {
        id: 'every-7',
        name: 'Every 7th integer',
        gen: 'everyKth',
        color: '#3fb950',
        alpha: 0.55,
        visible: false,
        params: { k: 7 },
      },
      {
        id: 'arith',
        name: 'Arithmetic progression a + dk',
        gen: 'arithmeticProgression',
        color: '#bc8cff',
        alpha: 0.7,
        visible: false,
        params: { a: 1, d: 30 },
      },
      {
        id: 'random-int',
        name: 'Random integers (density p)',
        gen: 'randomUniformIntegers',
        color: '#e6edf3',
        alpha: 0.55,
        visible: false,
        params: { density: 0.12, seed: 1 },
      },
      {
        id: 'random-cont',
        name: 'Random continuous (uniform cube)',
        gen: 'randomContinuous',
        color: '#ff7b72',
        alpha: 0.55,
        visible: false,
        params: { density: 0.12, seed: 2 },
      },
      {
        id: 'gauss',
        name: 'Gaussian cloud (σ)',
        gen: 'randomGaussian',
        color: '#79c0ff',
        alpha: 0.55,
        visible: false,
        params: { density: 0.12, sigma: 0.18, seed: 3 },
      },
      {
        id: 'quasi',
        name: 'Quasi-periodic R3 (irrational stride)',
        gen: 'quasiperiodic',
        color: '#56d4dd',
        alpha: 0.65,
        visible: false,
        params: { density: 0.12, seed: 4 },
      },
      {
        id: 'composites',
        name: 'Composites (¬prime)',
        gen: 'composites',
        color: '#8b949e',
        alpha: 0.4,
        visible: false,
        params: {},
      },
    ];
  }

  /* ── per-layer parameter schemas ──────────────────────────────────── */

  // Describes what extra knobs each generator exposes in the UI. Each entry:
  //   { key, label, type: 'int'|'float', min, max, step, default }
  const PARAM_SCHEMAS = {
    primes: [],
    composites: [],
    everyKth: [
      { key: 'k', label: 'k', type: 'int', min: 1, max: 1000, step: 1, default: 10 },
    ],
    arithmeticProgression: [
      { key: 'a', label: 'a', type: 'int', min: 0, max: 1000, step: 1, default: 1 },
      { key: 'd', label: 'd', type: 'int', min: 1, max: 1000, step: 1, default: 10 },
    ],
    randomUniformIntegers: [
      { key: 'density', label: 'p', type: 'float', min: 0.0005, max: 1, step: 0.001, default: 0.1 },
      { key: 'seed', label: 'seed', type: 'int', min: 1, max: 9999, step: 1, default: 1 },
    ],
    randomContinuous: [
      { key: 'density', label: 'fill', type: 'float', min: 0.0005, max: 1, step: 0.001, default: 0.1 },
      { key: 'seed', label: 'seed', type: 'int', min: 1, max: 9999, step: 1, default: 2 },
    ],
    randomGaussian: [
      { key: 'density', label: 'fill', type: 'float', min: 0.0005, max: 1, step: 0.001, default: 0.1 },
      { key: 'sigma', label: 'σ', type: 'float', min: 0.02, max: 0.5, step: 0.01, default: 0.18 },
      { key: 'seed', label: 'seed', type: 'int', min: 1, max: 9999, step: 1, default: 3 },
    ],
    quasiperiodic: [
      { key: 'density', label: 'fill', type: 'float', min: 0.0005, max: 1, step: 0.001, default: 0.1 },
      { key: 'seed', label: 'seed', type: 'int', min: 1, max: 9999, step: 1, default: 4 },
    ],
  };

  /* ── DOM refs ─────────────────────────────────────────────────────── */

  const el = {
    nCount: document.getElementById('lbl-n-count'),
    nExp: document.getElementById('lbl-n-exp'),
    L: document.getElementById('lbl-L'),
    Lcube: document.getElementById('lbl-Lcube'),
    ctlN: document.getElementById('ctl-n'),
    ctlL: document.getElementById('ctl-L'),
    ctlMapping: document.getElementById('ctl-mapping'),
    mappingHint: document.getElementById('mapping-hint'),
    btnFitL: document.getElementById('btn-fit-L'),

    layerList: document.getElementById('layer-list'),
    legend: document.getElementById('legend'),

    fov: document.getElementById('lbl-fov'),
    zoom: document.getElementById('lbl-zoom'),
    dist: document.getElementById('lbl-dist'),
    rowFov: document.getElementById('row-fov'),
    ctlFov: document.getElementById('ctl-fov'),
    ctlZoom: document.getElementById('ctl-zoom'),
    ctlDist: document.getElementById('ctl-dist'),
    ctlAutorot: document.getElementById('ctl-autorot'),
    ctlDepthfade: document.getElementById('ctl-depthfade'),
    btnResetCam: document.getElementById('btn-reset-cam'),

    sliceOn: document.getElementById('ctl-slice-on'),
    sliceGrad: document.getElementById('ctl-slice-grad'),
    sliceLines: document.getElementById('ctl-slice-lines'),
    sliceLinesOnly: document.getElementById('ctl-slice-lines-only'),
    sliceIdx: document.getElementById('ctl-slice-idx'),
    sliceThick: document.getElementById('ctl-slice-thick'),
    lineMin: document.getElementById('ctl-line-min'),
    lineGap: document.getElementById('ctl-line-gap'),
    lblSliceIdx: document.getElementById('lbl-slice-idx'),
    lblSliceMax: document.getElementById('lbl-slice-max'),
    lblSliceThick: document.getElementById('lbl-slice-thick'),
    lblLineMin: document.getElementById('lbl-line-min'),
    lblLineGap: document.getElementById('lbl-line-gap'),

    dot: document.getElementById('lbl-dot'),
    alpha: document.getElementById('lbl-alpha'),
    ctlDot: document.getElementById('ctl-dot'),
    ctlAlpha: document.getElementById('ctl-alpha'),
    ctlShowBox: document.getElementById('ctl-showbox'),
    ctlShowAxes: document.getElementById('ctl-showaxes'),

    hudMode: document.getElementById('hud-mode'),
    hudCount: document.getElementById('hud-count'),
    hudFps: document.getElementById('hud-fps'),
  };

  /* ── debounced regeneration ───────────────────────────────────────── */

  const _regenTimers = new Map();
  const _generatedCache = new Map();
  function scheduleRegen(layer, debounceMs = 30) {
    if (_regenTimers.has(layer.id)) clearTimeout(_regenTimers.get(layer.id));
    _regenTimers.set(layer.id, setTimeout(() => regenLayer(layer), debounceMs));
  }

  function regenAll() {
    for (const layer of state.layers) scheduleRegen(layer, 10);
  }

  function regenLayer(layer) {
    const nMax = currentNMax();
    const L = state.L;
    const mapping = state.mapping;
    const fnName = layer.gen;
    const fn = Lattice[fnName];
    if (!fn) return;

    const key = `${layer.id}|${fnName}|${mapping}|${nMax}|${L}|${JSON.stringify(layer.params)}`;
    let result = _generatedCache.get(key);
    if (!result) {
      try {
        result = fn({ nMax, L, mapping, ...layer.params });
      } catch (err) {
        console.warn('layer gen failed', layer.id, err);
        return;
      }
      _generatedCache.set(key, result);
      // Cheap cache eviction.
      if (_generatedCache.size > 32) {
        const firstKey = _generatedCache.keys().next().value;
        _generatedCache.delete(firstKey);
      }
    }
    layer._result = result;
    pushLayersToRenderer();
    updateLayerCounts();
    updateLegend();
  }

  function pushLayersToRenderer() {
    renderer.setLayers(
      state.layers
        .filter((l) => l._result && l.visible)
        .map((l) => ({
          id: l.id,
          name: l.name,
          color: l.color,
          alpha: l.alpha,
          positions: l._result.positions,
          count: l._result.count,
          visible: true,
        })),
    );
  }

  /* ── current N from log10 slider ──────────────────────────────────── */

  function currentNMax() {
    const raw = Math.round(Math.pow(10, state.nExp));
    return Math.max(2, Math.min(raw, 1e7));  // hard cap for memory
  }

  function currentCapacity() {
    const mapping = Lattice.Mappings[state.mapping] || Lattice.Mappings.raster;
    return mapping.capacity(state.L);
  }

  function refreshNumberLabels() {
    el.nExp.textContent = state.nExp.toFixed(1);
    el.nCount.textContent = currentNMax().toLocaleString();
    el.L.textContent = state.L.toString();
    el.Lcube.textContent = currentCapacity().toLocaleString();
  }

  /* ── layer list rendering ─────────────────────────────────────────── */

  function renderLayerList() {
    el.layerList.innerHTML = '';
    for (const layer of state.layers) {
      const li = document.createElement('li');
      li.className = 'layer';
      const head = document.createElement('div');
      head.className = 'layer-head';

      const sw = document.createElement('span');
      sw.className = 'layer-swatch';
      sw.style.background = layer.color;

      const tog = document.createElement('input');
      tog.type = 'checkbox';
      tog.className = 'layer-toggle';
      tog.checked = layer.visible;
      tog.addEventListener('click', (e) => e.stopPropagation());
      tog.addEventListener('change', () => {
        layer.visible = tog.checked;
        if (layer.visible && !layer._result) {
          regenLayer(layer);
        } else {
          pushLayersToRenderer();
          updateLegend();
        }
        renderer._needsRedraw = true;
      });

      const title = document.createElement('span');
      title.className = 'layer-title';
      title.textContent = layer.name;

      const count = document.createElement('span');
      count.className = 'layer-count';
      count.textContent = '—';
      layer._countEl = count;

      head.appendChild(sw);
      head.appendChild(tog);
      head.appendChild(title);
      head.appendChild(count);
      li.appendChild(head);

      const body = document.createElement('div');
      body.className = 'layer-body';

      // Color picker
      const colorField = makeField('color', (input) => {
        input.type = 'color';
        input.value = layer.color;
        input.addEventListener('input', () => {
          layer.color = input.value;
          sw.style.background = input.value;
          pushLayersToRenderer();
          updateLegend();
          renderer._needsRedraw = true;
        });
      });
      body.appendChild(colorField);

      // Alpha
      const alphaField = makeRangeField('alpha', layer.alpha, 0.05, 1, 0.01, (v) => {
        layer.alpha = v;
        pushLayersToRenderer();
        renderer._needsRedraw = true;
      });
      body.appendChild(alphaField);

      // Per-generator params
      const schema = PARAM_SCHEMAS[layer.gen] || [];
      for (const p of schema) {
        const v = layer.params[p.key];
        const field = makeRangeField(p.label, v, p.min, p.max, p.step, (val) => {
          layer.params[p.key] = (p.type === 'int') ? Math.round(val) : val;
          scheduleRegen(layer, 60);
        });
        body.appendChild(field);
      }

      head.addEventListener('click', (e) => {
        if (e.target === tog) return;
        li.classList.toggle('is-open');
      });

      li.appendChild(body);
      el.layerList.appendChild(li);
    }
  }

  function makeField(label, init) {
    const wrap = document.createElement('div');
    wrap.className = 'layer-field';
    const lab = document.createElement('label');
    lab.textContent = label;
    const input = document.createElement('input');
    init(input);
    wrap.appendChild(lab);
    wrap.appendChild(input);
    return wrap;
  }

  function makeRangeField(label, value, min, max, step, onChange) {
    const wrap = document.createElement('div');
    wrap.className = 'layer-field';
    const lab = document.createElement('label');
    lab.textContent = label;
    const range = document.createElement('input');
    range.type = 'range';
    range.min = min; range.max = max; range.step = step; range.value = value;
    const numStr = document.createElement('span');
    numStr.style.minWidth = '3.5rem';
    numStr.style.textAlign = 'right';
    numStr.style.fontFamily = 'var(--mono)';
    numStr.textContent = formatValue(value, step);
    range.addEventListener('input', () => {
      const v = parseFloat(range.value);
      numStr.textContent = formatValue(v, step);
      onChange(v);
    });
    wrap.appendChild(lab);
    wrap.appendChild(range);
    wrap.appendChild(numStr);
    return wrap;
  }

  function formatValue(v, step) {
    if (step >= 1) return Math.round(v).toString();
    if (step >= 0.1) return v.toFixed(1);
    if (step >= 0.01) return v.toFixed(2);
    return v.toFixed(3);
  }

  function updateLayerCounts() {
    for (const layer of state.layers) {
      if (layer._countEl) {
        layer._countEl.textContent = layer._result
          ? layer._result.count.toLocaleString()
          : '—';
      }
    }
  }

  function updateLegend() {
    el.legend.innerHTML = '';
    const visible = state.layers.filter((l) => l.visible && l._result);
    if (!visible.length) {
      el.legend.style.display = 'none';
      return;
    }
    el.legend.style.display = 'flex';
    for (const layer of visible) {
      const row = document.createElement('div');
      row.className = 'legend-row';
      const sw = document.createElement('span');
      sw.className = 'legend-swatch';
      sw.style.background = layer.color;
      const txt = document.createElement('span');
      txt.textContent = `${layer.name} · ${layer._result.count.toLocaleString()}`;
      row.appendChild(sw);
      row.appendChild(txt);
      el.legend.appendChild(row);
    }
  }

  /* ── control wiring ───────────────────────────────────────────────── */

  el.ctlN.addEventListener('input', () => {
    state.nExp = parseFloat(el.ctlN.value);
    refreshNumberLabels();
    debounceGlobalRegen();
  });

  el.ctlL.addEventListener('input', () => {
    state.L = parseInt(el.ctlL.value, 10);
    refreshNumberLabels();
    refreshSliceRange();
    debounceGlobalRegen();
  });

  el.btnFitL.addEventListener('click', () => {
    const nMax = currentNMax();
    // For cubic shells we want an odd L so the cube is centred (L = 2K+1).
    // For other mappings we just round to nearest odd to keep both behaviours
    // consistent with the slider's step=2.
    let L = Math.round(Math.cbrt(nMax));
    if (L % 2 === 0) L += 1;
    state.L = Math.max(11, Math.min(401, L));
    el.ctlL.value = state.L;
    refreshNumberLabels();
    refreshSliceRange();
    regenAll();
  });

  el.ctlMapping.addEventListener('change', () => {
    state.mapping = el.ctlMapping.value;
    el.mappingHint.textContent = MAPPING_HINTS[state.mapping] || '';
    // Cubic shells are centred on origin; raster fills from a corner. Reset
    // the camera so the first view of a switched mapping is well-framed.
    renderer.resetCamera();
    el.ctlZoom.value = renderer.opts.zoom;
    el.zoom.textContent = `${renderer.opts.zoom.toFixed(2)}×`;
    el.ctlDist.value = renderer.opts.distance;
    el.dist.textContent = renderer.opts.distance.toFixed(2);
    // Invalidate everything cached under the old mapping and rebuild.
    _generatedCache.clear();
    refreshNumberLabels();
    refreshSliceRange();
    regenAll();
  });

  let _globalRegenTimer = null;
  function debounceGlobalRegen() {
    if (_globalRegenTimer) clearTimeout(_globalRegenTimer);
    _globalRegenTimer = setTimeout(() => regenAll(), 80);
  }

  // Projection radios.
  document.querySelectorAll('input[name="proj"]').forEach((r) => {
    r.addEventListener('change', () => {
      const v = document.querySelector('input[name="proj"]:checked').value;
      renderer.setProjection(v);
      el.hudMode.textContent = v[0].toUpperCase() + v.slice(1);
      el.rowFov.style.opacity = (v === 'perspective') ? '1' : '0.35';
      el.rowFov.style.pointerEvents = (v === 'perspective') ? 'auto' : 'none';
    });
  });

  el.ctlFov.addEventListener('input', () => {
    const v = parseFloat(el.ctlFov.value);
    el.fov.textContent = `${v}°`;
    renderer.setOptions({ fovDeg: v });
  });
  el.ctlZoom.addEventListener('input', () => {
    const v = parseFloat(el.ctlZoom.value);
    el.zoom.textContent = `${v.toFixed(2)}×`;
    renderer.setOptions({ zoom: v });
  });
  el.ctlDist.addEventListener('input', () => {
    const v = parseFloat(el.ctlDist.value);
    el.dist.textContent = v.toFixed(2);
    renderer.setOptions({ distance: v });
  });
  el.ctlAutorot.addEventListener('change', () => {
    renderer.setOptions({ autoRotate: el.ctlAutorot.checked });
  });
  el.ctlDepthfade.addEventListener('change', () => {
    renderer.setOptions({ depthFade: el.ctlDepthfade.checked });
  });
  el.btnResetCam.addEventListener('click', () => {
    renderer.resetCamera();
    el.ctlZoom.value = renderer.opts.zoom;
    el.zoom.textContent = `${renderer.opts.zoom.toFixed(2)}×`;
    el.ctlDist.value = renderer.opts.distance;
    el.dist.textContent = renderer.opts.distance.toFixed(2);
  });

  /* ── slice (single Ulam plane) ────────────────────────────────────── */

  // Coordinate model per mapping: snake/shell/stacked place integer cell c
  // at normalised c/L (c ∈ [-K, K], K = ⌊(L-1)/2⌋); raster places cell c at
  // (c+0.5)/L - 0.5 (c ∈ [0, L-1]). The slab slider walks c; thickness is in
  // whole cells, each 1/L wide.
  function sliceAxisInfo() {
    const L = state.L;
    if (state.mapping === 'raster') {
      return { min: 0, max: L - 1, toNorm: (c) => (c + 0.5) / L - 0.5 };
    }
    const K = Math.floor((L - 1) / 2);
    return { min: -K, max: K, toNorm: (c) => c / L };
  }

  function refreshSliceRange() {
    const info = sliceAxisInfo();
    const idx = clampInt(parseInt(el.sliceIdx.value, 10) || 0, info.min, info.max);
    el.sliceIdx.min = info.min;
    el.sliceIdx.max = info.max;
    el.sliceIdx.value = idx;
    el.lblSliceIdx.textContent = idx.toString();
    el.lblSliceMax.textContent = Math.max(Math.abs(info.min), Math.abs(info.max)).toString();
    el.sliceThick.max = state.L;
    pushSlice();
  }

  function pushSlice() {
    const info = sliceAxisInfo();
    const axis = parseInt(document.querySelector('input[name="slice-axis"]:checked').value, 10);
    const idx = clampInt(parseInt(el.sliceIdx.value, 10) || 0, info.min, info.max);
    const thick = parseInt(el.sliceThick.value, 10) || 1;
    const minHits = parseInt(el.lineMin.value, 10) || 5;
    const maxGap = parseInt(el.lineGap.value, 10) || 0;
    renderer.setOptions({
      slice: {
        enabled: el.sliceOn.checked,
        axis,
        center: info.toNorm(idx),
        half: (thick * 0.5) / state.L + 1e-6,
        gradient: el.sliceGrad.checked,
        cellWidth: 1 / state.L,
        lines: {
          enabled: el.sliceLines.checked,
          only: el.sliceLinesOnly.checked,
          minHits,
          maxGap,
        },
      },
    });
  }

  function clampInt(v, lo, hi) { return v < lo ? lo : v > hi ? hi : v; }

  function snapCameraToSliceAxis() {
    const axis = parseInt(document.querySelector('input[name="slice-axis"]:checked').value, 10);
    renderer.setProjection('orthographic');
    const orthoRadio = document.querySelector('input[name="proj"][value="orthographic"]');
    if (orthoRadio && !orthoRadio.checked) {
      orthoRadio.checked = true;
      orthoRadio.dispatchEvent(new Event('change'));
    }
    renderer.setView(['x', 'y', 'z'][axis]);
  }

  // A single Z-slab is only a clean 2D Ulam spiral under the stacked mapping;
  // for the 3D shell/snake mappings it's a tangled cross-section. So when the
  // user opts into a Z-slice, switch them onto the mapping that makes it read.
  function maybeSwitchMappingForZSlice() {
    const axis = parseInt(document.querySelector('input[name="slice-axis"]:checked').value, 10);
    if (axis === 2 && state.mapping !== 'stackedUlam') {
      el.ctlMapping.value = 'stackedUlam';
      el.ctlMapping.dispatchEvent(new Event('change'));
      return true;
    }
    return false;
  }

  el.sliceOn.addEventListener('change', () => {
    if (el.sliceOn.checked) maybeSwitchMappingForZSlice();
    pushSlice();
    if (el.sliceOn.checked) snapCameraToSliceAxis();
  });
  document.querySelectorAll('input[name="slice-axis"]').forEach((r) => {
    r.addEventListener('change', () => {
      if (el.sliceOn.checked) maybeSwitchMappingForZSlice();
      pushSlice();
      if (el.sliceOn.checked) snapCameraToSliceAxis();
    });
  });
  el.sliceIdx.addEventListener('input', () => {
    el.lblSliceIdx.textContent = el.sliceIdx.value;
    pushSlice();
  });
  el.sliceThick.addEventListener('input', () => {
    el.lblSliceThick.textContent = el.sliceThick.value;
    pushSlice();
  });
  el.sliceGrad.addEventListener('change', pushSlice);
  el.sliceLines.addEventListener('change', pushSlice);
  el.sliceLinesOnly.addEventListener('change', pushSlice);
  el.lineMin.addEventListener('input', () => {
    el.lblLineMin.textContent = el.lineMin.value;
    pushSlice();
  });
  el.lineGap.addEventListener('input', () => {
    el.lblLineGap.textContent = el.lineGap.value;
    pushSlice();
  });

  el.ctlDot.addEventListener('input', () => {
    const v = parseFloat(el.ctlDot.value);
    el.dot.textContent = v.toFixed(1);
    renderer.setOptions({ dotSize: v });
  });
  el.ctlAlpha.addEventListener('input', () => {
    const v = parseFloat(el.ctlAlpha.value);
    el.alpha.textContent = v.toFixed(2);
    renderer.setOptions({ alpha: v });
  });
  el.ctlShowBox.addEventListener('change', () => {
    renderer.setOptions({ showBox: el.ctlShowBox.checked });
  });
  el.ctlShowAxes.addEventListener('change', () => {
    renderer.setOptions({ showAxes: el.ctlShowAxes.checked });
  });

  // Axis-align buttons: snap the camera to an exact orthogonal view down
  // X, Y, or Z and force orthographic projection so the plane reads true.
  document.querySelectorAll('.axis-btn').forEach((btn) => {
    btn.addEventListener('click', () => {
      renderer.setProjection('orthographic');
      const orthoRadio = document.querySelector('input[name="proj"][value="orthographic"]');
      if (orthoRadio && !orthoRadio.checked) {
        orthoRadio.checked = true;
        orthoRadio.dispatchEvent(new Event('change'));
      }
      renderer.setView(btn.dataset.axis);
      document.querySelectorAll('.axis-btn').forEach((b) => b.classList.remove('is-active'));
      btn.classList.add('is-active');
    });
  });

  // Any manual orbit clears the "aligned" highlight.
  canvas.addEventListener('pointerdown', () => {
    document.querySelectorAll('.axis-btn.is-active').forEach((b) => b.classList.remove('is-active'));
  });

  // Mouse-wheel zoom reflects back into the slider.
  renderer.onZoomChange((z) => {
    el.ctlZoom.value = z;
    el.zoom.textContent = `${z.toFixed(2)}×`;
  });

  // FPS / count HUD.
  renderer.onStats = ({ visibleCount, fps }) => {
    el.hudCount.textContent = visibleCount.toLocaleString();
    el.hudFps.textContent = fps.toString();
  };

  /* ── boot ─────────────────────────────────────────────────────────── */

  // Initial UI sync.
  el.ctlMapping.value = state.mapping;
  el.mappingHint.textContent = MAPPING_HINTS[state.mapping] || '';
  el.ctlL.value = state.L;
  refreshNumberLabels();
  refreshSliceRange();
  renderLayerList();
  renderer.setOptions({
    fovDeg: 60, zoom: 1.0, distance: 2.5,
    dotSize: 1.6, alpha: 0.85,
    depthFade: true, autoRotate: false,
    showBox: true, showAxes: false,
  });

  // Best starting point for seeing Ulam planes: stacked 2D mapping, Z-slice on,
  // viewed head-on in orthographic. Open on the bottom slab (z_slab 0 = the
  // first ~L² integers), which is the classic dense 2D Ulam spiral — the
  // central slab would be empty whenever N ≪ L³.
  el.sliceOn.checked = true;
  {
    const sinfo = sliceAxisInfo();
    el.sliceIdx.value = (state.mapping === 'stackedUlam') ? sinfo.min : 0;
    el.lblSliceIdx.textContent = el.sliceIdx.value;
  }
  pushSlice();
  snapCameraToSliceAxis();

  regenAll();
  renderer.start();
})();
