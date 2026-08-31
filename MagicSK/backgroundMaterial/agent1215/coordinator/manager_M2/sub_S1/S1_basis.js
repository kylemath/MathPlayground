/**
 * 1215-M2-S1 — Zero-dependency 4×4 orthonormal moment basis (reference)
 * Row-major indexing: k = 4*i + j
 */
(function (root, factory) {
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = factory();
  } else {
    root.MomentBasis4 = factory();
  }
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

  var SQRT5 = Math.sqrt(5);
  var SQRT5_9 = Math.sqrt(5 / 9);
  var COORDS = [-1.5, -0.5, 0.5, 1.5];

  function phi1d(p, t) {
    if (p === 0) return 0.5;
    if (p === 1) return t / SQRT5;
    if (p === 2) return (t * t - 1.25) / 2;
    if (p === 3) return SQRT5_9 * (t * t * t - (41 / 20) * t);
    throw new RangeError('degree must be 0..3');
  }

  var PHI = [];
  for (var p = 0; p < 4; p++) {
    PHI[p] = COORDS.map(function (t) { return phi1d(p, t); });
  }

  function modeIndex(p, q, i, j) {
    return PHI[p][i] * PHI[q][j];
  }

  function modeVector(p, q) {
    var v = new Float64Array(16);
    var idx = 0;
    for (var i = 0; i < 4; i++) {
      for (var j = 0; j < 4; j++) {
        v[idx++] = modeIndex(p, q, i, j);
      }
    }
    return v;
  }

  var MODES = {};
  for (var p2 = 0; p2 < 4; p2++) {
    for (var q2 = 0; q2 < 4; q2++) {
      MODES[p2 + '' + q2] = modeVector(p2, q2);
    }
  }

  function orderKey(p, q) {
    var deg = p + q;
    var mx = Math.max(p, q);
    return deg * 1000 + mx * 100 + p * 10 + q;
  }

  var COMPLETE_ORDER = [];
  for (var p3 = 0; p3 < 4; p3++) {
    for (var q3 = 0; q3 < 4; q3++) {
      COMPLETE_ORDER.push({ p: p3, q: q3, key: orderKey(p3, q3) });
    }
  }
  COMPLETE_ORDER.sort(function (a, b) { return a.key - b.key; });

  var HIGHER_MOMENTS = COMPLETE_ORDER.filter(function (m) {
    return m.p + m.q >= 2;
  });

  function dot(a, b) {
    var s = 0;
    for (var k = 0; k < 16; k++) s += a[k] * b[k];
    return s;
  }

  function coefficients(field) {
    var out = {};
    for (var p4 = 0; p4 < 4; p4++) {
      for (var q4 = 0; q4 < 4; q4++) {
        var key = p4 + '' + q4;
        out[key] = dot(field, MODES[key]);
      }
    }
    return out;
  }

  function reconstruct(coeffs) {
    var f = new Float64Array(16);
    for (var p5 = 0; p5 < 4; p5++) {
      for (var q5 = 0; q5 < 4; q5++) {
        var c = coeffs[p5 + '' + q5];
        if (c === 0) continue;
        var m = MODES[p5 + '' + q5];
        for (var k = 0; k < 16; k++) f[k] += c * m[k];
      }
    }
    return f;
  }

  function safeDiv(num, den) {
    return Math.abs(den) > 1e-15 ? num / den : 0;
  }

  function energyMetrics(field, retainedList) {
    var coeffs = coefficients(field);
    var eTotal = 0;
    var c00 = coeffs['00'];
    for (var key in coeffs) {
      if (Object.prototype.hasOwnProperty.call(coeffs, key)) {
        eTotal += coeffs[key] * coeffs[key];
      }
    }
    var eDc = c00 * c00;
    var eNonconst = eTotal - eDc;
    var eRetained = 0;
    var dcInS = false;
    for (var r = 0; r < retainedList.length; r++) {
      var pq = retainedList[r];
      var k2 = pq.p + '' + pq.q;
      eRetained += coeffs[k2] * coeffs[k2];
      if (pq.p === 0 && pq.q === 0) dcInS = true;
    }
    var retainedNonconst = eRetained - (dcInS ? eDc : 0);
    return {
      coeffs: coeffs,
      E_total: eTotal,
      E_dc: eDc,
      E_nonconst: eNonconst,
      E_retained: eRetained,
      E_residual: eTotal - eRetained,
      retained_frac_total: safeDiv(eRetained, eTotal),
      retained_frac_nonconst: safeDiv(retainedNonconst, eNonconst),
      residual_frac_total: safeDiv(eTotal - eRetained, eTotal),
      residual_frac_nonconst: safeDiv(eNonconst - retainedNonconst, eNonconst),
    };
  }

  return {
    COORDS: COORDS,
    PHI: PHI,
    MODES: MODES,
    COMPLETE_ORDER: COMPLETE_ORDER,
    HIGHER_MOMENTS: HIGHER_MOMENTS,
    coefficients: coefficients,
    reconstruct: reconstruct,
    energyMetrics: energyMetrics,
    TOL: { ortho: 1e-12, parseval: 1e-12, recon: 1e-10, zero: 1e-9 },
  };
});
