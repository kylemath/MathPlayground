/*
 * render.js — 3D point cloud renderer for the Prime Lattice Explorer.
 *
 * Zero-dependency canvas 2D renderer. Maintains an orbit camera and
 * projects every point either in perspective or orthographically. Layers
 * are drawn back-to-front per-layer (no global depth sort — keeping it
 * O(N) for millions of points; depth-fade approximates occlusion).
 *
 * Public API:
 *     const r = new Renderer(canvasEl);
 *     r.setLayers([{ id, name, color, alpha, positions: Float32Array, count, visible }]);
 *     r.setProjection('perspective' | 'orthographic');
 *     r.setOptions({ fovDeg, zoom, distance, dotSize, alpha, depthFade,
 *                    autoRotate, showBox, showAxes });
 *     r.start();
 *     r.onStats = ({ visibleCount, fps }) => { ... };
 */

class Renderer {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d', { alpha: false });
    this.dpr = window.devicePixelRatio || 1;
    this.layers = [];
    this.projection = 'perspective';
    this.opts = {
      fovDeg: 60,
      zoom: 1.0,
      distance: 2.5,
      dotSize: 1.6,
      alpha: 0.85,
      depthFade: true,
      autoRotate: false,
      showBox: true,
      showAxes: false,
      // Single-slab slicing. axis: 0=x,1=y,2=z. center/half are in
      // normalised cube coords [-0.5, 0.5]; only points with the chosen
      // coordinate inside [center-half, center+half] are drawn.
      slice: {
        enabled: false,
        axis: 2,
        center: 0,
        half: 0.02,
        gradient: false,
        cellWidth: 0.01,
        lines: { enabled: false, only: false, minHits: 5, maxGap: 3 },
      },
    };
    this.cam = { yaw: 0.6, pitch: 0.45 };
    this.onStats = null;

    this._dragging = false;
    this._lastX = 0;
    this._lastY = 0;
    this._frame = 0;
    this._lastT = 0;
    this._fpsEMA = 0;
    this._needsRedraw = true;

    this._resize = this._resize.bind(this);
    window.addEventListener('resize', this._resize);
    this._resize();

    this._installInput();
  }

  destroy() {
    window.removeEventListener('resize', this._resize);
  }

  setLayers(layers) {
    this.layers = layers;
    this._needsRedraw = true;
  }

  setProjection(p) {
    this.projection = p;
    this._needsRedraw = true;
  }

  setOptions(patch) {
    Object.assign(this.opts, patch);
    this._needsRedraw = true;
  }

  resetCamera() {
    this.cam.yaw = 0.6;
    this.cam.pitch = 0.45;
    this.opts.zoom = 1.0;
    this.opts.distance = 2.5;
    this._needsRedraw = true;
  }

  // Snap the orbit camera so we look exactly down one world axis. With the
  // rotation matrix in _render(), these (yaw, pitch) pairs make camera depth
  // align with the chosen axis:
  //   z → (0, 0)        screen shows world X (→) / Y (↑)
  //   y → (0, π/2)      screen shows world X (→) / Z (↑)
  //   x → (-π/2, 0)     screen shows world Z (→) / Y (↑)
  setView(axis) {
    switch (axis) {
      case 'x': this.cam.yaw = -Math.PI / 2; this.cam.pitch = 0; break;
      case 'y': this.cam.yaw = 0;            this.cam.pitch = Math.PI / 2; break;
      case 'z': this.cam.yaw = 0;            this.cam.pitch = 0; break;
      default: return;
    }
    this._needsRedraw = true;
  }

  /* ── lifecycle ──────────────────────────────────────────────────── */

  start() {
    const loop = (t) => {
      const dt = (t - this._lastT) / 1000;
      this._lastT = t;
      if (this.opts.autoRotate) {
        this.cam.yaw += dt * 0.3;
        this._needsRedraw = true;
      }
      if (this._needsRedraw) {
        this._render();
        this._needsRedraw = false;
        this._frame++;
      }
      if (dt > 0) {
        const instantFps = 1 / dt;
        this._fpsEMA = this._fpsEMA * 0.9 + instantFps * 0.1;
        if (this.onStats && this._frame % 6 === 0) {
          this.onStats({ visibleCount: this._lastVisibleCount, fps: Math.round(this._fpsEMA) });
        }
      }
      requestAnimationFrame(loop);
    };
    requestAnimationFrame(loop);
  }

  /* ── input ───────────────────────────────────────────────────────── */

  _installInput() {
    const c = this.canvas;
    c.addEventListener('pointerdown', (e) => {
      this._dragging = true;
      this._lastX = e.clientX;
      this._lastY = e.clientY;
      c.setPointerCapture(e.pointerId);
    });
    c.addEventListener('pointermove', (e) => {
      if (!this._dragging) return;
      const dx = e.clientX - this._lastX;
      const dy = e.clientY - this._lastY;
      this._lastX = e.clientX;
      this._lastY = e.clientY;
      this.cam.yaw -= dx * 0.005;
      this.cam.pitch -= dy * 0.005;
      const lim = Math.PI / 2 - 0.05;
      if (this.cam.pitch > lim) this.cam.pitch = lim;
      if (this.cam.pitch < -lim) this.cam.pitch = -lim;
      this._needsRedraw = true;
    });
    c.addEventListener('pointerup', (e) => {
      this._dragging = false;
      try { c.releasePointerCapture(e.pointerId); } catch (_) {}
    });
    c.addEventListener('wheel', (e) => {
      e.preventDefault();
      const k = Math.exp(e.deltaY * 0.001);
      this.opts.zoom = Math.max(0.2, Math.min(8, this.opts.zoom / k));
      this._needsRedraw = true;
      if (this._onZoomChange) this._onZoomChange(this.opts.zoom);
    }, { passive: false });
  }

  onZoomChange(cb) { this._onZoomChange = cb; }

  /* ── canvas sizing ───────────────────────────────────────────────── */

  _resize() {
    const rect = this.canvas.getBoundingClientRect();
    this.dpr = window.devicePixelRatio || 1;
    this.canvas.width = Math.max(2, Math.floor(rect.width * this.dpr));
    this.canvas.height = Math.max(2, Math.floor(rect.height * this.dpr));
    this._needsRedraw = true;
  }

  /* ── rendering ───────────────────────────────────────────────────── */

  _render() {
    const ctx = this.ctx;
    const W = this.canvas.width;
    const H = this.canvas.height;
    ctx.fillStyle = '#07090d';
    ctx.fillRect(0, 0, W, H);

    const cy = Math.cos(this.cam.yaw),    sy = Math.sin(this.cam.yaw);
    const cp = Math.cos(this.cam.pitch),  sp = Math.sin(this.cam.pitch);

    // World→camera (camera looks from +z, with yaw around y, pitch around x).
    // Build rotation matrix entries directly.
    const m00 =  cy,         m01 = 0,    m02 =  sy;
    const m10 =  sy * sp,    m11 = cp,   m12 = -cy * sp;
    const m20 = -sy * cp,    m21 = sp,   m22 =  cy * cp;

    const d = this.opts.distance;
    const halfW = W * 0.5;
    const halfH = H * 0.5;

    // Common scaling: in perspective use focal length f = halfH / tan(fov/2).
    // In orthographic use a pixel-per-world ratio chosen so the unit cube fits.
    const isPerspective = this.projection === 'perspective';
    const fov = (this.opts.fovDeg * Math.PI) / 180;
    const focal = halfH / Math.tan(fov / 2);
    const orthoScale = Math.min(halfW, halfH) * 0.9;

    const zoom = this.opts.zoom;
    const dotPx = Math.max(0.5, this.opts.dotSize * this.dpr);

    // Pre-compute the per-camera z range used for depth fade. With the cube
    // centred at origin, point z range is roughly [d - 0.87, d + 0.87].
    const zNear = d - 0.95;
    const zFar  = d + 0.95;
    const fadeOn = this.opts.depthFade;

    let visibleCount = 0;

    // Slice clip bounds (precomputed once per frame).
    const slice = this.opts.slice;
    const sliceOn = slice && slice.enabled;
    const sliceAxis = sliceOn ? slice.axis : -1;
    const sliceLo = sliceOn ? slice.center - slice.half : 0;
    const sliceHi = sliceOn ? slice.center + slice.half : 0;
    const sliceSpan = sliceHi - sliceLo;
    const gradientOn = sliceOn && slice.gradient && sliceSpan > 1e-9;
    const lineOpts = sliceOn && slice.lines ? slice.lines : null;
    const linesOn = !!(lineOpts && lineOpts.enabled);
    const linesOnly = !!(linesOn && lineOpts.only);
    const sliceCellW = sliceOn ? (slice.cellWidth || 0.01) : 0.01;
    const lineMinHits = lineOpts ? Math.max(2, Math.floor(lineOpts.minHits || 5)) : 5;
    const lineMaxGap = lineOpts ? Math.max(0, Math.floor(lineOpts.maxGap || 0)) : 0;

    // Optional: draw lattice cube wireframe + axes behind the points.
    if (this.opts.showBox) {
      this._drawCube(ctx, m00, m01, m02, m10, m11, m12, m20, m21, m22,
        d, halfW, halfH, focal, orthoScale, isPerspective, zoom);
    }
    if (this.opts.showAxes) {
      this._drawAxes(ctx, m00, m01, m02, m10, m11, m12, m20, m21, m22,
        d, halfW, halfH, focal, orthoScale, isPerspective, zoom);
    }

    for (const layer of this.layers) {
      if (!layer.visible) continue;
      const pos = layer.positions;
      const N = layer.count;
      if (!N) continue;

      // Convert hex color to [r,g,b].
      const c = hexToRgb(layer.color);
      const baseAlpha = (layer.alpha != null ? layer.alpha : 1) * this.opts.alpha;

      // Fast path: write directly via fillRect for tiny dots; use arc for big ones.
      const useArc = dotPx > 2.5;
      const lineSegments = linesOn
        ? this._detectUlamLines(pos, N, sliceAxis, sliceLo, sliceHi, sliceCellW, lineMinHits, lineMaxGap)
        : [];

      ctx.save();
      if (!linesOnly) {
        for (let i = 0; i < N; i++) {
          const ix = i * 3;
          const x = pos[ix], y = pos[ix + 1], z = pos[ix + 2];

          let gr = -1, gg = -1, gb = -1;
          if (sliceAxis >= 0) {
            const sv = sliceAxis === 0 ? x : sliceAxis === 1 ? y : z;
            if (sv < sliceLo || sv > sliceHi) continue;
            if (gradientOn) {
              // Single continuous scale: white (near slab) → red (far slab),
              // so depth across the stack reads as one monotonic ramp.
              const t = clamp01((sv - sliceLo) / sliceSpan);
              gr = 255;
              gg = Math.round(255 * (1 - t));
              gb = Math.round(255 * (1 - t));
            }
          }

          // World → camera (camera at +z = d looking at origin).
          const cxp = m00 * x + m01 * y + m02 * z;
          const cyp = m10 * x + m11 * y + m12 * z;
          const czp = m20 * x + m21 * y + m22 * z + d;

          if (czp <= 0.05) continue;  // behind / on top of camera

          let sx, sy_, sizeFactor;
          if (isPerspective) {
            sx = halfW + cxp * focal * zoom / czp;
            sy_ = halfH - cyp * focal * zoom / czp;
            sizeFactor = (d / czp);  // close = bigger
          } else {
            sx = halfW + cxp * orthoScale * zoom;
            sy_ = halfH - cyp * orthoScale * zoom;
            sizeFactor = 1.0;
          }

          if (sx < -4 || sx > W + 4 || sy_ < -4 || sy_ > H + 4) continue;

          let a = baseAlpha;
          if (fadeOn) {
            const t = (czp - zNear) / (zFar - zNear);
            const fade = 1 - clamp01(t) * 0.65;
            a *= fade;
          }
          if (a < 0.02) continue;

          const sz = dotPx * sizeFactor;
          const rr = gr >= 0 ? gr : c[0];
          const gg2 = gg >= 0 ? gg : c[1];
          const bb = gb >= 0 ? gb : c[2];
          ctx.fillStyle = `rgba(${rr},${gg2},${bb},${a.toFixed(3)})`;

          if (useArc) {
            ctx.beginPath();
            ctx.arc(sx, sy_, Math.max(0.5, sz * 0.5), 0, Math.PI * 2);
            ctx.fill();
          } else {
            ctx.fillRect(sx - sz * 0.5, sy_ - sz * 0.5, sz, sz);
          }
          visibleCount++;
        }
      }
      if (lineSegments.length) {
        this._drawUlamLines(ctx, lineSegments, c, gradientOn, sliceLo, sliceSpan,
          [m00, m01, m02, m10, m11, m12, m20, m21, m22],
          d, halfW, halfH, focal, orthoScale, isPerspective, zoom);
      }
      ctx.restore();
    }

    this._lastVisibleCount = visibleCount;
  }

  _detectUlamLines(pos, N, sliceAxis, sliceLo, sliceHi, cellW, minHits, maxGap) {
    if (sliceAxis < 0 || !cellW) return [];
    const groups = new Map();

    for (let i = 0; i < N; i++) {
      const ix = i * 3;
      const x = pos[ix], y = pos[ix + 1], z = pos[ix + 2];
      const sv = sliceAxis === 0 ? x : sliceAxis === 1 ? y : z;
      if (sv < sliceLo || sv > sliceHi) continue;

      const gx = Math.round(x / cellW);
      const gy = Math.round(y / cellW);
      const gz = Math.round(z / cellW);
      let u, v, w;
      if (sliceAxis === 0) {        // looking down X: horizontal=Z, vertical=Y
        u = gz; v = gy; w = gx;
      } else if (sliceAxis === 1) { // looking down Y: horizontal=X, vertical=Z
        u = gx; v = gz; w = gy;
      } else {                      // looking down Z: horizontal=X, vertical=Y
        u = gx; v = gy; w = gz;
      }

      let group = groups.get(w);
      if (!group) {
        group = { cells: [], set: new Set(), minU: u, maxU: u, minV: v, maxV: v, w };
        groups.set(w, group);
      }
      const key = gridKey(u, v);
      if (group.set.has(key)) continue;
      group.set.add(key);
      group.cells.push([u, v]);
      if (u < group.minU) group.minU = u;
      if (u > group.maxU) group.maxU = u;
      if (v < group.minV) group.minV = v;
      if (v > group.maxV) group.maxV = v;
    }

    const segments = [];
    const dirs = [[1, 0], [0, 1], [1, 1], [1, -1]];
    const maxSteps = Math.ceil(1 / cellW) + maxGap + 4;

    for (const group of groups.values()) {
      for (const [u, v] of group.cells) {
        for (const [du, dv] of dirs) {
          if (this._hasBackwardHit(group.set, u, v, du, dv, maxGap)) continue;

          let hits = 1;
          let lastU = u, lastV = v;
          let misses = 0;
          for (let step = 1; step <= maxSteps && misses <= maxGap; step++) {
            const nu = u + du * step;
            const nv = v + dv * step;
            if (nu < group.minU - maxGap || nu > group.maxU + maxGap ||
                nv < group.minV - maxGap || nv > group.maxV + maxGap) {
              break;
            }
            if (group.set.has(gridKey(nu, nv))) {
              hits++;
              lastU = nu;
              lastV = nv;
              misses = 0;
            } else {
              misses++;
            }
          }

          const span = Math.max(Math.abs(lastU - u), Math.abs(lastV - v)) + 1;
          if (hits >= minHits && span >= minHits) {
            segments.push({
              a: this._gridToWorld(u, v, group.w, sliceAxis, cellW),
              b: this._gridToWorld(lastU, lastV, group.w, sliceAxis, cellW),
              depth: group.w * cellW,
              hits,
            });
          }
        }
      }
    }

    return segments;
  }

  _hasBackwardHit(set, u, v, du, dv, maxGap) {
    for (let gap = 1; gap <= maxGap + 1; gap++) {
      if (set.has(gridKey(u - du * gap, v - dv * gap))) return true;
    }
    return false;
  }

  _gridToWorld(u, v, w, sliceAxis, cellW) {
    if (sliceAxis === 0) return [w * cellW, v * cellW, u * cellW];
    if (sliceAxis === 1) return [u * cellW, w * cellW, v * cellW];
    return [u * cellW, v * cellW, w * cellW];
  }

  _drawUlamLines(ctx, segments, layerRgb, gradientOn, sliceLo, sliceSpan,
                 m, d, halfW, halfH, focal, orthoScale, isPersp, zoom) {
    ctx.save();
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';

    // A subtle dark backing keeps extracted structures readable on dense dots.
    ctx.lineWidth = 3.2 * this.dpr;
    ctx.strokeStyle = 'rgba(0,0,0,0.45)';
    for (const seg of segments) {
      const pa = this._project(seg.a[0], seg.a[1], seg.a[2], m, d, halfW, halfH, focal, orthoScale, isPersp, zoom);
      const pb = this._project(seg.b[0], seg.b[1], seg.b[2], m, d, halfW, halfH, focal, orthoScale, isPersp, zoom);
      if (!pa || !pb) continue;
      ctx.beginPath();
      ctx.moveTo(pa[0], pa[1]);
      ctx.lineTo(pb[0], pb[1]);
      ctx.stroke();
    }

    ctx.lineWidth = 1.35 * this.dpr;
    for (const seg of segments) {
      const pa = this._project(seg.a[0], seg.a[1], seg.a[2], m, d, halfW, halfH, focal, orthoScale, isPersp, zoom);
      const pb = this._project(seg.b[0], seg.b[1], seg.b[2], m, d, halfW, halfH, focal, orthoScale, isPersp, zoom);
      if (!pa || !pb) continue;
      if (gradientOn && sliceSpan > 1e-9) {
        const t = clamp01((seg.depth - sliceLo) / sliceSpan);
        const gb = Math.round(255 * (1 - t));
        ctx.strokeStyle = `rgba(255,${gb},${gb},0.82)`;
      } else {
        ctx.strokeStyle = `rgba(${layerRgb[0]},${layerRgb[1]},${layerRgb[2]},0.82)`;
      }
      ctx.beginPath();
      ctx.moveTo(pa[0], pa[1]);
      ctx.lineTo(pb[0], pb[1]);
      ctx.stroke();
    }
    ctx.restore();
  }

  _project(x, y, z, m, d, halfW, halfH, focal, orthoScale, isPersp, zoom) {
    const [m00, m01, m02, m10, m11, m12, m20, m21, m22] = m;
    const cx = m00 * x + m01 * y + m02 * z;
    const cy = m10 * x + m11 * y + m12 * z;
    const cz = m20 * x + m21 * y + m22 * z + d;
    if (cz <= 0.05) return null;
    if (isPersp) {
      return [halfW + cx * focal * zoom / cz, halfH - cy * focal * zoom / cz, cz];
    }
    return [halfW + cx * orthoScale * zoom, halfH - cy * orthoScale * zoom, cz];
  }

  _drawCube(ctx, m00, m01, m02, m10, m11, m12, m20, m21, m22,
            d, halfW, halfH, focal, orthoScale, isPersp, zoom) {
    const m = [m00, m01, m02, m10, m11, m12, m20, m21, m22];
    const s = 0.5;
    const corners = [
      [-s, -s, -s], [ s, -s, -s], [ s,  s, -s], [-s,  s, -s],
      [-s, -s,  s], [ s, -s,  s], [ s,  s,  s], [-s,  s,  s],
    ];
    const edges = [
      [0,1],[1,2],[2,3],[3,0],
      [4,5],[5,6],[6,7],[7,4],
      [0,4],[1,5],[2,6],[3,7],
    ];
    const proj = corners.map((c) =>
      this._project(c[0], c[1], c[2], m, d, halfW, halfH, focal, orthoScale, isPersp, zoom));
    ctx.save();
    ctx.strokeStyle = 'rgba(120,140,170,0.35)';
    ctx.lineWidth = 1 * this.dpr;
    for (const [a, b] of edges) {
      const pa = proj[a], pb = proj[b];
      if (!pa || !pb) continue;
      ctx.beginPath();
      ctx.moveTo(pa[0], pa[1]);
      ctx.lineTo(pb[0], pb[1]);
      ctx.stroke();
    }
    ctx.restore();
  }

  _drawAxes(ctx, m00, m01, m02, m10, m11, m12, m20, m21, m22,
            d, halfW, halfH, focal, orthoScale, isPersp, zoom) {
    const m = [m00, m01, m02, m10, m11, m12, m20, m21, m22];
    const o = this._project(0, 0, 0, m, d, halfW, halfH, focal, orthoScale, isPersp, zoom);
    if (!o) return;
    const axes = [
      [[0.6, 0, 0], 'rgba(248,81,73,0.9)'],
      [[0, 0.6, 0], 'rgba(63,185,80,0.9)'],
      [[0, 0, 0.6], 'rgba(88,166,255,0.9)'],
    ];
    ctx.save();
    ctx.lineWidth = 1.5 * this.dpr;
    for (const [v, col] of axes) {
      const p = this._project(v[0], v[1], v[2], m, d, halfW, halfH, focal, orthoScale, isPersp, zoom);
      if (!p) continue;
      ctx.strokeStyle = col;
      ctx.beginPath();
      ctx.moveTo(o[0], o[1]);
      ctx.lineTo(p[0], p[1]);
      ctx.stroke();
    }
    ctx.restore();
  }
}

function clamp01(x) { return x < 0 ? 0 : x > 1 ? 1 : x; }

function gridKey(u, v) { return `${u},${v}`; }

function hexToRgb(hex) {
  let h = hex.replace('#', '');
  if (h.length === 3) h = h.split('').map((c) => c + c).join('');
  const v = parseInt(h, 16);
  return [(v >> 16) & 255, (v >> 8) & 255, v & 255];
}
