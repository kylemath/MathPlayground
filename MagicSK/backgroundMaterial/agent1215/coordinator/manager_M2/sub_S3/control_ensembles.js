/**
 * Deterministic control ensembles for 4×4 grids (zero-dependency browser module).
 * PRNG and algorithms match control_ensembles.py byte-for-byte on uint32 paths.
 */

const N_CELLS = 16;
const GRID_SIDE = 4;
const COORDS_1D = [-1.5, -0.5, 0.5, 1.5];
const UINT32_RANGE = 4294967296;

/** Domain-separation tags — must match control_ensembles.py */
export const PERM_DOMAIN = 0x5065524d;
export const SWAP_DOMAIN = 0x53574150;

/** @type {Array<[number, number]>} */
const UNORDERED_PAIRS = [];
for (let i = 0; i < N_CELLS; i += 1) {
  for (let j = i + 1; j < N_CELLS; j += 1) {
    UNORDERED_PAIRS.push([i, j]);
  }
}

function u32(x) {
  return x >>> 0;
}

/**
 * @param {number} state uint32 PRNG state
 * @returns {{ raw: number, state: number }}
 */
export function mulberry32NextU32(state) {
  let s = u32(state + 0x6d2b79f5);
  let t = s;
  t = u32(Math.imul(t ^ (t >>> 15), t | 1));
  t = u32(t ^ u32(t + u32(Math.imul(t ^ (t >>> 7), t | 61))));
  return { raw: u32(t ^ (t >>> 14)), state: s };
}

/**
 * @param {number} state uint32 PRNG state (updated in place via return)
 * @returns {{ u: number, state: number }}
 */
export function mulberry32Next(state) {
  const { raw, state: next } = mulberry32NextU32(state);
  return { u: raw / UINT32_RANGE, state: next };
}

export function seedToState(seed) {
  const s = u32(seed);
  return s !== 0 ? s : 1;
}

export function randBelow(state, n) {
  if (n <= 0) throw new Error("n must be positive");
  const limit = Math.floor(UINT32_RANGE / n) * n;
  while (true) {
    const draw = mulberry32NextU32(state);
    state = draw.state;
    if (draw.raw < limit) {
      return { value: draw.raw % n, state };
    }
  }
}

export function deriveReplicateSeed(baseSeed, squareId, replicate, domain = 0) {
  let x = u32(baseSeed);
  x = u32(x ^ u32(squareId * 0x9e3779b1));
  x = u32(x ^ u32(replicate * 0x85ebca77));
  if (domain) x = u32(x ^ domain);
  return x !== 0 ? x : 1;
}

/**
 * Fisher–Yates shuffle (unbiased uniform random permutation).
 * @param {number[]} values
 * @param {number} state
 */
export function fisherYates(values, state) {
  const arr = values.slice();
  const n = arr.length;
  for (let i = n - 1; i > 0; i -= 1) {
    const draw = randBelow(state, i + 1);
    state = draw.state;
    const j = draw.value;
    const tmp = arr[i];
    arr[i] = arr[j];
    arr[j] = tmp;
  }
  return { arr, state };
}

export function flatToGrid(flat) {
  const grid = [];
  for (let r = 0; r < GRID_SIDE; r += 1) {
    grid.push(flat.slice(r * GRID_SIDE, (r + 1) * GRID_SIDE));
  }
  return grid;
}

export function applySwap(flat, pair) {
  const [a, b] = pair;
  if (a === b) throw new Error("no-op swap forbidden");
  const tmp = flat[a];
  flat[a] = flat[b];
  flat[b] = tmp;
}

/**
 * @param {'uniform_with_replacement'|'distinct_pairs_no_replacement'|'no_immediate_undo'|'distinct_pairs_no_immediate_undo'} mode
 */
function samplePair(state, mode, usedPairs, prevPair) {
  const maxAttempts = 512;
  for (let attempt = 0; attempt < maxAttempts; attempt += 1) {
    const draw = randBelow(state, UNORDERED_PAIRS.length);
    state = draw.state;
    const pair = UNORDERED_PAIRS[draw.value];
    if (
      (mode === "distinct_pairs_no_replacement" ||
        mode === "distinct_pairs_no_immediate_undo") &&
      usedPairs.has(pairKey(pair))
    ) {
      continue;
    }
    if (
      (mode === "no_immediate_undo" ||
        mode === "distinct_pairs_no_immediate_undo") &&
      prevPair &&
      pairKey(pair) === pairKey(prevPair)
    ) {
      continue;
    }
    return { pair, state };
  }
  throw new Error(`failed to sample pair under mode=${mode}`);
}

function pairKey(pair) {
  return `${pair[0]},${pair[1]}`;
}

/**
 * @param {number[]} base
 * @param {number} k
 * @param {number} state
 * @param {{ pairSampling: string, acrossK: string }} protocol
 */
export function sequentialSwaps(base, k, state, protocol) {
  const flat = base.slice();
  /** @type {Array<[number, number]>} */
  const pairs = [];
  const used = new Set();
  let prev = null;
  const mode = protocol.pairSampling;
  for (let step = 0; step < k; step += 1) {
    const sampled = samplePair(state, mode, used, prev);
    state = sampled.state;
    const pair = sampled.pair;
    applySwap(flat, pair);
    pairs.push(pair);
    used.add(pairKey(pair));
    prev = pair;
  }
  return { flat, pairs, state };
}

/**
 * @param {number[]} base
 * @param {number[]} kValues
 * @param {number} state
 * @param {{ pairSampling: string, acrossK: string }} protocol
 */
export function swapEnsembleForKValues(base, kValues, state, protocol) {
  const kmax = Math.max(...kValues);
  /** @type {Record<number, { k: number, pairs: Array<[number, number]>, flat: number[] }>} */
  const traces = {};
  if (protocol.acrossK === "paired_prefix") {
    const flat = base.slice();
    /** @type {Array<[number, number]>} */
    const pairsSoFar = [];
    const used = new Set();
    let prev = null;
    const mode = protocol.pairSampling;
    for (let step = 1; step <= kmax; step += 1) {
      const sampled = samplePair(state, mode, used, prev);
      state = sampled.state;
      const pair = sampled.pair;
      applySwap(flat, pair);
      pairsSoFar.push(pair);
      used.add(pairKey(pair));
      prev = pair;
      if (kValues.includes(step)) {
        traces[step] = {
          k: step,
          pairs: pairsSoFar.slice(),
          flat: flat.slice(),
        };
      }
    }
  } else {
    for (const k of kValues.slice().sort((a, b) => a - b)) {
      const result = sequentialSwaps(base, k, state, protocol);
      state = result.state;
      traces[k] = { k, pairs: result.pairs, flat: result.flat };
    }
  }
  return { traces, state };
}

function gramSchmidt1d(degreeMax) {
  const n = COORDS_1D.length;
  /** @type {number[][]} */
  const basis = [];
  for (let p = 0; p <= degreeMax; p += 1) {
    let v = COORDS_1D.map((x) => x ** p);
    for (const b of basis) {
      let proj = 0;
      for (let i = 0; i < n; i += 1) proj += v[i] * b[i];
      proj /= n;
      v = v.map((val, i) => val - proj * b[i]);
    }
    let norm = 0;
    for (let i = 0; i < n; i += 1) norm += v[i] * v[i];
    norm = Math.sqrt(norm / n);
    basis.push(v.map((val) => val / norm));
  }
  return basis;
}

const PHI_1D = gramSchmidt1d(3);

/** @type {Array<{ p: number, q: number, degree: number, index: number }>} */
const MOMENT_MODES = [];
(function buildModes() {
  let idx = 0;
  for (let degree = 0; degree < 7; degree += 1) {
    for (let p = 0; p < 4; p += 1) {
      const q = degree - p;
      if (q >= 0 && q <= 3) {
        MOMENT_MODES.push({ p, q, degree, index: idx });
        idx += 1;
      }
    }
  }
})();

function evalBasis2d(p, q, row, col) {
  return PHI_1D[p][col] * PHI_1D[q][row];
}

export function momentCoefficients(flat) {
  const grid = flatToGrid(flat);
  return MOMENT_MODES.map((mode) => {
    let acc = 0;
    for (let r = 0; r < GRID_SIDE; r += 1) {
      for (let c = 0; c < GRID_SIDE; c += 1) {
        acc += grid[r][c] * evalBasis2d(mode.p, mode.q, r, c);
      }
    }
    return acc / N_CELLS;
  });
}

export function energyMetrics(flat, retainMaxDegree = 1) {
  const coeffs = momentCoefficients(flat);
  /** @type {Record<number, number>} */
  const byDegree = { 0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0 };
  MOMENT_MODES.forEach((mode, i) => {
    byDegree[mode.degree] += coeffs[i] * coeffs[i];
  });
  const total = Object.values(byDegree).reduce((a, b) => a + b, 0);
  let retained = 0;
  for (const [d, e] of Object.entries(byDegree)) {
    if (Number(d) <= retainMaxDegree) retained += e;
  }
  return { total, retained, residual: total - retained, byDegree };
}

export function parsevalCheck(flat) {
  const meanSquare = flat.reduce((s, v) => s + v * v, 0) / N_CELLS;
  const coeffEnergy = momentCoefficients(flat).reduce((s, c) => s + c * c, 0);
  return meanSquare - coeffEnergy;
}

function quantile(sorted, q) {
  if (q <= 0) return sorted[0];
  if (q >= 1) return sorted[sorted.length - 1];
  const pos = q * (sorted.length - 1);
  const lo = Math.floor(pos);
  const hi = Math.ceil(pos);
  if (lo === hi) return sorted[lo];
  const w = pos - lo;
  return sorted[lo] * (1 - w) + sorted[hi] * w;
}

/**
 * Run control ensemble for one magic square (browser-side batch).
 * @param {number} squareId
 * @param {number[]} baseFlat length-16 row-major
 * @param {{ seed?: number, nReplicates?: number, retainMaxDegree?: number, swapProtocol?: object }} cfg
 */
export function runControlEnsemble(squareId, baseFlat, cfg = {}) {
  const seed = cfg.seed ?? 1215;
  const nReplicates = cfg.nReplicates ?? 200;
  const retainMaxDegree = cfg.retainMaxDegree ?? 1;
  const swapProtocol = {
    pairSampling: "distinct_pairs_no_replacement",
    acrossK: "paired_prefix",
    ...(cfg.swapProtocol || {}),
  };

  const conditions = ["rand", "swap1", "swap2", "swap3"];
  /** @type {Record<string, object>} */
  const summaries = {};

  for (const cond of conditions) {
    /** @type {Array<{ total: number, retained: number, residual: number }>} */
    const energies = [];
    for (let rep = 0; rep < nReplicates; rep += 1) {
      let flat;
      if (cond === "rand") {
        let state = seedToState(
          deriveReplicateSeed(seed, squareId, rep, PERM_DOMAIN),
        );
        const shuffled = fisherYates(baseFlat.slice(), state);
        flat = shuffled.arr;
      } else {
        let state = seedToState(
          deriveReplicateSeed(seed, squareId, rep, SWAP_DOMAIN),
        );
        const k = Number(cond.slice(-1));
        const { traces } = swapEnsembleForKValues(
          baseFlat,
          [1, 2, 3],
          state,
          swapProtocol,
        );
        flat = traces[k].flat;
      }
      energies.push(energyMetrics(flat, retainMaxDegree));
    }
    const totals = energies.map((e) => e.total);
    const retained = energies.map((e) => e.retained);
    const residuals = energies.map((e) => e.residual).sort((a, b) => a - b);
    const mean = (xs) => xs.reduce((a, b) => a + b, 0) / xs.length;
    const pstdev = (xs) => {
      const m = mean(xs);
      return Math.sqrt(xs.reduce((s, x) => s + (x - m) ** 2, 0) / xs.length);
    };
    summaries[cond] = {
      n: nReplicates,
      mean_total: mean(totals),
      std_total: pstdev(totals),
      mean_retained: mean(retained),
      mean_residual: mean(residuals),
      q05_residual: quantile(residuals, 0.05),
      q50_residual: quantile(residuals, 0.5),
      q95_residual: quantile(residuals, 0.95),
    };
  }

  return {
    squareId,
    baseEnergy: energyMetrics(baseFlat, retainMaxDegree),
    parsevalError: parsevalCheck(baseFlat),
    summaries,
  };
}

// CommonJS fallback for smoke tests without bundler
if (typeof module !== "undefined" && module.exports) {
  module.exports = {
    mulberry32Next,
    mulberry32NextU32,
    seedToState,
    randBelow,
    deriveReplicateSeed,
    fisherYates,
    swapEnsembleForKValues,
    energyMetrics,
    runControlEnsemble,
    PERM_DOMAIN,
    SWAP_DOMAIN,
    UNORDERED_PAIRS,
  };
}
