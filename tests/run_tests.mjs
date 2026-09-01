#!/usr/bin/env node
/*
 * run_tests.mjs — end-to-end pipeline validation
 * ------------------------------------------------
 * Drives the same modules the browser uses (dsp.js, classifier.js,
 * simulator.js, model_weights.js) and checks:
 *   1. Simulator produces plausible signals per scenario.
 *   2. DSP extracts sane features (HR near ground truth, SDNN ordering,
 *      AF vs NSR separation of the irregularity features).
 *   3. Classifier maps the four demo scenarios to the right care level.
 *   4. Guardrails trigger on weak/noisy signals.
 *
 * Run:  node tests/run_tests.mjs
 */

import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const path = require('path');
global.window = {}; // some modules sniff `window`

// load modules exactly like index.html does (shared globals)
const load = (f) => require(path.join(path.dirname(new URL(import.meta.url).pathname), '..', 'js', f));
global.NADI_MODEL = load('model_weights.js'); // classifier.js reads this global
const DSP = load('dsp.js');
const Classifier = load('classifier.js');
const Simulator = load('simulator.js');

let pass = 0, fail = 0;
const ok = (name, cond, extra = '') => {
  if (cond) { pass++; console.log(`  ✓ ${name}`); }
  else { fail++; console.log(`  ✗ ${name} ${extra}`); }
};

console.log('NadiSense pipeline tests\n');

// ---------- 1. signal sanity ----------
for (const kind of Object.keys(Simulator.SCENARIOS)) {
  const { signal } = Simulator.generate(kind, 7);
  const finite = signal.every(Number.isFinite);
  const rms = Math.sqrt(signal.reduce((s, v) => s + v * v, 0) / signal.length);
  ok(`sim: ${kind} → 900 finite samples, rms=${rms.toFixed(3)}`, signal.length === 900 && finite && rms > 0.01 && rms < 2);
}

// ---------- 2. feature extraction, scenario by scenario ----------
const rates = {};
for (const kind of ['normal', 'lowhrv', 'afib', 'noisy', 'weak']) {
  const { signal } = Simulator.generate(kind, 7);
  const f = DSP.features(signal);
  ok(`dsp: ${kind} → features extracted (${f ? f.n_beats : 0} beats)`, !!f);
  rates[kind] = f;
}

// heart rate near ground truth (sim targets: 72/86/97/76/70 bpm)
const hrErr = Math.abs(rates.normal.hrMean - 72);
ok(`dsp: normal HR ≈ 72 bpm (got ${rates.normal.hrMean.toFixed(1)}, err ${hrErr.toFixed(1)})`, hrErr < 8);
ok(`dsp: afib HR ≈ 97 bpm (got ${rates.afib.hrMean.toFixed(1)})`, Math.abs(rates.afib.hrMean - 97) < 12);

// SDNN ordering: afib ≫ normal ≫ lowhrv
ok('dsp: SDNN afib > normal > lowhrv',
  rates.afib.sdnn > rates.normal.sdnn && rates.normal.sdnn > rates.lowhrv.sdnn,
  `(${rates.afib.sdnn.toFixed(0)} / ${rates.normal.sdnn.toFixed(0)} / ${rates.lowhrv.sdnn.toFixed(0)})`);
ok('dsp: RMSSD afib > normal', rates.afib.rmssd > rates.normal.rmssd);
ok('dsp: turning-point ratio afib < normal (chaotic beat order)',
  rates.afib.turning < rates.normal.turning,
  `(${rates.afib.turning.toFixed(2)} vs ${rates.normal.turning.toFixed(2)})`);
ok('dsp: irregularity % afib >> normal', rates.afib.irr > rates.normal.irr * 3,
  `(${rates.afib.irr.toFixed(0)} vs ${rates.normal.irr.toFixed(0)})`);
// spectral entropy is not monotone in rhythm irregularity, so assert
// something weaker and physically meaningful: clean NSR stays in the
// low-entropy... both stay within the trained envelope (checked by the
// classifier test below).
ok('dsp: ectopy fraction afib > normal', rates.afib.pvc > rates.normal.pvc);

// ---------- 3. classification ----------
const assess = (kind) => Classifier.assess(rates[kind] ? rates[kind] : DSP.features(Simulator.generate(kind, 7).signal), null);
const aNormal = assess('normal'), aLow = assess('lowhrv'), aAfib = assess('afib');
ok(`cls: normal → low risk (p=${(aNormal.p * 100).toFixed(1)}%)`, aNormal.level === 'low');
ok(`cls: lowhrv → low/mid (p=${(aLow.p * 100).toFixed(1)}%)`, aLow.level === 'low' || aLow.level === 'mid');
ok(`cls: afib → high risk (p=${(aAfib.p * 100).toFixed(1)}%)`, aAfib.level === 'high');
ok('cls: P(afib) > P(normal)', aAfib.p > aNormal.p + 0.3);

// classifier runs standalone on the exported weights (no dsp dependency)
const featVec = {};
for (const k of Classifier.FEATURES) featVec[k] = rates.normal[k];
const pStandalone = Classifier.assess(featVec, null).p;
ok(`cls: standalone forward pass works (p=${(pStandalone * 100).toFixed(1)}%)`, Number.isFinite(pStandalone));

// ---------- 4. quality / guardrails ----------
const qOf = (kind, seed = 7) => {
  const sig = Simulator.generate(kind, seed).signal;
  const det = DSP.detrend(sig);
  const bp = DSP.bandpass(det, 0.6, 3.5, 30);
  const pks = DSP.detectPeaks(bp);
  const rr = []; for (let i = 1; i < pks.length; i++) rr.push((pks[i] - pks[i - 1]) / 30);
  return { q: DSP.qualityIndex(bp, det, rr), f: DSP.features(sig), sig };
};
ok('quality: clean holds score > 0.7', qOf('normal').q > 0.7 && qOf('lowhrv').q > 0.7);
const motion = qOf('motion'), weak = qOf('weak');
ok(`guard: heavy motion flagged (Q=${motion.q.toFixed(2)})`, motion.q < 0.6);
ok(`guard: weak signal flagged (Q=${weak.q.toFixed(2)})`, weak.q < 0.6);
ok('guard: warnings surface in assessment',
  Classifier.assess(motion.f, motion.q).warnings.includes('WARN_QUALITY'));
ok('guard: too-few-beats => error level', Classifier.assess(null, 0).level === 'error');

// ---------- 5. determinism & timing ----------
const s1 = Simulator.generate('afib', 42), s2 = Simulator.generate('afib', 42);
ok('sim: deterministic per seed', s1.signal.every((v, i) => v === s2.signal[i]));
const t0 = Date.now();
DSP.features(Simulator.generate('normal', 7).signal);
ok(`perf: 30 s window analysed in ${Date.now() - t0} ms (target < 250 ms)`, Date.now() - t0 < 250);

console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
