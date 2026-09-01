/*
 * simulator.js — SYNTHETIC pulse-signal generator (demo/test mode only)
 * ---------------------------------------------------------------------
 * Generates a 30 s photoplethysmogram-like waveform with physiological
 * beat dynamics. It exists so the pipeline can be demonstrated on any
 * laptop (judges' rooms rarely have a finger + camera setup), and so
 * the automated tests (tests/run_tests.mjs) have a ground truth.
 *
 * IMPORTANT: this is a *test fixture*, not product functionality. The
 * shipped capture path is the phone camera (ppgcamera.js). The signal
 * flows through the exact same DSP + classifier as real capture.
 */

const Simulator = (() => {
  'use strict';
  const FS = 30;

  // one-beat template: systolic peak, dicrotic notch, ~0.9 s
  const TPL = (() => {
    const n = Math.floor(0.75 * FS), tpl = new Float64Array(n);
    for (let i = 0; i < n; i++) {
      const t = i / FS;
      tpl[i] = 0.9 * Math.exp(-0.5 * Math.pow((t - 0.22) / 0.055, 2))
             + 0.35 * Math.exp(-0.5 * Math.pow((t - 0.50) / 0.070, 2))
             + 0.08 * Math.exp(-0.5 * Math.pow((t - 0.62) / 0.045, 2));
    }
    const mx = Math.max(...tpl);
    return tpl.map(v => v / mx);
  })();

  function mulberry32(a) {
    return function () {
      a |= 0; a = (a + 0x6D2B79F5) | 0;
      let t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  const SCENARIOS = {
    normal:  { label: 'Normal sinus rhythm', hr: 72, sdnn: 46, rho: 0.35, af: false, noise: 0.012 },
    lowhrv:  { label: 'Low HRV (stressed / risk)', hr: 86, sdnn: 21, rho: 0.30, af: false, noise: 0.013 },
    afib:    { label: 'Atrial fibrillation-like', hr: 97, sdnn: 158, rho: 0.05, af: true, noise: 0.012 },
    noisy:   { label: 'With motion artifact', hr: 76, sdnn: 52, rho: 0.30, af: false, noise: 0.070 },
    weak:    { label: 'Weak/flat signal', hr: 70, sdnn: 44, rho: 0.35, af: false, noise: 0.040, gain: 0.18 },
    motion:  { label: 'Heavy motion (cannot hold still)', hr: 74, sdnn: 55, rho: 0.30, af: false, noise: 0.120, gain: 0.5, wander: 0.55 },
  };

  function genRR(cfg, rng, n) {
    const base = 60 / cfg.hr;
    const rr = new Float64Array(n);
    const raw = new Float64Array(n);
    for (let i = 0; i < n; i++) raw[i] = (rng() * 2 - 1) * 0.9 + (rng() * 2 - 1) * 0.9;
    if (!cfg.af) {
      for (let i = 0; i < n; i++) {
        const phase = 2 * Math.PI * (0.18 + 0.1 * rng()) * i / (base * 18);
        rr[i] = base * (1 + 0.022 * Math.sin(phase)) + raw[i];
      }
      const m = rr.reduce((s, v) => s + v, 0) / n;
      const d = [], out = new Float64Array(n);
      for (let i = 0; i < n; i++) d.push(rr[i] - m);
      out[0] = d[0];
      for (let i = 1; i < n; i++) out[i] = cfg.rho * out[i - 1] + d[i];
      for (let i = 0; i < n; i++) rr[i] = m + out[i] * (0.55 + 0.45 * rng());
    } else {
      for (let i = 0; i < n; i++) rr[i] = base + 0.55 * raw[i] * 0.9;
      for (let i = 0; i < n; i++) if (rng() < 0.08) rr[i] += (rng() * 2 - 1) * 0.9 * base;
    }
    // rescale sdnn to target (ms), then recentre the finite-sample mean
    // on the target rate (the AR(1) pass drifts it otherwise)
    let m = rr.reduce((s, v) => s + v, 0) / n;
    let sd = Math.sqrt(rr.reduce((s, v) => s + (v - m) * (v - m), 0) / n) || 1e-9;
    for (let i = 0; i < n; i++) rr[i] = m + (rr[i] - m) * (cfg.sdnn / 1000 / sd);
    m = rr.reduce((s, v) => s + v, 0) / n;
    for (let i = 0; i < n; i++) rr[i] = base + (rr[i] - m);
    for (let i = 0; i < n; i++) rr[i] = Math.max(0.30, Math.min(1.45, rr[i]));
    return rr;
  }

  /*
   * Generate the full 30 s waveform.
   * kind: one of the SCENARIOS keys. Returns { signal: Float64Array, fs }.
   */
  function generate(kind = 'normal', seed = 7) {
    const cfg = SCENARIOS[kind] || SCENARIOS.normal;
    const rng = mulberry32(seed * 2654435761 ^ 0x9e3779b9);
    const n = Math.floor(30 * FS);
    const sig = new Float64Array(n);
    const rr = genRR(cfg, rng, 140);
    const tm = [0];
    for (let i = 1; i < rr.length; i++) tm.push(tm[i - 1] + rr[i]);
    for (const t0 of tm) {
      const i0 = Math.floor(t0 * FS);
      for (let k = 0; k < TPL.length && i0 + k < n; k++) {
        sig[i0 + k] += TPL[k] * (0.9 + 0.1 * rng());
      }
    }
    const gain = cfg.gain || 1.0;
    for (let i = 0; i < n; i++) {
      const t = i / FS;
      const wander = 0.035 * Math.sin(2 * Math.PI * 0.14 * t + rng() * 6)
                   + (cfg.wander || 0.16) * Math.sin(2 * Math.PI * 0.30 * t + rng() * 6);
      const tremor = 0.02 * Math.sin(2 * Math.PI * 9 * t + rng() * 6)
                   * (0.5 + 0.5 * Math.sin(2 * Math.PI * 0.11 * t));
      sig[i] = sig[i] * gain + wander + tremor + (rng() * 2 - 1) * cfg.noise;
    }
    return { signal: sig, fs: FS, kind, label: cfg.label };
  }

  return { generate, SCENARIOS, FS };
})();

if (typeof module !== 'undefined') module.exports = Simulator;
