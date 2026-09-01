/*
 * classifier.js — on-device inference + care-level logic
 * -------------------------------------------------------
 * Feeds the 13 DSP features through the tiny MLP exported by
 * tools/train_mlp.py (js/model_weights.js), then maps the probability
 * to a care level with rule-based guardrails (signal quality, heart
 * rate range, beat count). Kept deliberately small so it runs on a
 * ₹6,000 Android phone during the zonal/final demos.
 */

const Classifier = (() => {
  'use strict';

  const M = (typeof NADI_MODEL !== 'undefined') ? NADI_MODEL : null;
  const FEATURES = M ? M.features : [];
  const M2F = FEATURES.length;

  function stdize(feat) {
    const x = new Float64Array(FEATURES.length);
    for (let i = 0; i < FEATURES.length; i++) {
      const z = (feat[FEATURES[i]] - M.mean[i]) / M.scale[i];
      x[i] = Math.max(-3, Math.min(3, z));   // winsorise (matches training)
    }
    return x;
  }

  /* Forward pass: 13 -> 20 -> 10 -> 1 (tanh/tanh/sigmoid). */
  function forward(x) {
    const a1 = new Float64Array(20), a2 = new Float64Array(10);
    for (let j = 0; j < 20; j++) {
      let s = M.b1[j];
      for (let i = 0; i < M2F; i++) s += x[i] * M.W1[j * M2F + i];
      a1[j] = Math.tanh(s);
    }
    for (let j = 0; j < 10; j++) {
      let s = M.b2[j];
      for (let i = 0; i < 20; i++) s += a1[i] * M.W2[j * 20 + i];
      a2[j] = Math.tanh(s);
    }
    let s = M.b3[0];
    for (let i = 0; i < 10; i++) s += a2[i] * M.W3[i];
    return 1 / (1 + Math.exp(-s));
  }

  /*
   * feat: object from DSP.features()
   * Returns { p, level, warnings[], hr, notes[] }
   * level: 'low' | 'mid' | 'high'
   */
  function assess(feat, quality) {
    const warnings = [], notes = [];

    if (!feat || feat.n_beats < 8) {
      return { p: null, level: 'error', warnings: ['WARN_FEW_BEATS'], hr: null, notes: [] };
    }

    const p = M ? forward(stdize(feat)) : 0.5;

    // ---- guardrails -------------------------------------------------
    if (feat.hrMean < 40 || feat.hrMean > 180) warnings.push('WARN_HR_RANGE');
    if (feat.n_beats < 12) warnings.push('WARN_SHORT');
    if (quality !== null && quality < 0.6) warnings.push('WARN_QUALITY');
    if (feat.pvc > 0.18) notes.push('NOTE_ECTOPIC');

    let level;
    if (p < 0.35) level = 'low';
    else if (p < 0.65) level = 'mid';
    else level = 'high';

    if (feat.sdnn < 30 && p < 0.35) notes.push('NOTE_LOW_HRV');

    return { p, level, warnings, hr: feat.hrMean, notes: notes.concat(warnings) };
  }

  return { assess, stdize, forward, FEATURES };
})();

if (typeof module !== 'undefined') module.exports = Classifier;
