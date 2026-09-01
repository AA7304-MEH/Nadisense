#!/usr/bin/env node
/*
 * build_standalone.mjs — bundles NadiSense into ONE self-contained HTML
 * file (no server, no network, works from a USB stick). This is the file
 * we demo on the zonal/final laptops.
 *
 * Run:  node tools/build_standalone.mjs   →  ../deliverables/nadi.html
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const root = path.join(path.dirname(fileURLToPath(import.meta.url)), '..');
let html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');

const css = fs.readFileSync(path.join(root, 'css', 'style.css'), 'utf8');
const scripts = [
  'js/model_weights.js',
  'js/dsp.js',
  'js/classifier.js',
  'js/simulator.js',
  'js/ppgcamera.js',
  'js/i18n.js',
  'js/asr.js',
  'js/app.js',
].map((f) => fs.readFileSync(path.join(root, f), 'utf8'));

// external <link rel="stylesheet"> -> inline <style>
html = html.replace(
  /<link rel="stylesheet" href="css\/style\.css">/,
  () => `<style>\n${css}\n</style>`
);

// external <script src="..."> -> inline <script>
const scriptTags = [...html.matchAll(/<script src="(js\/[^"]+)"><\/script>/g)];
if (scriptTags.length !== scripts.length) {
  console.error('script list mismatch:', scriptTags.map((m) => m[1]));
  process.exit(1);
}
for (const [i, tag] of scriptTags.entries()) {
  html = html.replace(tag[0], () => `<script>\n${scripts[i]}\n</script>`);
}

const out = path.join(root, '..', 'deliverables', 'nadi.html');
fs.mkdirSync(path.dirname(out), { recursive: true });
fs.writeFileSync(out, html);
console.log(`wrote ${out} (${(fs.statSync(out).size / 1024).toFixed(0)} KB, single file)`);
