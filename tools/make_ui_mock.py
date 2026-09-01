#!/usr/bin/env python3
"""mock_ui.py — faithful PIL mockup of the NadiSense result screen
(uses the app's actual colors/layout so the deck matches the demo)."""
import os, sys, json, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont

def font(sz, bold=True):
    base = '/usr/share/fonts/truetype/dejavu/'
    name = 'DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf'
    return ImageFont.truetype(base + name, sz)

def js_get(kind, seed=7):
    code = f"""
const DSP = require('./js/dsp.js');
const Sim = require('./js/simulator.js');
const sig = Sim.generate('{kind}', {seed}).signal;
const f = DSP.features(sig);
console.log(JSON.stringify({{rr:f.rr, hr:f.hrMean, sdnn:f.sdnn, rmssd:f.rmssd, pnn50:f.pnn50, sd1sd2:f.sd1sd2, lfhf:f.lf_hf, n:f.n_beats, sig:Array.from(sig)}}));
"""
    r = subprocess.run(['node', '-e', code], capture_output=True, text=True)
    return json.loads(r.stdout)

W, H = 1500, 980
BG = (7, 24, 34); CARD = (14, 40, 56); LINE = (29, 65, 86)
TXT = (232, 241, 246); MUTED = (147, 169, 184); TEAL = (45, 212, 191)
TEALD = (15, 118, 110); GREEN = (34, 197, 94); RED = (239, 68, 68); AMBER = (245, 158, 11)

img = Image.new('RGB', (W, H), BG)
d = ImageDraw.Draw(img)

# header
d.rounded_rectangle([24, 20, W - 24, 108], 20, fill=CARD)
d.ellipse([44, 38, 92, 86], fill=TEALD)
d.line([60, 72, 70, 72, 76, 56, 84, 84, 90, 66, 96, 72], fill='white', width=5)
d.text((104, 40), 'NadiSense', font=font(34), fill=TXT)
d.text((104, 84), 'Screening result · 30 s window · on-device', font=font(20, False), fill=MUTED)
d.rounded_rectangle([W - 400, 36, W - 40, 96], 26, fill=RED)
d.text((W - 380, 47), 'FLAGGED · REFER FOR ECG', font=font(21), fill='white')

data = js_get('afib')

# left: gauge card
gx0, gy0, gx1, gy1 = 24, 130, 500, 600
d.rounded_rectangle([gx0, gy0, gx1, gy1], 20, fill=CARD)
d.text((gx0 + 30, gy0 + 24), 'P(irregular rhythm)', font=font(22, False), fill=MUTED)
d.text((gx0 + 30, gy0 + 56), '99%', font=font(78), fill=TXT)
# gauge arc (PIL: degrees clockwise from 3 o'clock, y-down; top arc = 180..360)
cx, cy, R = 262, 470, 150
import math
zones = [((0, 0.35), GREEN), ((0.35, 0.65), AMBER), ((0.65, 1.0), RED)]
for (f0, f1), col in zones:
    d.arc([cx - R, cy - R, cx + R, cy + R], start=180 + 180 * f0, end=180 + 180 * f1 - 2, fill=col, width=14)
# needle at ~99% (f = 0.999)
f = 0.999
ang = math.radians(180 + 180 * f)
nx = cx + (R - 44) * math.cos(ang)
ny = cy + (R - 44) * math.sin(ang)
d.line([cx, cy, nx, ny], fill='white', width=7)
d.ellipse([cx - 12, cy - 12, cx + 12, cy + 12], fill='white')
d.text((cx - R - 20, cy + 14), '0', font=font(18, False), fill=MUTED)
d.text((cx + R + 4, cy + 14), '1', font=font(18, False), fill=MUTED)

# right: HRV metrics
mx0 = 530
d.rounded_rectangle([mx0, 130, W - 24, 470], 20, fill=CARD)
d.text((mx0 + 30, 150), 'HRV metrics', font=font(26), fill=TXT)
cards = [('HR', f"{data['hr']:.0f}", 'bpm'), ('SDNN', f"{data['sdnn']:.0f}", 'ms'),
         ('RMSSD', f"{data['rmssd']:.0f}", 'ms'), ('pNN50', f"{data['pnn50']:.0f}", '%'),
         ('SD1/SD2', f"{data['sd1sd2']:.2f}", ''), ('LF/HF', f"{data['lfhf']:.2f}", ''),
         ('Beats', str(data['n']), '')]
for i, (k, v, u) in enumerate(cards):
    x0 = mx0 + 30 + (i % 4) * ((W - 24 - mx0 - 60) / 4)
    y0 = 210 + (i // 4) * 120
    d.rounded_rectangle([x0, y0, x0 + (W - 24 - mx0 - 60) / 4 - 12, y0 + 96], 14, fill=(11, 34, 49))
    d.text((x0 + 16, y0 + 12), k, font=font(18, False), fill=MUTED)
    d.text((x0 + 16, y0 + 40), f'{v} {u}'.strip(), font=font(30), fill=TEAL)

# waveform strip
d.rounded_rectangle([24, 620, W - 24, 940], 20, fill=CARD)
d.text((50, 640), '30 s pulse waveform · ● detected beats', font=font(22, False), fill=MUTED)
sig = np.array(data['sig'])
det = sig - sig.mean()
# simple bandpass via numpy
n = len(det)
F = np.fft.rfft(det)
freqs = np.fft.rfftfreq(n, 1 / 30)
mask = np.zeros_like(freqs)
mask[(freqs >= 0.6) & (freqs <= 3.5)] = 1
bp = np.fft.irfft(F * mask, n)
mn, mx = bp.min(), bp.max(); rng = max(mx - mn, 1e-9)
x0, ytop, x1, ybot = 50, 680, W - 50, 900
pts = []
for i in range(n):
    x = x0 + (i / n) * (x1 - x0)
    y = ytop + (ybot - ytop) * (1 - (bp[i] - mn) / rng)
    pts.append((x, y))
d.line(pts, fill=(56, 189, 248), width=5, joint='curve')
# peaks
for i in range(1, n - 1):
    if bp[i] >= bp[i - 1] and bp[i] > bp[i + 1] and bp[i] > 0.4 * rng:
        x = x0 + (i / n) * (x1 - x0)
        y = ytop + (ybot - ytop) * (1 - (bp[i] - mn) / rng)
        d.ellipse([x - 7, y - 7, x + 7, y + 7], fill=(244, 114, 182))

out = '../assets/ui_mock.png'
img.save(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', out))
print('wrote', out)
