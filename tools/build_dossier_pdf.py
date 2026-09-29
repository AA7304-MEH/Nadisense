#!/usr/bin/env python3
"""
build_dossier_pdf.py — NadiSense Complete Project Dossier (one PDF with
everything): the application, the AI engine + real-patient validation, the
GitHub repo guide, deliverables, how-to-demo, honest limits, current status.

Style matches the other deliverables (teal/navy palette), with the running
TCET header + page numbers like the submission docx.

Run:  pip install reportlab && python3 tools/build_dossier_pdf.py
"""
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, PageBreak, HRFlowable)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT1 = os.path.join(HERE, '..', '..', 'deliverables')
OUT2 = os.path.join(HERE, '..', '..', 'UPLOAD_THIS')

TEAL = HexColor('#0F766E'); NAVY = HexColor('#0B1F3A'); INK = HexColor('#1E293B')
MUTED = HexColor('#64748B'); LIGHT = HexColor('#F1F5F9'); LINE = HexColor('#D8E2E9')

HEADER_L = ('NadiSense · Team Agent Matrix · TECHNOVA 2026 · '
            'TCET — Thakur College of Engineering & Technology, Mumbai')

BODY = ParagraphStyle('body', fontName='Helvetica', fontSize=9.5, leading=13.5,
                      textColor=INK, alignment=TA_JUSTIFY, spaceAfter=5)
H1 = ParagraphStyle('H1', fontName='Helvetica-Bold', fontSize=14, leading=17,
                    textColor=TEAL, spaceBefore=14, spaceAfter=5)
H2 = ParagraphStyle('H2', fontName='Helvetica-Bold', fontSize=11, leading=14,
                    textColor=NAVY, spaceBefore=9, spaceAfter=3.5)
BULL = ParagraphStyle('bull', parent=BODY, leftIndent=11, bulletIndent=3, spaceAfter=3)
CODE = ParagraphStyle('code', parent=BODY, fontName='Courier', fontSize=8.3,
                      leading=11, leftIndent=8, textColor=NAVY)
SMALL = ParagraphStyle('small', parent=BODY, fontSize=8.3, textColor=MUTED)


def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def table(rows, widths, header=True, fs=8.6):
    data = [[Paragraph(
        f'<font name="Helvetica{"-Bold" if header and ri == 0 else ""}" size="{fs}">{esc(c)}</font>',
        BODY) for c in row] for ri, row in enumerate(rows)]
    t = Table(data, colWidths=widths, hAlign='LEFT', repeatRows=1 if header else 0)
    style = [('GRID', (0, 0), (-1, -1), 0.5, LINE),
             ('VALIGN', (0, 0), (-1, -1), 'TOP'),
             ('LEFTPADDING', (0, 0), (-1, -1), 5), ('RIGHTPADDING', (0, 0), (-1, -1), 5),
             ('TOPPADDING', (0, 0), (-1, -1), 3.5), ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5)]
    if header:
        style += [('BACKGROUND', (0, 0), (-1, 0), LIGHT),
                  ('TEXTCOLOR', (0, 0), (-1, 0), NAVY)]
    t.setStyle(TableStyle(style))
    return t


def bullets(items):
    return [Paragraph(f'• {esc(i)}', BULL) for i in items]


def on_page(canvas, doc_):
    canvas.saveState()
    canvas.setFont('Helvetica', 7.5); canvas.setFillColor(MUTED)
    canvas.drawString(20*mm, A4[1] - 12*mm, HEADER_L)
    canvas.setStrokeColor(LINE); canvas.setLineWidth(0.5)
    canvas.line(20*mm, A4[1] - 14*mm, 190*mm, A4[1] - 14*mm)
    canvas.setFont('Helvetica', 7.5)
    canvas.drawString(20*mm, 9*mm, 'On-device AI screening aid — not a diagnostic device · nothing leaves the phone')
    canvas.drawRightString(190*mm, 9*mm, f'Page {doc_.page}')
    canvas.restoreState()


def build(path):
    doc = SimpleDocTemplate(path, pagesize=A4,
                            leftMargin=20*mm, rightMargin=20*mm,
                            topMargin=20*mm, bottomMargin=16*mm,
                            title='NadiSense — Complete Project Dossier (v1.0)',
                            author='Team Agent Matrix — TCET, Mumbai University')
    el = []

    # ---------------- cover ----------------
    el.append(Spacer(1, 8*mm))
    el.append(Paragraph('TECHNOVA 2026 — National AI Innovation Challenge', ParagraphStyle(
        'c1', parent=BODY, alignment=TA_CENTER, textColor=MUTED, fontSize=10)))
    el.append(Spacer(1, 4*mm))
    el.append(Paragraph('NadiSense', ParagraphStyle('c2', parent=BODY, alignment=TA_CENTER,
                                                    fontName='Helvetica-Bold', fontSize=30, textColor=TEAL)))
    el.append(Paragraph('30-second AI heart-rhythm screening, from any phone camera',
                        ParagraphStyle('c3', parent=BODY, alignment=TA_CENTER, fontSize=11.5, textColor=NAVY)))
    el.append(Spacer(1, 2*mm))
    el.append(Paragraph('Camera-only PPG · on-device neural network · zero hardware · zero internet · in English, Hindi and Tamil',
                        ParagraphStyle('c4', parent=BODY, alignment=TA_CENTER, fontSize=8.8, textColor=MUTED)))
    el.append(Spacer(1, 7*mm))
    el.append(HRFlowable(width='100%', thickness=0.8, color=LINE))
    el.append(Spacer(1, 5*mm))
    el.append(table([
        ['Team', 'Agent Matrix (3 members, within the 3–5 rule)'],
        ['Team leader', 'Aditya Mehra — E&TC, 3rd year (presents solo)'],
        ['Members', 'Akanshu Pandey, 3rd year · Siddesh Wagh (BCA, 3rd year)'],
        ['Institution', 'Thakur College of Engineering and Technology (TCET), Mumbai University, Maharashtra'],
        ['Contact', 'matricphase@gmail.com'],
        ['Domain', 'Healthcare / Digital Health — accessible cardiac screening'],
        ['Stage', 'Working product v1.0 — live, tested, deployed'],
        ['Version date', '27 September 2026'],
    ], [34*mm, 136*mm], header=False))
    el.append(Spacer(1, 6*mm))
    el.append(Paragraph('Live links', H2))
    el.append(table([
        ['Live application (v1.0)', 'https://nadisense.vercel.app'],
        ['GitHub repository', 'https://github.com/AA7304-MEH/Nadisense'],
        ['GitHub Pages mirror', 'https://aa7304-meh.github.io/Nadisense/'],
        ['Offline single-file app', 'deliverables/nadi.html (runs from a USB stick, no install)'],
    ], [52*mm, 118*mm]))
    el.append(Paragraph(
        'This dossier is the single shareable document covering the application, the AI engine and its '
        'real-patient validation, the repository, the deliverables, and exactly where the project stands today.',
        SMALL))
    el.append(PageBreak())

    # ---------------- 1 project at a glance ----------------
    el.append(Paragraph('1 · Project at a glance', H1))
    el.append(Paragraph(
        'Cardiovascular disease kills more people in India than any other cause, and the stroke-causing rhythm '
        'disorder atrial fibrillation (AFib) is both common and silent. The only reliable detector is an ECG — a '
        'machine most villages do not have, at a distance most patients cannot afford to travel. NadiSense closes '
        'that gap with software alone: it turns the phone camera in an ASHA worker’s pocket into a pulse sensor '
        'and reads the 30-second signal with a tiny neural network running entirely on the phone. No sensor, '
        'no internet, no cloud, no clinic visit.', BODY))
    el += bullets([
        'One-finger, 30-second screening; answer is one clear line: GREEN — routine · AMBER — repeat in 2 weeks · RED — ECG within 7 days.',
        'Works fully offline after first load; also ships as a single self-contained HTML file.',
        'Privacy by architecture: frames are reduced to brightness means and discarded instantly — no image, video or signal ever stored or uploaded.',
        'Built for ASHA/PHC field reality: 3 languages, ~4 taps, voice questionnaire, printable report, quality-gated retakes.',
        'AI validated on real patient data — MIT-BIH AFDB, record-independent holdout: 97.2% accuracy, 99.5% sensitivity, 95.2% specificity (Section 3).',
    ])

    # ---------------- 2 the application ----------------
    el.append(Paragraph('2 · The application', H1))
    el.append(Paragraph('2.1 The 30-second flow', H2))
    el += bullets([
        'Set up — open the app (offline), pick language, patient’s fingertip covers the rear camera and flash, pressed gently.',
        'Capture — flash auto-switches on (transmitted-light PPG); the app auto-picks the strongest pulse channel (green/red/blue) after the first second; live waveform, quality meter, live HR and beat count.',
        'Analyse (instant, on-device) — detrend → zero-phase FFT band-pass (0.6–3.5 Hz) → adaptive two-pass peak detection → RR intervals → 12 HRV features → ±3σ winsorisation → MLP inference (~2 ms).',
        'Act — green/amber/red card with 12 HRV metrics, tachogram, Poincaré plot, detected-beat waveform, an optional 2-question voice screen, and a printable on-device report branded “NadiSense v1.0 · Agent Matrix · TECHNOVA 2026”.',
    ])
    el.append(Paragraph('2.2 Field robustness (hardened this cycle)', H2))
    el += bullets([
        'Works in every browser tab — normal or incognito. If camera permission was ever blocked, the app now shows the exact two-tap fix (“lock icon → Site settings → Camera → Allow”) instead of silently falling back.',
        'Per-cause camera panels (blocked / busy in another app / no camera / needs-https), each with Retry + Demo Mode buttons, in English, Hindi and Tamil.',
        'Constraint ladder for exotic devices and in-app webviews; torch required note when the room is dark.',
        'Self-healing boot: stale caches/service workers from older builds are cleared, so nobody ever gets stuck on an old version; a boot error can never leave a black screen.',
        'Safety guardrails never loosened: signal quality < 0.6 → polite retake; HR sanity 40–180; ≥12 clean beats required; heavy ectopy mentioned as a note, never punished as AFib.',
    ])
    el.append(Paragraph('2.3 Two modes, one pipeline', H2))
    el += bullets([
        'Camera mode — the field capability: verified on real fingertip captures (e.g. 17 Sep 2026, 14:21: regular rhythm, P=6%, HR 64 bpm, 25 beats analysed, printable report).',
        'Demo Mode — the stage capability: six deterministic simulated scenarios (normal, low-HRV, AFib-like, noisy, weak) fed through the identical DSP + classifier. Works in a hall with no internet and a projector; perfect with a seeded repeat for side-by-side runs.',
    ])

    # ---------------- 3 the AI engine ----------------
    el.append(PageBreak())
    el.append(Paragraph('3 · The AI engine — trained on real patient data', H1))
    el.append(Paragraph('3.1 What goes in', H2))
    el += bullets([
        '12 interpretable features from the beat-to-beat (RR) tachogram: HR mean, SDNN, RMSSD, pNN50, SD1, SD2, SD1/SD2, LF/HF, spectral entropy, turning-point ratio, irregularity %, ectopy-like beat fraction.',
        'Model: MLP 12→20→10→1 (tanh/tanh/sigmoid), 11.5 KB of plain-text weights, ~2 ms inference in any modern browser.',
        'The Python training reference mirrors the shipped JS DSP line-for-line; equivalence verified numerically — the model card is reproducible, not marketing.',
    ])
    el.append(Paragraph('3.2 The dataset (this is the upgrade)', H2))
    el.append(Paragraph(
        'The shipped v1.0 model is trained on the MIT-BIH Atrial Fibrillation Database (PhysioNet afdb 1.0.0) — '
        'the standard research benchmark: cardiologist-annotated beats from 25 AFib patients, 23 two-channel ECG '
        'records ~10 hours each. Rhythm annotations are joined with beat annotations; the RR series is cut into '
        '30 s windows (15 s stride; single-rhythm windows with ≥18 beats) → 93,730 training windows (+±3% '
        'proportional “camera-jitter” augmentation on the training side so the model tolerates phone-PPG '
        'peak-timing noise). One command reproduces everything: python3 tools/train_real_data.py', BODY))
    el.append(Paragraph('3.3 Validation — record-independent, the honest kind', H2))
    el.append(table([
        ['Metric', 'Score', 'Basis'],
        ['Accuracy', '97.2%', '5 held-out patients never seen in training: 06426, 06995, 08378, 08434, 08455'],
        ['Sensitivity', '99.5%', 'catches 99.5 of 100 AFib windows'],
        ['Specificity', '95.2%', '≈1 in 20 normal windows may false-flag — deliberately cautious'],
        ['Precision / F1', '94.8% / 0.971', '11,858 validation windows (47% AF prevalence)'],
    ], [30*mm, 30*mm, 110*mm]))
    el.append(Spacer(1, 2*mm))
    el.append(Paragraph(
        'The full numbers ship as tools/metrics.json and inside the app itself (NADI_MODEL.meta) — any judge '
        'can open dev tools and verify. An extreme synthetic AF fixture reads ~91% P(irregular), not a pegged '
        '100%: real-data calibration, with the care-level decision unchanged.', SMALL))
    el.append(Paragraph('3.4 Honest limits (stated in the app, the deck, everywhere)', H2))
    el += bullets([
        'Validation is on ECG-derived RR intervals — the clinical gold standard for rhythm labels; phone PPG adds noise (mitigated by jitter augmentation + the quality gate). A PHC field study vs 12-lead ECG is the next tier.',
        'Screening aid, not a diagnostic device — a red card means “go get an ECG”, never “you have AFib”.',
        'Irregularity has many causes (stress, caffeine, ectopy); a negative result does not rule out heart disease.',
    ])

    # ---------------- 4 engineering quality ----------------
    el.append(Paragraph('4 · Engineering quality & verification', H1))
    el += bullets([
        '61 automated tests, all green: 37 pipeline assertions (simulator, DSP, features, classifier, guardrails, camera buffer) + 24 full-UI browser assertions in jsdom — including the camera failure UX and saturated-flash adaptive-channel regressions.',
        'Run it exactly like a judge: npm install && npm test in the repo.',
        'Single-file offline build (tools/build_standalone.mjs) → 127 KB nadi.html, no network calls at all.',
        'Install-free deployment: static hosting on Vercel (prod) + GitHub Pages mirror; camera requires https, which both provide.',
    ])

    # ---------------- 5 the repository ----------------
    el.append(Paragraph('5 · GitHub repository — what a judge sees', H1))
    el.append(Paragraph('Repo: https://github.com/AA7304-MEH/Nadisense  ·  Live from it: '
                        'https://aa7304-meh.github.io/Nadisense/', BODY))
    el.append(Paragraph('Layout (fully browsable source, not a zip blob):', H2))
    el.append(Paragraph(
        'index.html — the full app<br/>'
        'css/style.css — design system<br/>'
        'js/ — app.js (UI/flow) · ppgcamera.js (adaptive-channel capture) · dsp.js (signal chain + 12 features) · '
        'classifier.js (MLP + guardrails) · model_weights.js (weights + model card) · simulator.js (demo fixture) · '
        'i18n.js (EN/HI/TA strings) · asr.js (voice Q&amp;A)<br/>'
        'tests/ — run_tests.mjs (34) · run_browser_smoke.mjs (24)<br/>'
        'tools/ — train_real_data.py (MIT-BIH retrain) · train_mlp.py (synthetic preview) · build_standalone.mjs · '
        'metrics.json (validation record) · build_submission_docx.py · build_dossier_pdf.py<br/>'
        'nadi.html — offline single-file build · assets/ · demo.mp4 · README.md · package.json', CODE))
    el.append(Spacer(1, 2*mm))
    el.append(table([
        ['Command', 'What it does'],
        ['npm install && npm test', 'Installs jsdom and runs all 61 tests'],
        ['python3 tools/train_real_data.py', 'Streams MIT-BIH AFDB, retrains on real patient data, rewrites js/model_weights.js + tools/metrics.json'],
        ['node tools/build_standalone.mjs', 'Bundles the app into one offline HTML file'],
        ['(open index.html / the Pages link)', 'Runs the app — nothing to build, no server needed'],
    ], [56*mm, 114*mm]))

    # ---------------- 6 deliverables ----------------
    el.append(Paragraph('6 · Deliverables checklist', H1))
    el.append(table([
        ['Item', 'File / place', 'Status'],
        ['Submission document (Word, TCET running header)', 'deliverables/NadiSense_TECHNOVA2026_Submission.docx', 'v1.0 ready'],
        ['Innovation Summary PDF', 'NadiSense_Innovation_Summary.pdf', 'ready'],
        ['Presentation PDF (14 pages)', 'NadiSense_Presentation.pdf', 'ready'],
        ['Zonal pitch deck', 'NadiSense_Zonal_Round_Pitch.pptx', 'ready'],
        ['Demo video', 'NadiSense_Demo.mp4', 'ready'],
        ['Q&A battle reference + battle card', 'Zonal_QA_Battle_Ref.pdf · Tech_QA_Set.md · Zonal_BattleCard.md', 'ready'],
        ['Solo presenter script (Aditya)', 'Zonal_Speech_Script_SOLO_Aditya.md + slide-by-slide content', 'ready'],
        ['Form answers (all 7 sections)', 'deliverables/Form_Answers_*', 'ready to paste'],
        ['Source code', 'GitHub repo + NadiSense_source.zip', 'v1.0 push pending'],
        ['Offline app build', 'deliverables/nadi.html', 'v1.0'],
        ['This dossier', 'deliverables/NadiSense_Complete_Dossier.pdf', 'v1.0'],
    ], [62*mm, 84*mm, 24*mm]))

    # ---------------- 7 status & next actions ----------------
    el.append(Paragraph('7 · Where we stand — and what happens next', H1))
    el += bullets([
        'DONE: real-patient model shipped and verified live; camera hardened for normal tabs, incognito, webviews; 61/61 tests green; all documents rebranded to Agent Matrix with the TCET header; live app verified by curl after every deploy.',
        'IN FLIGHT: push v1.0 to GitHub (commit prepared; one token away) — Pages then auto-updates.',
        'NEXT: submit the TECHNOVA form using the pre-written section answers; run one seated rehearsal of the Demo Mode story; field-test the camera on 2–3 different phones for confidence.',
        'AFTER SEASON: revoke the temporary Vercel + GitHub tokens (security hygiene); refresh the demo video with the v1.0 UI; optional PWA install icon.',
    ])
    el.append(Spacer(1, 3*mm))
    el.append(HRFlowable(width='100%', thickness=0.8, color=LINE))
    el.append(Spacer(1, 3*mm))
    el.append(Paragraph(
        'NadiSense is built to be checked, not believed. Every number in this dossier is reproducible from the '
        'repo; every claim in the app is stated as a screening aid, not a diagnosis. Team Agent Matrix — TCET, '
        'Mumbai University · TECHNOVA 2026 · 27 September 2026', SMALL))

    doc.build(el, onFirstPage=on_page, onLaterPages=on_page)
    return path


if __name__ == '__main__':
    import shutil
    p1 = os.path.join(OUT1, 'NadiSense_Complete_Dossier.pdf')
    build(p1)
    shutil.copy(p1, os.path.join(OUT2, 'NadiSense_Complete_Dossier.pdf'))
    print('wrote', p1)
