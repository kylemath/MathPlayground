/*
 * lattice.js — point-set generators for the Prime Lattice Explorer.
 *
 * Coordinates are returned as a flat Float32Array of length 3·count:
 *     [x0, y0, z0, x1, y1, z1, …]
 * each normalised into the cube [-0.5, +0.5]^3.
 *
 * Two layers of choice control how an integer index n becomes a 3D position:
 *
 *   1. The *generator* (primes, every k-th, random, …) decides which
 *      integers participate.
 *   2. The *mapping* (row-major raster, 3D Ulam cubic-shell, stacked 2D
 *      Ulam) decides where the integer n lives in space.
 *
 * Generators are pure and side-effect free; the app caches results by
 * (mapping × generator × params × N × L).
 */

const Lattice = (function () {

  /* ── prime sieve (shared across layers) ────────────────────────────── */

  let _primeSieve = null;
  let _primeSieveLimit = 0;
  /** Sieve of Eratosthenes up to limit. Uses one byte per integer; the
   *  ~10 MB cap at limit = 1e7 is why the UI slider tops out there. */
  function getPrimeSieve(limit) {
    if (_primeSieve && _primeSieveLimit >= limit) return _primeSieve;
    const sieve = new Uint8Array(limit + 1);
    sieve.fill(1);
    sieve[0] = 0;
    sieve[1] = 0;
    const sqrtLimit = Math.floor(Math.sqrt(limit));
    for (let i = 2; i <= sqrtLimit; i++) {
      if (sieve[i]) {
        for (let j = i * i; j <= limit; j += i) sieve[j] = 0;
      }
    }
    _primeSieve = sieve;
    _primeSieveLimit = limit;
    return sieve;
  }

  /* ── mappings: integer → (x, y, z) ─────────────────────────────────── */
  //
  // Each mapping exposes:
  //   id       — short string id used by the UI dropdown
  //   name     — display name
  //   capacity(L) — how many integers fit in a cube of side L
  //   toCoord(n, L, out, outIdx) — writes 3 floats into `out` at `outIdx`
  //                                in normalised cube coords [-0.5, 0.5].
  // All mappings are 0-indexed: n = 0 is one of the placed integers.

  // ── raster: classic row-major. n = 0 at corner (−0.5, −0.5, −0.5). ──
  function rasterCoord(n, L, out, outIdx) {
    const x = n % L;
    const y = Math.floor(n / L) % L;
    const z = Math.floor(n / (L * L));
    const inv = 1 / L;
    out[outIdx]     = (x + 0.5) * inv - 0.5;
    out[outIdx + 1] = (y + 0.5) * inv - 0.5;
    out[outIdx + 2] = (z + 0.5) * inv - 0.5;
  }

  // ── 2D Ulam ring helpers (shared by stacked-2D and cubic-shell side strips)
  //
  // 0-indexed: ringIndex 0 returns (0, 0). For m ≥ 1, locate ring k where
  //   (2k − 1)² ≤ m < (2k + 1)².    (k ≥ 1)
  // Within ring k, local index m' = m − (2k − 1)² walks 8k cells counter-
  // clockwise starting one step right of the previous ring's bottom-right
  // corner. That matches the classic Ulam ordering (1 at centre, 2 right,
  // 3 up, 4 left, …) shifted to 0-index.
  function ulamRing(m) {
    if (m === 0) return [0, 0];
    let k = Math.max(1, Math.round((Math.sqrt(m) + 1) * 0.5));
    while ((2 * k + 1) * (2 * k + 1) <= m) k++;
    while (k > 0 && (2 * k - 1) * (2 * k - 1) > m) k--;
    const m1 = m - (2 * k - 1) * (2 * k - 1);
    let x, y;
    if (m1 < 2 * k) {              // right edge going up
      x = k;
      y = -(k - 1) + m1;
    } else if (m1 < 4 * k) {       // top edge going left
      x = 3 * k - 1 - m1;
      y = k;
    } else if (m1 < 6 * k) {       // left edge going down
      x = -k;
      y = 5 * k - 1 - m1;
    } else {                       // bottom edge going right
      x = m1 - 7 * k + 1;
      y = -k;
    }
    return [x, y];
  }

  // ── stacked 2D Ulam: each z-slab is a 2D Ulam spiral on L² cells, slabs
  //    stacked in increasing z. n = 0 at the centre of the bottom slab. ──
  function stackedUlamCoord(n, L, out, outIdx) {
    const L2 = L * L;
    const z = Math.floor(n / L2);
    const m = n - z * L2;
    const [ux, uy] = ulamRing(m);
    const half = (L - 1) * 0.5;
    const inv = 1 / L;
    out[outIdx]     = ux * inv;
    out[outIdx + 1] = uy * inv;
    out[outIdx + 2] = (z - half) * inv;
  }

  // ── 3D Ulam cubic-shell mapping.
  //
  // Concentric cubic shells centred on origin: shell 0 is the single cell
  // (0,0,0). Shell k (k ≥ 1) is the set of integer points with
  // max(|x|, |y|, |z|) = k, containing exactly 24k² + 2 cells. The first
  // (2k − 1)³ integers fill shells 0..k−1, so shell k starts at index
  //   start(k) = (2k − 1)³.
  //
  // Within shell k we walk:
  //   1. Top face (z = +k):    (2k+1)² cells, raster scan in (x, y).
  //   2. Bottom face (z = −k):  (2k+1)² cells, raster scan.
  //   3. Side strips (4 faces, z ∈ {−(k−1)..+(k−1)}):
  //         for each z (top → bottom), walk the (2k+1)² boundary as a
  //         2D Ulam ring of radius k (8k cells per slab).
  //
  // The walk is deterministic — not contiguous — but it gives the visual
  // feel of "fill the centre, then keep expanding outward by one shell".
  function cubicShellCoord(n, L, out, outIdx) {
    if (n === 0) {
      out[outIdx] = 0; out[outIdx + 1] = 0; out[outIdx + 2] = 0;
      return;
    }
    // Find shell k via cbrt then correct.
    let k = Math.max(1, Math.round((Math.cbrt(n) + 1) * 0.5));
    while ((2 * k + 1) ** 3 <= n) k++;
    while (k > 0 && (2 * k - 1) ** 3 > n) k--;
    const shellStart = (2 * k - 1) ** 3;
    const m = n - shellStart;           // local index within shell, 0..24k²+1
    const side = 2 * k + 1;
    const faceCount = side * side;      // cells per top/bottom face

    let x, y, z;
    if (m < faceCount) {
      // Top face z = +k, raster scan.
      const i = m % side, j = (m - i) / side;
      x = i - k; y = j - k; z = k;
    } else if (m < 2 * faceCount) {
      // Bottom face z = -k.
      const m2 = m - faceCount;
      const i = m2 % side, j = (m2 - i) / side;
      x = i - k; y = j - k; z = -k;
    } else {
      // Side strips. 2k - 1 z-slabs, 8k cells each (boundary of square).
      const m3 = m - 2 * faceCount;
      const perSlab = 8 * k;
      const zIdx = Math.floor(m3 / perSlab);
      const m4 = m3 - zIdx * perSlab;
      z = (k - 1) - zIdx;               // top-down through the side strips
      if (m4 < 2 * k) {                 // right edge going up
        x = k;
        y = -(k - 1) + m4;
      } else if (m4 < 4 * k) {          // top edge going left
        x = 3 * k - 1 - m4;
        y = k;
      } else if (m4 < 6 * k) {          // left edge going down
        x = -k;
        y = 5 * k - 1 - m4;
      } else {                          // bottom edge going right
        x = m4 - 7 * k + 1;
        y = -k;
      }
    }

    // Clamp to the L-cube: drop points whose shell is bigger than the cube
    // by placing them at the origin. The generators apply `capacity(L)` so
    // this is just a safety net.
    const inv = 1 / L;
    out[outIdx]     = x * inv;
    out[outIdx + 1] = y * inv;
    out[outIdx + 2] = z * inv;
  }

  // ── 3D Ulam snake: a genuine continuous Hamiltonian path ────────────
  //
  // Unlike `cubicShell`, this mapping guarantees that consecutive integers
  // n and n+1 are always spatial neighbours (Chebyshev distance exactly 1),
  // so it actually *snakes* through 3D space rather than visiting each shell
  // in disconnected pieces. This is the property that makes Ulam-style
  // prime-polynomial "spokes" appear.
  //
  // Construction — shells are filled outward from the origin, and within a
  // shell the walk is:
  //   1. bottom face (z = −k): 2D Ulam spiral OUT from the face centre,
  //   2. side rings (z = −k+1 … k−1): walk each square ring, stepping up
  //      one z at a time (a boustrophedon up a square cylinder),
  //   3. top face (z = +k): square spiral IN, ending at the face centre.
  // So `shellUp(k)` runs from (0,0,−k) to (0,0,+k). Odd shells use it
  // forward; even shells use it reversed (so they run (0,0,+k) → (0,0,−k)).
  // Consecutive shells then connect along the z-axis through their face
  // centres: e.g. shell k (odd, up) ends at (0,0,+k) and shell k+1 (even,
  // down) starts at (0,0,+(k+1)) — Chebyshev distance 1. The origin shell
  // (0,0,0) connects to shell 1's start (0,0,−1) the same way.
  //
  // The integer path is independent of L (L only sets the normalisation and
  // the capacity cap), so it is built once and cached globally.

  let _snakeCells = null;   // Int32Array, flat [x0,y0,z0, x1,y1,z1, …]
  let _snakeLen = 0;        // number of cells currently built

  /** Spiral-out enumeration of the square [−k,k]² from its centre, reusing
   *  the 2D Ulam ordering. Element 0 is (0,0); the last element is on the
   *  outer ring (Chebyshev radius k). */
  function _ulamSquare(k) {
    const total = (2 * k + 1) * (2 * k + 1);
    const arr = new Array(total);
    for (let m = 0; m < total; m++) arr[m] = ulamRing(m);
    return arr;
  }

  /** Canonical CCW cycle of the square ring of radius r (8r cells), starting
   *  at the bottom-right corner (r, −r). */
  function _canonRing(r) {
    const cells = [];
    for (let y = -r; y < r; y++) cells.push([r, y]);     // right edge ↑
    for (let x = r; x > -r; x--) cells.push([x, r]);     // top edge ←
    for (let y = r; y > -r; y--) cells.push([-r, y]);    // left edge ↓
    for (let x = -r; x < r; x++) cells.push([x, -r]);    // bottom edge →
    return cells;
  }

  /** The ring of radius r, rotated to begin at startXY and proceed CCW. The
   *  last cell returned is the CCW-neighbour of startXY (so a vertical step
   *  to the next layer keeps the footprint on the ring). */
  function _ringFrom(startXY, r) {
    const canon = _canonRing(r);
    let idx = 0;
    for (let i = 0; i < canon.length; i++) {
      if (canon[i][0] === startXY[0] && canon[i][1] === startXY[1]) { idx = i; break; }
    }
    const out = new Array(canon.length);
    for (let i = 0; i < canon.length; i++) out[i] = canon[(idx + i) % canon.length];
    return out;
  }

  /** Step one cell inward (toward the origin) from a ring-r cell, landing on
   *  ring r−1. Reduces whichever axis is at the Chebyshev radius. */
  function _inwardNeighbor(cell, r) {
    let [x, y] = cell;
    if (Math.abs(x) === r) x -= Math.sign(x);
    if (Math.abs(y) === r) y -= Math.sign(y);
    return [x, y];
  }

  /** Inward square spiral filling [−k,k]², starting at an arbitrary outer-
   *  ring cell `startXY` and ending at the centre (0,0). */
  function _spiralInFrom(startXY, k) {
    const out = [];
    let start = startXY;
    for (let r = k; r >= 1; r--) {
      const ring = _ringFrom(start, r);
      for (const c of ring) out.push(c);
      start = _inwardNeighbor(ring[ring.length - 1], r);
    }
    out.push([0, 0]);
    return out;
  }

  /** Ordered cells of shell k as a continuous walk from (0,0,−k) to (0,0,+k).
   *  Length is 24k² + 2 for k ≥ 1. */
  function _shellUpCells(k) {
    const out = [];
    const sq = _ulamSquare(k);
    for (const [x, y] of sq) out.push([x, y, -k]);     // bottom face, spiral out
    let cx = sq[sq.length - 1][0];
    let cy = sq[sq.length - 1][1];
    for (let z = -k + 1; z <= k - 1; z++) {            // side rings up the cylinder
      const ring = _ringFrom([cx, cy], k);
      for (const [x, y] of ring) out.push([x, y, z]);
      cx = ring[ring.length - 1][0];
      cy = ring[ring.length - 1][1];
    }
    const inward = _spiralInFrom([cx, cy], k);          // top face, spiral in to centre
    for (const [x, y] of inward) out.push([x, y, k]);
    return out;
  }

  function _buildSnakeUpToShell(K) {
    const cells = [];
    cells.push(0, 0, 0);                                // shell 0 = origin
    for (let k = 1; k <= K; k++) {
      const shell = _shellUpCells(k);
      if (k % 2 === 1) {                                // odd shell: forward (up)
        for (const c of shell) cells.push(c[0], c[1], c[2]);
      } else {                                          // even shell: reversed (down)
        for (let i = shell.length - 1; i >= 0; i--) {
          const c = shell[i];
          cells.push(c[0], c[1], c[2]);
        }
      }
    }
    _snakeCells = Int32Array.from(cells);
    _snakeLen = cells.length / 3;
  }

  /** Ensure the cached snake path covers index `maxIndex`. */
  function _ensureSnake(maxIndex) {
    if (_snakeCells && _snakeLen > maxIndex) return;
    let K = 1;
    while ((2 * K + 1) ** 3 <= maxIndex + 1) K++;
    _buildSnakeUpToShell(K);
  }

  function ulamSnakeCoord(n, L, out, outIdx) {
    const cap = (2 * Math.floor((L - 1) / 2) + 1) ** 3;
    if (n >= cap) { out[outIdx] = 0; out[outIdx + 1] = 0; out[outIdx + 2] = 0; return; }
    _ensureSnake(n);
    const i = n * 3;
    const inv = 1 / L;
    out[outIdx]     = _snakeCells[i] * inv;
    out[outIdx + 1] = _snakeCells[i + 1] * inv;
    out[outIdx + 2] = _snakeCells[i + 2] * inv;
  }

  const Mappings = {
    ulamSnake: {
      id: 'ulamSnake',
      name: '3D Ulam snake (continuous)',
      // Fills cubic shells 0..K where 2K+1 ≤ L → K = floor((L-1)/2).
      capacity: (L) => {
        const K = Math.floor((L - 1) / 2);
        return (2 * K + 1) ** 3;
      },
      toCoord: ulamSnakeCoord,
    },
    cubicShell: {
      id: 'cubicShell',
      name: '3D Ulam cubic shells (piecewise)',
      // shells 0..K fit in side 2K+1 ≤ L → K = floor((L-1)/2); count = (2K+1)³
      capacity: (L) => {
        const K = Math.floor((L - 1) / 2);
        return (2 * K + 1) ** 3;
      },
      toCoord: cubicShellCoord,
    },
    stackedUlam: {
      id: 'stackedUlam',
      name: 'Stacked 2D Ulam (per Z-slab)',
      capacity: (L) => L * L * L,
      toCoord: stackedUlamCoord,
    },
    raster: {
      id: 'raster',
      name: 'Row-major raster',
      capacity: (L) => L * L * L,
      toCoord: rasterCoord,
    },
  };

  /* ── shared coord builder ──────────────────────────────────────────── */

  function _coordsFromIndices(indices, L, mappingId) {
    const mapping = Mappings[mappingId] || Mappings.raster;
    const N = indices.length;
    const out = new Float32Array(N * 3);
    for (let i = 0; i < N; i++) {
      mapping.toCoord(indices[i], L, out, i * 3);
    }
    return out;
  }

  function _effectiveLimit(nMax, L, mappingId) {
    const mapping = Mappings[mappingId] || Mappings.raster;
    return Math.min(nMax, mapping.capacity(L));
  }

  /* ── public generators ─────────────────────────────────────────────── */

  /** All primes p ≤ nMax mapped via the chosen index mapping. */
  function primes({ nMax, L, mapping }) {
    const limit = _effectiveLimit(nMax, L, mapping);
    const sieve = getPrimeSieve(limit);
    const indices = [];
    for (let n = 2; n <= limit; n++) if (sieve[n]) indices.push(n);
    return {
      positions: _coordsFromIndices(indices, L, mapping),
      count: indices.length,
      label: `primes ≤ ${limit.toLocaleString()}`,
    };
  }

  /** Composite numbers (¬prime) in 2..nMax — the visual complement of primes. */
  function composites({ nMax, L, mapping }) {
    const limit = _effectiveLimit(nMax, L, mapping);
    const sieve = getPrimeSieve(limit);
    const indices = [];
    for (let n = 4; n <= limit; n++) if (!sieve[n]) indices.push(n);
    return {
      positions: _coordsFromIndices(indices, L, mapping),
      count: indices.length,
      label: `composites ≤ ${limit.toLocaleString()}`,
    };
  }

  /** Every integer 1..nMax (gets dense fast — useful as a baseline). */
  function everyInteger({ nMax, L, mapping }) {
    const limit = _effectiveLimit(nMax, L, mapping);
    const indices = new Uint32Array(limit);
    for (let i = 0; i < limit; i++) indices[i] = i + 1;
    return {
      positions: _coordsFromIndices(indices, L, mapping),
      count: limit,
      label: `all integers 1..${limit.toLocaleString()}`,
    };
  }

  /** Every k-th integer: k, 2k, 3k, … up to nMax. */
  function everyKth({ nMax, L, k, mapping }) {
    k = Math.max(1, Math.floor(k));
    const limit = _effectiveLimit(nMax, L, mapping);
    const indices = [];
    for (let n = k; n <= limit; n += k) indices.push(n);
    return {
      positions: _coordsFromIndices(indices, L, mapping),
      count: indices.length,
      label: `every ${k}-th integer`,
    };
  }

  /** Arithmetic progression a, a+d, a+2d, … */
  function arithmeticProgression({ nMax, L, a, d, mapping }) {
    a = Math.max(1, Math.floor(a));
    d = Math.max(1, Math.floor(d));
    const limit = _effectiveLimit(nMax, L, mapping);
    const indices = [];
    for (let n = a; n <= limit; n += d) indices.push(n);
    return {
      positions: _coordsFromIndices(indices, L, mapping),
      count: indices.length,
      label: `arithmetic ${a} + ${d}k`,
    };
  }

  /** Uniform random subset of integers 1..nMax of approximate density p.
   *  Deterministic given seed so re-renders are stable until you tweak knobs. */
  function randomUniformIntegers({ nMax, L, density, seed, mapping }) {
    const limit = _effectiveLimit(nMax, L, mapping);
    const rng = mulberry32(seed >>> 0);
    const indices = [];
    for (let n = 1; n <= limit; n++) if (rng() < density) indices.push(n);
    return {
      positions: _coordsFromIndices(indices, L, mapping),
      count: indices.length,
      label: `random integers (p = ${density.toFixed(3)})`,
    };
  }

  /** Random points uniformly distributed in the continuous cube. NOT on
   *  the lattice — exists as a control for "no integer alignment at all". */
  function randomContinuous({ nMax, L, density, seed, mapping }) {
    const limit = _effectiveLimit(nMax, L, mapping);
    const count = Math.floor(limit * density);
    const rng = mulberry32((seed ^ 0xa5a5a5a5) >>> 0);
    const out = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      out[i * 3 + 0] = rng() - 0.5;
      out[i * 3 + 1] = rng() - 0.5;
      out[i * 3 + 2] = rng() - 0.5;
    }
    return { positions: out, count, label: `random continuous (n = ${count.toLocaleString()})` };
  }

  /** Gaussian cloud centred on origin. */
  function randomGaussian({ nMax, L, density, sigma, seed, mapping }) {
    const limit = _effectiveLimit(nMax, L, mapping);
    const count = Math.floor(limit * density);
    const rng = mulberry32((seed ^ 0x5a5a5a5a) >>> 0);
    const out = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      out[i * 3 + 0] = gaussian(rng) * sigma;
      out[i * 3 + 1] = gaussian(rng) * sigma;
      out[i * 3 + 2] = gaussian(rng) * sigma;
    }
    return { positions: out, count, label: `Gaussian σ = ${sigma.toFixed(2)} (n = ${count.toLocaleString()})` };
  }

  /** Quasi-periodic 3D low-discrepancy sequence (plastic-constant R3).
   *  Bravais-free dot cloud — no integer alignments at all. */
  function quasiperiodic({ nMax, L, density, seed, mapping }) {
    const limit = _effectiveLimit(nMax, L, mapping);
    const count = Math.floor(limit * density);
    const out = new Float32Array(count * 3);
    const g = 1.22074408460575947536;  // plastic / golden 3D constant
    const a1 = 1.0 / g;
    const a2 = 1.0 / (g * g);
    const a3 = 1.0 / (g * g * g);
    const offset = (seed % 997) / 997;
    for (let i = 0; i < count; i++) {
      const t = i + 1 + offset;
      out[i * 3 + 0] = ((t * a1) % 1) - 0.5;
      out[i * 3 + 1] = ((t * a2) % 1) - 0.5;
      out[i * 3 + 2] = ((t * a3) % 1) - 0.5;
    }
    return {
      positions: out,
      count,
      label: `quasi-periodic R3 (n = ${count.toLocaleString()})`,
    };
  }

  /* ── helpers ───────────────────────────────────────────────────────── */

  function mulberry32(a) {
    return function () {
      a |= 0; a = a + 0x6D2B79F5 | 0;
      let t = a;
      t = Math.imul(t ^ t >>> 15, t | 1);
      t ^= t + Math.imul(t ^ t >>> 7, t | 61);
      return ((t ^ t >>> 14) >>> 0) / 4294967296;
    };
  }

  /** Standard normal via Box–Muller, caching the second sample. */
  let _gaussCache = null;
  function gaussian(rng) {
    if (_gaussCache !== null) {
      const v = _gaussCache; _gaussCache = null; return v;
    }
    let u1;
    do { u1 = rng(); } while (u1 === 0);
    const u2 = rng();
    const mag = Math.sqrt(-2.0 * Math.log(u1));
    _gaussCache = mag * Math.sin(2 * Math.PI * u2);
    return mag * Math.cos(2 * Math.PI * u2);
  }

  return {
    getPrimeSieve,
    Mappings,
    primes,
    composites,
    everyInteger,
    everyKth,
    arithmeticProgression,
    randomUniformIntegers,
    randomContinuous,
    randomGaussian,
    quasiperiodic,
  };
})();
