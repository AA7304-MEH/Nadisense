/*
 * dsp.js — signal processing kernel for NadiSense
 * -------------------------------------------------
 * Pure-JS port of the DSP pipeline used to train the model
 * (see tools/train_mlp.py). Every step here is mirrored 1:1 with the
 * Python reference so the deployed features match training features.
 *
 * Pipeline: detrend -> zero-phase bandpass (FFT) -> systolic peak pick
 * -> RR intervals -> 12 HRV / irregularity features.
 *
 * (Features used: HR, SDNN, RMSSD, pNN50, SD1, SD2, SD1/SD2, LF/HF,
 *  spectral entropy, turning-point ratio, irregularity %, PVC-like
 *  beats, sample entropy.)
 */

const DSP = (() => {
  'use strict';

  const FS = 30.0; // uniform samples per second after resampling

  /* ------------------------- FFT (iterative radix-2) ------------------- */
  function fft(re, im) {
    const n = re.length;
    if (n <= 1) return;
    // bit-reversal permutation
    for (let i = 1, j = 0; i < n; i++) {
      let bit = n >> 1;
      for (; j & bit; bit >>= 1) j ^= bit;
      j ^= bit;
      if (i < j) {
        const tr = re[i]; re[i] = re[j]; re[j] = tr;
        const ti = im[i]; im[i] = im[j]; im[j] = ti;
      }
    }
    for (let len = 2; len <= n; len <<= 1) {
      const ang = -2 * Math.PI / len;
      const wr = Math.cos(ang), wi = Math.sin(ang);
      for (let i = 0; i < n; i += len) {
        let cr = 1, ci = 0;
        for (let k = 0; k < len / 2; k++) {
          const ur = re[i + k], ui = im[i + k];
          const vr = re[i + k + len / 2] * cr - im[i + k + len / 2] * ci;
          const vi = re[i + k + len / 2] * ci + im[i + k + len / 2] * cr;
          re[i + k] = ur + vr;           im[i + k] = ui + vi;
          re[i + k + len / 2] = ur - vr; im[i + k + len / 2] = ui - vi;
          const ncr = cr * wr - ci * wi, nci = cr * wi + ci * wr;
          cr = ncr; ci = nci;
        }
      }
    }
  }

  /* Inverse FFT via conjugation: x = (1/N) conj(FFT(conj(X))). */
  function ifft(re, im) {
    const n = re.length;
    for (let i = 0; i < n; i++) im[i] = -im[i];
    fft(re, im);
    for (let i = 0; i < n; i++) { im[i] = -im[i]; re[i] /= n; im[i] /= n; }
  }

  function nextPow2(n) {
    let m = 1;
    while (m < n) m <<= 1;
    return m;
  }

  /* Zero-phase bandpass via FFT with soft (raised-cosine) edges. */
  function bandpass(x, lo, hi, fSample) {
    const n = x.length;
    const N = nextPow2(Math.max(n, 1));
    const re = new Float64Array(N), im = new Float64Array(N);
    re.set(x);
    fft(re, im);
    const loF = Math.max(lo, 1e-3), hiF = Math.min(hi, fSample / 2 - 1e-3);
    const width = 0.20; // transition bands sit OUTSIDE the passband
    for (let k = 0; k <= N / 2; k++) {
      const f = k * fSample / N;
      let m = (f >= loF && f <= hiF) ? 1 : 0;
      if (f >= loF - width && f < loF) {
        m = 0.5 * (1 - Math.cos(Math.PI * (f - (loF - width)) / width));
      }
      if (f > hiF && f <= hiF + width) {
        m = 0.5 * (1 + Math.cos(Math.PI * (f - hiF) / width));
      }
      re[k] *= m; im[k] *= m;
      if (k > 0 && k < N / 2) { re[N - k] *= m; im[N - k] *= m; }
    }
    const out = new Float64Array(n);
    const full = new Float64Array(N);
    full.set(Float64Array.from(re));
    const fim = Float64Array.from(im);
    ifft(full, fim);
    for (let i = 0; i < n; i++) out[i] = full[i];
    return out;
  }

  function detrend(x) {
    const n = x.length;
    let st = 0, stt = 0, sx = 0, sxt = 0;
    for (let i = 0; i < n; i++) {
      st += i; stt += i * i; sx += x[i]; sxt += x[i] * i;
    }
    const den = n * stt - st * st;
    if (den === 0) return Float64Array.from(x);
    const b = (n * sxt - st * sx) / den;
    const a = (sx - b * st) / n;
    const out = new Float64Array(n);
    for (let i = 0; i < n; i++) out[i] = x[i] - (a + b * i);
    return out;
  }

  /* Linear-interp resample of (times, values) onto a uniform grid. */
  function resampleUniform(times, values, outLen, span) {
    const out = new Float64Array(outLen);
    let j = 1;
    for (let i = 0; i < outLen; i++) {
      const g = span * i / (outLen || 1);
      while (j < times.length - 1 && times[j] < g) j++;
      const t0 = times[j - 1], t1 = times[j];
      const v0 = values[j - 1], v1 = values[j];
      const d = Math.max(t1 - t0, 1e-9);
      out[i] = v0 + (v1 - v0) * ((g - t0) / d);
    }
    return out;
  }

  /* Amplitude-ranked peak picker with a refractory window. */
  function findPeaks(x, minDistSec, thrQuantile) {
    const n = x.length;
    const minSamp = Math.max(1, Math.floor(minDistSec * FS));
    const cand = [];
    for (let i = 1; i < n - 1; i++) {
      if (x[i] >= x[i - 1] && x[i] > x[i + 1]) cand.push(i);
    }
    if (cand.length === 0) return [];
    const amps = cand.map(i => x[i]);
    const sorted = amps.slice().sort((a, b) => a - b);
    const thr = sorted[Math.floor(thrQuantile / 100 * (sorted.length - 1))] * 0.6;
    const order = cand.map((c, idx) => idx).sort((a, b) => amps[b] - amps[a]);
    const kept = [];
    for (const idx of order) {
      const i = cand[idx];
      if (amps[idx] < thr) break;
      if (kept.every(k => Math.abs(k - i) >= minSamp)) kept.push(i);
    }
    kept.sort((a, b) => a - b);
    return kept;
  }

  function rrFromPeaks(peaks) {
    const rr = [];
    for (let i = 1; i < peaks.length; i++) {
      const v = (peaks[i] - peaks[i - 1]) / FS;
      if (v >= 0.30 && v <= 1.60) rr.push(v);
    }
    return rr;
  }

  /*
   * Adaptive-refractory peak detector (two passes). Pass 1 finds the
   * strong systolic peaks; pass 2 re-runs with a refractory derived
   * from the median RR, which drops dicrotic-notch second peaks.
   * Mirrors tools/train_mlp.py::detect_peaks exactly.
   */
  function detectPeaks(x) {
    let minDist = 0.30;
    let pk = findPeaks(x, minDist, 55);
    const rr = rrFromPeaks(pk);
    if (rr.length >= 4) {
      const med = rr.slice().sort((a, b) => a - b)[rr.length >> 1];
      minDist = Math.max(0.35, Math.min(1.0, 0.65 * med));
      pk = findPeaks(x, minDist, 55);
    }
    return pk;
  }

  function mean(a) { return a.reduce((s, v) => s + v, 0) / (a.length || 1); }
  function std(a) {
    if (a.length < 2) return 0;
    const m = mean(a);
    return Math.sqrt(a.reduce((s, v) => s + (v - m) * (v - m), 0) / a.length);
  }

  /* Sample entropy (m=2, r = 0.2*SDNN) — same definition as the python side. */
  function sampleEntropy(rr, m, r) {
    const n = rr.length;
    if (n < m + 2 || r <= 0) return 0;
    function count(mm) {
      let hits = 0, total = 0;
      for (let i = 0; i <= n - mm; i++) {
        for (let j = 0; j <= n - mm; j++) {
          if (i === j) continue;
          let d = 0;
          for (let k = 0; k < mm; k++) d = Math.max(d, Math.abs(rr[i + k] - rr[j + k]));
          if (d < r) hits++;
          total++;
        }
      }
      return hits / total;
    }
    const B = count(2) + 1e-12, A = count(3) + 1e-12;
    return B > 1e-12 ? -Math.log(A / B) : 0;
  }

  /*
   * Main feature extractor. Input: Float64Array of ~30 s raw PPG (uniform
   * FS). Returns the 13-feature object, or null if the signal is unusable.
   */
  function features(raw) {
    if (!raw || raw.length < 8 * FS) return null;
    const det = detrend(raw);
    const bp = bandpass(det, 0.6, 3.5, FS);
    const peaks = detectPeaks(bp);
    const rr = rrFromPeaks(peaks);
    if (rr.length < 8) return null;

    const hr = 60 / (rr.slice().sort((a, b) => a - b)[rr.length >> 1]);
    const mrr = mean(rr);
    const sdnn = std(rr) * 1000;
    const drr = [];
    for (let i = 1; i < rr.length; i++) drr.push((rr[i] - rr[i - 1]) * 1000);
    const rmssd = Math.sqrt(mean(drr.map(d => d * d))) || 0;
    const pnn50 = 100 * drr.filter(d => Math.abs(d) > 50).length / (drr.length || 1);

    // Poincare (SD1/SD2 from adjacent-beat difference and sum series)
    const n1 = rr.length - 1;
    const diffs = [], sums = [];
    for (let i = 0; i < n1; i++) { diffs.push(rr[i] - rr[i + 1]); sums.push(rr[i] + rr[i + 1]); }
    const sdDiff = std(diffs), sdSum = std(sums);
    const sd1 = sdDiff / Math.SQRT2 * 1000;
    const sd2 = sdSum / Math.SQRT2 * 1000;
    const sd1sd2 = sd2 > 1e-9 ? sd1 / sd2 : 0;

    // tachogram -> LF/HF + spectral entropy (resample to 4 Hz)
    const tm = [0];
    for (let i = 1; i < rr.length; i++) tm.push(tm[i - 1] + rr[i]);
    const span = tm[tm.length - 1];
    const outLen = Math.max(16, Math.floor(span * 4));
    const tach = resampleUniform(tm, rr, outLen, span);
    const tm0 = mean(tach);
    for (let i = 0; i < tach.length; i++) tach[i] -= tm0;
    const N2 = Math.min(nextPow2(tach.length), 512);
    const re = new Float64Array(N2), im = new Float64Array(N2);
    re.set(tach.slice(0, N2));
    fft(re, im);
    const spec = [];
    for (let k = 0; k <= N2 / 2; k++) spec.push(re[k] * re[k] + im[k] * im[k]);
    let lf = 0, hf = 0, band = 0, totEnt = 0;
    const bandStart = 0.04, bandEnd = 0.40;
    for (let k = 0; k < spec.length; k++) {
      const f = k * 4 / N2;
      const v = spec[k];
      if (f >= bandStart && f <= bandEnd) { band += v; totEnt++; }
      if (f >= bandStart && f < 0.15) lf += v;
      if (f >= 0.15 && f <= bandEnd) hf += v;
    }
    const lf_hf = hf > 1e-9 ? lf / hf : 0;
    let pArr = [];
    for (let k = 0; k < spec.length; k++) {
      const f = k * 4 / N2;
      if (f >= bandStart && f <= bandEnd && band > 0) pArr.push(spec[k] / band);
    }
    let s_ent = 0;
    for (const p of pArr) {
      if (p > 0) s_ent -= p * Math.log(p);
    }
    s_ent = pArr.length ? s_ent / Math.log(pArr.length) : 0;

    // beat pattern irregularity
    let turns = 0, tot = 0;
    for (let i = 1; i + 1 < rr.length; i++) {
      if ((rr[i] > rr[i - 1]) !== (rr[i] > rr[i + 1])) turns++;
      tot++;
    }
    const turning = tot ? turns / tot : 0.5;
    let absSum = 0;
    for (const d of drr) absSum += Math.abs(d);
    const irr = mrr > 0 ? (absSum / (drr.length || 1)) / mrr * 100 : 0;
    const med = rr.slice().sort((a, b) => a - b)[rr.length >> 1];
    let pvcCount = 0;
    for (const v of rr) if (Math.abs(v - med) / med > 0.22) pvcCount++;
    const pvc = pvcCount / rr.length;
    const sampen = sampleEntropy(rr, 2, 0.2 * (sdnn / 1000));

    return {
      hrMean: hr, sdnn, rmssd, pnn50, sd1, sd2, sd1sd2,
      lf_hf, s_ent, turning, irr, pvc, sampen,
      n_beats: rr.length,
      // extras for the UI / guards
      peaks, rr, bp, det
    };
  }

  /*
   * Signal-quality index in [0,1] — blend of spectral band ratio and
   * beat-interval regularity. A fingertip with motion artifact gives a
   * low band ratio; a clean but tremorous hold gives irregular RRs; both
   * pull the index down and trigger the "retake" guardrail.
   */
  function qualityIndex(bp, det, rr) {
    if (!bp || !det || det.length < 32) return 0;
    const vDet = std(det), vBp = std(bp);
    // contrast: pulse-band (0.6-3.5 Hz) power vs out-of-band power
    // (baseline wander, tremor, broadband noise) -- logistic-scaled
    const br2 = vBp * vBp / Math.max(vDet * vDet - vBp * vBp, 1e-12);
    const bandRatio = br2 / (br2 + 0.7);
    let reg = 0;
    if (rr && rr.length >= 4) {
      const med = rr.slice().sort((a, b) => a - b)[rr.length >> 1];
      let inBand = 0;
      for (const v of rr) if (v >= 0.75 * med && v <= 1.35 * med) inBand++;
      reg = inBand / rr.length;
    }
    return Math.max(0, Math.min(1, 0.6 * bandRatio + 0.4 * reg));
  }

  return { FS, features, findPeaks, detectPeaks, bandpass, detrend, resampleUniform,
           qualityIndex, fft, nextPow2, mean, std };
})();

if (typeof module !== 'undefined') module.exports = DSP;
