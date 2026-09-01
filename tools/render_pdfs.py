#!/usr/bin/env python3
"""
render_pdfs.py — builds the two required upload PDFs:
  1. NadiSense_Innovation_Summary.pdf   (Section 27 of the form)
  2. NadiSense_Presentation.pdf         (Section 28 of the form, 14 pages)
"""
import os
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm, inch
from reportlab.lib.colors import HexColor, white
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, PageBreak, Image as RLImage, HRFlowable)
from reportlab.pdfgen import canvas as rlcanvas

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', '..', 'deliverables')
ASSETS = os.path.join(HERE, '..', '..', 'assets')

TEAL = HexColor('#0F766E')
NAVY = HexColor('#0B1F3A')
INK = HexColor('#1E293B')
MUTED = HexColor('#64748B')
LIGHT = HexColor('#F1F5F9')
LINE = HexColor('#D8E2E9')

# ======================================================================
# 1 · INNOVATION SUMMARY PDF
# ======================================================================
def build_summary():
    path = os.path.join(OUT, 'NadiSense_Innovation_Summary.pdf')
    doc = SimpleDocTemplate(path, pagesize=A4,
                            leftMargin=20*mm, rightMargin=20*mm,
                            topMargin=16*mm, bottomMargin=16*mm,
                            title='NadiSense — TECHNOVA 2026 Innovation Summary',
                            author='Team Matric Phase')

    H1 = ParagraphStyle('H1', fontName='Helvetica-Bold', fontSize=14,
                        textColor=TEAL, spaceBefore=12, spaceAfter=4)
    H2 = ParagraphStyle('H2', fontName='Helvetica-Bold', fontSize=11.5,
                        textColor=INK, spaceBefore=8, spaceAfter=3)
    BODY = ParagraphStyle('BODY', fontName='Helvetica', fontSize=9.5,
                          leading=13.5, textColor=INK, alignment=TA_JUSTIFY,
                          spaceAfter=5)
    SMALL = ParagraphStyle('SMALL', fontName='Helvetica-Oblique', fontSize=8,
                           textColor=MUTED, leading=11, spaceAfter=4)
    TITLE = ParagraphStyle('TITLE', fontName='Helvetica-Bold', fontSize=26,
                           textColor=TEAL, alignment=TA_CENTER, leading=30)
    SUB = ParagraphStyle('SUB', fontName='Helvetica', fontSize=12,
                         textColor=INK, alignment=TA_CENTER, leading=16)
    META = ParagraphStyle('META', fontName='Helvetica', fontSize=9,
                          textColor=MUTED, alignment=TA_CENTER, leading=13)
    CELL = ParagraphStyle('CELL', fontName='Helvetica', fontSize=8.5,
                          leading=11.5, textColor=INK, alignment=TA_LEFT,
                          wordWrap='CJK', spaceBefore=1, spaceAfter=1)
    CELLB = ParagraphStyle('CELLB', fontName='Helvetica-Bold', fontSize=8.5,
                           leading=11.5, textColor=INK, alignment=TA_LEFT,
                           wordWrap='CJK', spaceBefore=1, spaceAfter=1)

    def st_table(rows, widths):
        """Table where EVERY cell is a Paragraph so text wraps inside
        narrow columns (plain strings overflow). Header row teal, first
        column bold."""
        p_rows = []
        for i, row in enumerate(rows):
            out = []
            for j, val in enumerate(row):
                if i == 0:
                    st_ = ParagraphStyle('HDR', parent=CELLB, textColor=white)
                elif j == 0:
                    st_ = CELLB
                else:
                    st_ = CELL
                out.append(Paragraph(str(val), st_))
            p_rows.append(out)
        t = Table(p_rows, colWidths=widths, repeatRows=1, hAlign='LEFT')
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#0F766E')),
            ('TEXTCOLOR', (0, 0), (-1, 0), white),
            ('GRID', (0, 0), (-1, -1), 0.4, LINE),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, LIGHT]),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ]))
        return t

    story = []
    # ---- cover ----
    story.append(Spacer(1, 18*mm))
    story.append(Paragraph('TECHNOVA 2026 — National AI Innovation Challenge', META))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph('NadiSense', TITLE))
    story.append(Paragraph('60-second AI heart-rhythm screening for rural India', SUB))
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph('Camera-only photoplethysmography · on-device neural network · '
                           'zero hardware · zero internet · EN / Hindi / Tamil', META))
    story.append(Spacer(1, 8*mm))
    story.append(Paragraph('Innovation Summary — Submission Document', SUB))
    story.append(Spacer(1, 5*mm))
    story.append(Table([
        [Paragraph('<b>Team</b>', CELLB), Paragraph('Matric Phase', CELL)],
        [Paragraph('<b>Team leader</b>', CELLB), Paragraph('Aditya Mehra — E&TC, 3rd year', CELL)],
        [Paragraph('<b>Members</b>', CELLB),
         Paragraph('Abhishek Singh (E&TC, 3rd year) · Siddesh Wagh (BCA, 3rd year)', CELL)],
        [Paragraph('<b>Institution</b>', CELLB),
         Paragraph('Thakur College of Engineering and Technology, Mumbai University, Maharashtra', CELL)],
        [Paragraph('<b>Domain</b>', CELLB),
         Paragraph('Healthcare / Digital Health — accessible cardiac screening', CELL)],
        [Paragraph('<b>SDGs</b>', CELLB), Paragraph('SDG 3 · SDG 9 · SDG 10', CELL)],
        [Paragraph('<b>Stage</b>', CELLB), Paragraph('Working prototype (v0.9) — live demo included', CELL)],
    ], colWidths=[30*mm, 130*mm], style=TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.4, LINE),
        ('BACKGROUND', (0, 0), (0, -1), LIGHT),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ])))
    story.append(Spacer(1, 6*mm))
    story.append(Paragraph('Themes addressed: “Solving Tomorrow’s Problems Today” — the problem is '
                           'today’s (silent heart disease reaches the village late), the solution is '
                           'tomorrow’s AI (a 6 KB model that runs on a phone that already exists).', SMALL))
    story.append(PageBreak())

    # ---- 1. Executive summary ----
    story.append(Paragraph('1. Executive summary', H1))
    story.append(Paragraph(
        'Cardiovascular disease is India’s leading cause of death, and the stroke-causing rhythm '
        'disorder atrial fibrillation (AFib) is both common and silent. The only reliable test is an '
        'ECG — a machine most villages do not have, at a distance most patients cannot afford to '
        'travel. <b>NadiSense closes that gap with software alone:</b> it turns the smartphone camera '
        'in an ASHA worker’s pocket into a pulse sensor and reads a 60-second signal with a 6 KB '
        'neural network running entirely on the phone. No sensor, no internet, no cloud, no clinic '
        'visit. The output is one line an ASHA worker can act on: <b>green</b> — routine; <b>amber</b> '
        '— repeat in two weeks; <b>red</b> — ECG within seven days. In English, Hindi and Tamil, '
        'offline, with a printable screening report.', BODY))
    story.append(Paragraph(
        'We have fully built the product: a working prototype (camera capture + signal processing + '
        'classifier + vernacular UI + report), 30 automated pipeline tests, 13 end-to-end UI tests, '
        'and a reproducible training pipeline. We are also explicit about what is not yet true: the '
        'shipped model is validated on a realistic synthetic training distribution; a real-patient '
        'benchmark (MIT-BIH AF/NSR) is one command away — the script ships with the code. We treat '
        'that honesty as part of the engineering, not a disclaimer.', BODY))

    # ---- 2. Problem ----
    story.append(Paragraph('2. Problem statement', H1))
    story.append(Paragraph(
        'Millions of Indians are never screened for the two conditions that cause most preventable '
        'strokes — hypertension and atrial fibrillation. The clinical reality is blunt: rhythm '
        'disorders are diagnosed by ECG, and ECG machines live in district hospitals often 40–90 km '
        'and a day’s wages away.', BODY))
    story.append(Paragraph('2.1 Why AFib is the right target', H2))
    for b in [
        'Most common sustained arrhythmia; prevalence rises from ~1% under 60 to ~9% above 80 — a '
        'rapidly ageing population makes this a growing problem.',
        'The most common cause of cardioembolic stroke: roughly 1 in 5 strokes is attributed to AF. '
        'Many of those strokes are the first symptom — the disease is silent.',
        'It is paroxysmal: symptoms come and go, so a single in-clinic ECG is a coin flip.',
        'It is treatable: anticoagulation cuts stroke risk by roughly two-thirds. Early detection '
        'converts a catastrophic event into a prescription.',
    ]:
        story.append(Paragraph('•  ' + b, ParagraphStyle('bul', parent=BODY, leftIndent=8,
                                                         spaceAfter=2)))
    story.append(Paragraph('2.2 The screening gap is logistical, not clinical', H2))
    story.append(st_table([
        ['Who', 'What they have today', 'The gap'],
        ['Village / PHC level', 'Manual BP cuffs, outreach camps',
         'No rhythm screening at all — “pulse feels fine” is not a test'],
        ['Block CHC', 'One ECG machine, one technician, long queue',
         'Travel + waiting cost more than the test; referrals drop off'],
        ['ASHA workers (~10 lakh)', 'A smartphone and a door-to-door mandate',
         'No tool matches their workflow; NCD software is paper-first'],
    ], [34*mm, 56*mm, 70*mm]))

    # ---- 3. Solution ----
    story.append(Paragraph('3. The solution', H1))
    story.append(Paragraph('3.1 Experience (60 seconds)', H2))
    for b in [
        '<b>Set up</b> — ASHA worker opens the app (offline), picks language, places patient’s '
        'fingertip over the camera lens.',
        '<b>Capture</b> — the app shows the live pulse waveform, a signal-quality meter and live HR; '
        'motion is rejected with clear “hold still” guidance and a retake prompt.',
        '<b>Analyse</b> — on-device detrend + FFT band-pass -> beat detection -> 12 HRV features -> '
        '±3σ winsorisation -> 6 KB MLP -> P(irregular rhythm). ~2 ms.',
        '<b>Act</b> — green / amber / red card, the 12 HRV metrics, tachogram, Poincaré plot, '
        'detected-beat waveform, printable report, optional 2-question voice screen.',
    ]:
        story.append(Paragraph('•  ' + b, ParagraphStyle('bul', parent=BODY, leftIndent=8,
                                                         spaceAfter=2)))
    story.append(Paragraph('3.2 What is actually built', H2))
    story.append(st_table([
        ['Component', 'Status', 'Location'],
        ['Camera PPG capture (green-channel ROI -> 30 Hz signal)', 'Shipped', 'js/ppgcamera.js'],
        ['DSP: detrend, zero-phase FFT band-pass, adaptive 2-pass peak detection', 'Shipped, tested', 'js/dsp.js'],
        ['12 HRV features (SDNN, RMSSD, pNN50, SD1, SD2, SD1/SD2, LF/HF, spectral entropy, turning-point, irregularity %, ectopy fraction, HR)', 'Shipped, tested', 'js/dsp.js'],
        ['MLP classifier 12->20->10->1 (6 KB) + care levels + guardrails', 'Shipped, tested', 'js/classifier.js'],
        ['Vernacular UI (EN / Hindi / Tamil) + voice questionnaire', 'Shipped', 'js/i18n.js, js/asr.js'],
        ['Result dashboard, logbook, printable report', 'Shipped', 'js/app.js'],
        ['Synthetic signal generator (6 scenarios incl. AFib-like, motion, weak)', 'Shipped (test fixture)', 'js/simulator.js'],
        ['Training pipeline (NumPy, mirrors the JS DSP 1:1)', 'Shipped + documented', 'tools/train_mlp.py'],
        ['Automated tests: 30 pipeline + 13 full-UI', 'All green', 'tests/'],
        ['Single-file offline build (runs from a USB stick)', 'Shipped', 'deliverables/nadi.html'],
    ], [96*mm, 34*mm, 30*mm]))

    # ---- 4. Architecture ----
    story.append(Paragraph('4. Frugal hardware & software architecture', H1))
    story.append(Paragraph(
        '<b>Hardware: none, deliberately.</b> The bill of materials is one smartphone. Reflectance '
        'photoplethysmography needs only a camera and, in low light, the flash — both standard on '
        'the cheapest devices issued to ASHA workers. No calibration, no consumables, no firmware, '
        'nothing to lose or break. <b>Software:</b> capture (ROI summed to one green-channel mean '
        'per frame), DSP (detrend -> zero-phase FFT band-pass -> adaptive peak finder -> RR intervals), '
        '12 interpretable HRV features, a 6 KB MLP, guardrails, and a 4-step vernacular UI with '
        'on-device reporting. All processing stays on the phone:', BODY))
    story.append(Paragraph(
        '•  <b>Offline-first:</b> connectivity is unreliable where ASHA workers operate — offline is '
        'a requirement, not a preference.<br/>'
        '•  <b>No server:</b> no server bill, no breach surface, no data-protection paperwork at PHC '
        'level, and no images or signals ever leave the device.<br/>'
        '•  <b>Auditable AI:</b> every weight ships in a plain-text file — 6 KB, no black box.<br/>'
        '•  <b>Pipeline integrity:</b> the Python training script and the shipped JS DSP are '
        'mirrored line-for-line (verified cross-language correlation ~ 0.998), so the deployed '
        'features equal the trained features — 30 automated tests guard every release.', BODY))

    # ---- 5. Model ----
    story.append(Paragraph('5. Model development and validation', H1))
    story.append(Paragraph('5.1 Data and training', H2))
    story.append(Paragraph(
        '12,000 windows of 30-second pulse signals generated with physiological beat dynamics '
        '(normal sinus rhythm with respiratory modulation; low-HRV; AF-like with high short-term '
        'variability, low serial correlation and occasional ectopy-like bursts), plus perturbation '
        'augmentation (noise, gain, time-warp, motion). Features are computed by the same DSP that '
        'runs in production; the dataset regenerates deterministically from a seed. Inputs are '
        'standardised and winsorised at ±3σ.', BODY))
    story.append(Paragraph('5.2 Results (held-out 20%)', H2))
    story.append(st_table([
        ['Run', 'Accuracy', 'Sensitivity', 'Specificity', 'F1'],
        ['v0.9 preview model — 12,000 windows, 60 epochs', '99.5%', '99.6%', '99.4%', '0.996'],
    ], [62*mm, 24*mm, 26*mm, 26*mm, 22*mm]))
    story.append(Paragraph(
        'End-to-end demo results through the shipped model: healthy rhythm -> risk 0.3% (green) · '
        'low-HRV -> 0.2% · AFib-like -> 99.9% (red).', BODY))
    story.append(Paragraph('5.3 Honest limits', H2))
    story.append(Paragraph(
        'The model is validated on its realistic synthetic training distribution; it has not yet '
        'been benchmarked on real patient recordings. That benchmark is the very next step and is '
        'already wired in: a one-command pipeline pulls MIT-BIH AF and NSR records, computes features '
        'through the same code, and retrains. We published it rather than hiding it, because a '
        'screening tool that overclaims is worse than no tool. Our success metric is avoidable '
        'strokes prevented — the code, benchmark script and model card will be public.', BODY))

    # ---- 6. Impact ----
    story.append(Paragraph('6. Expected impact', H1))
    story.append(st_table([
        ['Indicator', 'Baseline (rural circuit)', 'With NadiSense deployed'],
        ['Adults >40 screened for rhythm, per PHC / year', '~0', '10,000+ (one ASHA worker, 4 home visits/day)'],
        ['Time from symptom to ECG', 'Weeks–months', '≤7 days for red-flagged patients (protocol)'],
        ['Cost per screened person', 'Rs 300–800 (clinic + travel)', '~Rs 0 incremental (existing phone)'],
    ], [58*mm, 52*mm, 50*mm]))
    story.append(Paragraph(
        '<b>Economic</b> — removes the largest cost of screening (travel and lost workday) from the '
        'equation; zero procurement since the phone is already in budget; earlier detection lowers '
        'catastrophic stroke costs; better triage frees ECG capacity.<br/>'
        '<b>Social</b> — screening at the doorstep in the local language; since ~1 in 5 strokes is '
        'AF-linked and anticoagulation cuts stroke risk by ~2/3, detection prevents disability and '
        'premature death in the highest-burden population; elevates ASHA workers to first-line '
        'screeners; supports the national NCD programme; narrows the urban–rural health divide '
        '(SDG 10).<br/>'
        '<b>Environmental</b> — software only: no device manufacturing, batteries, consumables or '
        'e-waste; digital reports replace paper; inference on an existing handset means no cloud '
        'infrastructure or its energy footprint.', BODY))

    # ---- 7. Roadmap & business ----
    story.append(Paragraph('7. Roadmap', H1))
    story.append(st_table([
        ['Milestone', 'When', 'What'],
        ['v0.9 — this submission', 'Now (Sept 2026)', 'Working prototype, tested, documented'],
        ['v1.0', 'Q4 2026', 'MIT-BIH retrain + validation report; PHC pilot (2 circuits)'],
        ['v1.1', 'H1 2027', 'Multi-class rhythm model; follow-up scheduler; report handoff'],
        ['v2.0', '2027+', 'ASHA-assistant: screening calendar, BP/diabetes trends, ANM integration'],
    ], [46*mm, 34*mm, 80*mm]))
    story.append(Paragraph('Business model', H2))
    story.append(Paragraph(
        'Public health systems receive the software free (impact is the point); insurers/TPAs and '
        'diagnostics chains pay per active screen; CSR and employer wellness programmes buy per-camp '
        'bundles. Anchor principle: the public deployment is free forever, and the commercial lines '
        'subsidise it.', BODY))

    # ---- 8. Team ----
    story.append(Paragraph('8. Team (Matric Phase)', H1))
    story.append(st_table([
        ['Member', 'Role'],
        ['Aditya Mehra (lead) — E&TC, 3rd year', 'Product & ML: feature pipeline, model training, on-device inference, app'],
        ['Abhishek Singh — E&TC, 3rd year', 'Signal processing verification, hardware-free capture testing, deployment'],
        ['Siddesh Wagh — BCA, 3rd year', 'UI/UX & vernacular flows, field pilot coordination, documentation'],
    ], [80*mm, 80*mm]))

    # ---- Appendix ----
    story.append(PageBreak())
    story.append(Paragraph('Appendix A — Reproducing everything', H1))
    story.append(Paragraph(
        'Everything in this document is reproducible from the submission bundle. Structure: '
        'nadi-app/ (app source), tools/ (training, deck, figures, standalone build), tests/ '
        '(43 automated tests), deliverables/ (standalone app + deck + this summary).', BODY))
    story.append(st_table([
        ['Command', 'What it does'],
        ['python tools/train_mlp.py', 'Regenerates the dataset, retrains the MLP, writes model weights + metrics'],
        ['node tests/run_tests.mjs', '30 assertions: simulator, DSP, features, classifier, guardrails'],
        ['node tests/run_browser_smoke.mjs', '13 assertions driving the real UI in a DOM'],
        ['node tools/build_standalone.mjs', 'Bundles the app into one offline HTML file'],
        ['python tools/make_figures.py', 'Regenerates every figure from the product’s own DSP'],
    ], [66*mm, 94*mm]))
    story.append(Paragraph('Appendix B — Sources (public ranges)', H1))
    story.append(Paragraph(
        '•  CVD mortality: WHO Global Health Estimates — CVD is the leading cause of death globally.<br/>'
        '•  AF prevalence/age gradient and stroke attribution: published epidemiological reviews '
        '(1–2% overall, up to ~9% over 80; ~20% of strokes attributed to AF).<br/>'
        '•  ASHA workforce ~10 lakh: Government of India NHM programme figures.<br/>'
        'We keep these as ranges rather than single-point claims; the product does not depend on any '
        'figure being precise to the decimal.', SMALL))
    story.append(Paragraph('Demo', H1))
    story.append(Paragraph(
        'The demo needs no internet and no permissions: open deliverables/nadi.html, choose '
        '“Demo Mode”, pick a scenario, and the full pipeline runs live. A presenter runbook and a '
        'video plan are in deliverables/demo-script.md.', BODY))

    def footer(canvas, doc_):
        canvas.saveState()
        canvas.setFont('Helvetica', 7.5)
        canvas.setFillColor(MUTED)
        canvas.drawString(20*mm, 9*mm, 'NadiSense · Team Matric Phase · TECHNOVA 2026 · TSM Madurai')
        canvas.drawRightString(190*mm, 9*mm, f'Page {doc_.page}')
        canvas.restoreState()

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print('wrote', path, f'({os.path.getsize(path)//1024} KB)')

# ======================================================================
# 2 · PRESENTATION PDF (14 pages, matches the PPTX design)
# ======================================================================
def build_deck():
    path = os.path.join(OUT, 'NadiSense_Presentation.pdf')
    W, H = 13.333*inch, 7.5*inch
    c = rlcanvas.Canvas(path, pagesize=(W, H))
    c.setTitle('NadiSense — TECHNOVA 2026 Pitch')
    c.setAuthor('Team Matric Phase')

    def page_header(title, kicker=None, dark=False):
        col = HexColor('#FFFFFF') if dark else INK
        c.setFillColor(HexColor('#2DD4BF') if dark else TEAL)
        c.setFont('Helvetica-Bold', 12)
        c.drawString(0.62*inch, H-0.52*inch, (kicker or '').upper())
        c.setFillColor(col)
        c.setFont('Helvetica-Bold', 28)
        c.drawString(0.62*inch, H-1.08*inch, title)
        c.setFillColor(TEAL)
        c.rect(0.62*inch, H-1.40*inch, 1.15*inch, 0.05*inch, stroke=0, fill=1)

    def footer(note=None, dark=False):
        c.setFillColor(HexColor('#94A3B8') if dark else MUTED)
        c.setFont('Helvetica', 9)
        c.drawString(0.62*inch, 0.30*inch, note or 'NadiSense · Matric Phase · TECHNOVA 2026 · TSM Madurai')
        c.setFillColor(HexColor('#2DD4BF') if dark else TEAL)
        c.setFont('Helvetica-Bold', 9)
        c.drawRightString(W-0.62*inch, 0.30*inch, '60 seconds · one phone · zero hardware')
        c.showPage()   # every content slide ends with footer -> page break

    def card(x, y, w, h, fill=None, line=None, r=0.10):
        c.setFillColor(fill or HexColor('#FFFFFF'))
        c.setStrokeColor(line or LINE)
        c.setLineWidth(0.8)
        c.roundRect(x*inch, y*inch, w*inch, h*inch, r*inch, stroke=1 if line else 0, fill=1)

    from reportlab.pdfbase.pdfmetrics import stringWidth

    def wrap_lines(t, width_in, size, font='Helvetica'):
        words = str(t).split()
        lines, cur = [], ''
        for w_ in words:
            trial = (cur + ' ' + w_).strip()
            if not cur or stringWidth(trial, font, size) <= width_in * 72:
                cur = trial
            else:
                lines.append(cur); cur = w_
        if cur:
            lines.append(cur)
        return lines

    def wdraw(x, y, t, width_in, size, color=INK, font='Helvetica', bold=False,
              leading=None, gap=0.02):
        """Draw word-wrapped text descending from (x, y) in inches."""
        lines = wrap_lines(t, width_in, size, font)
        yy = y
        for ln in lines:
            c.setFillColor(color)
            c.setFont(font + ('-Bold' if bold else ''), size)
            c.drawString(x * inch, yy * inch, ln)
            yy -= (leading or size * 1.22) / 72 + gap
        return yy

    def text(x, y, s, size=12, color=INK, bold=False, align='l', width=3.0, leading=None):
        c.setFillColor(color)
        c.setFont('Helvetica-Bold' if bold else 'Helvetica', size)
        leading = leading or size*1.18
        y_ = y*inch
        for line in s.split('\n'):
            if align == 'c':
                c.drawCentredString((x + width/2)*inch, y_, line)
            elif align == 'r':
                c.drawRightString((x + width)*inch, y_, line)
            else:
                c.drawString(x*inch, y_, line)
            y_ -= leading

    def img(name, x, y, w=None, h=None):
        p = os.path.join(ASSETS, name)
        from reportlab.lib.utils import ImageReader
        ir = ImageReader(p)
        iw, ih = ir.getSize()
        if w and not h: h = w * ih / iw
        if h and not w: w = h * iw / ih
        c.drawImage(ir, x*inch, y*inch, w*inch, h*inch, preserveAspectRatio=True)

    def table(rows, x, y, widths, header_fill=NAVY if False else None, font=9, row_h=0.32):
        hdr = header_fill or HexColor('#0F766E')
        yy = y
        c.setFont('Helvetica-Bold', font)
        for j, val in enumerate(rows[0]):
            c.setFillColor(hdr); c.rect(x*inch, (yy - row_h)*inch if False else (yy - row_h)*inch,
                                        0, 0)  # placeholder, handled below
        # simpler: draw as alternating white rows
        for i, row in enumerate(rows):
            rh = 0.42 if len(str(row[0])) > 40 else 0.34
            if i == 0:
                for j, val in enumerate(row):
                    c.setFillColor(HexColor('#0F766E'))
                    c.rect((x*inch), (yy - rh)*inch, sum(widths)*inch, rh*inch, stroke=0, fill=1)
                c.setFillColor(white); c.setFont('Helvetica-Bold', font)
                xx = x
                for j, val in enumerate(row):
                    c.drawString((xx + 0.1)*inch, (yy - rh + 0.12)*inch, str(val))
                    xx += widths[j]/inch if False else widths[j]
                yy -= rh + 0.02
            else:
                fill = white if i % 2 else HexColor('#F1F5F9')
                c.setFillColor(fill)
                c.rect(x*inch, (yy - rh)*inch, sum(widths)*inch, rh*inch, stroke=0, fill=1)
                c.setStrokeColor(LINE); c.setLineWidth(0.4)
                c.rect(x*inch, (yy - rh)*inch, sum(widths)*inch, rh*inch, stroke=1, fill=0)
                c.setFillColor(INK)
                c.setFont('Helvetica-Bold', font)
                xx = x
                for j, val in enumerate(row):
                    c.drawString((xx + 0.1)*inch, (yy - rh + 0.12)*inch, str(val)[:46])
                    xx += widths[j]
                yy -= rh + 0.02
        return yy

    # ---- 01 title ----
    c.setFillColor(NAVY); c.rect(0, 0, W, H, stroke=0, fill=1)
    img('wave_banner.png', 0, 0, w=13.333, h=1.55)
    c.setFillColor(HexColor('#2DD4BF')); c.setFont('Helvetica-Bold', 12)
    c.drawString(0.62*inch, H-0.85*inch, 'MATRIC PHASE · TECHNOVA 2026 · NATIONAL AI INNOVATION CHALLENGE')
    c.setFillColor(white); c.setFont('Helvetica-Bold', 62)
    c.drawString(0.62*inch, H-2.0*inch, 'NadiSense')
    c.setFillColor(HexColor('#2DD4BF')); c.setFont('Helvetica-Bold', 24)
    c.drawString(0.62*inch, H-2.75*inch, '60-second AI heart-rhythm screening for rural India')
    c.setFillColor(HexColor('#C7D5E1')); c.setFont('Helvetica', 15)
    c.drawString(0.62*inch, H-3.6*inch, 'Every phone already has a sensor. We use the camera as a photoplethysmograph —')
    c.drawString(0.62*inch, H-3.85*inch, 'no extra hardware, no internet, no ECG clinic visit. An ASHA worker screens rhythm')
    c.drawString(0.62*inch, H-4.10*inch, 'at the doorstep and learns in one minute who needs an ECG while there is still time.')
    c.setFillColor(TEAL); c.roundRect(0.62*inch, H-5.35*inch, 2.6*inch, 0.62*inch, 0.2*inch, stroke=0, fill=1)
    c.setFillColor(white); c.setFont('Helvetica-Bold', 13)
    c.drawCentredString(1.92*inch, H-5.22*inch, 'LIVE DEMO TODAY')
    c.setFillColor(HexColor('#94A3B8')); c.setFont('Helvetica', 14)
    c.drawString(3.5*inch, H-5.05*inch, 'Team Matric Phase · Aditya Mehra (lead) · Abhishek Singh · Siddesh Wagh')
    c.setFillColor(white); c.setFont('Helvetica', 14)
    c.drawString(3.5*inch, H-5.35*inch, 'Theme: “Solving Tomorrow’s Problems Today”')
    c.showPage()

    # ---- 02 problem ----
    page_header('India’s #1 killer: the village never sees an ECG', 'The problem')
    c.setFillColor(MUTED); c.setFont('Helvetica', 12.5)
    c.drawString(0.62*inch, 5.42*inch, 'AFib — the most common sustained arrhythmia and a leading cause of stroke — is silent, intermittent,')
    c.drawString(0.62*inch, 5.19*inch, 'and needs an ECG to confirm. ECGs live in district hospitals: 40–90 km and a day’s wages away.')
    stats = [('17.9M', 'deaths from CVD / year', 'worldwide — the leading cause of death'),
             ('1->9%', 'adults with AFib by age', 'rising sharply with age'),
             ('1 in 5', 'strokes linked to AFib', 'often the first symptom'),
             ('>40 km', 'to the nearest ECG', 'for most rural patients')]
    for i, (v, t, d) in enumerate(stats):
        x = 0.62 + i*3.06
        card(x, 2.72, 2.92, 2.05, fill=white, line=LINE)
        c.setFillColor(TEAL); c.setFont('Helvetica-Bold', 30)
        c.drawString((x+0.18)*inch, 4.48*inch, v)
        c.setFillColor(INK); c.setFont('Helvetica-Bold', 12.5)
        c.drawString((x+0.18)*inch, 4.06*inch, t)
        c.setFillColor(MUTED); c.setFont('Helvetica', 10.5)
        c.drawString((x+0.18)*inch, 3.78*inch, d[:40])
    c.setFillColor(INK); c.setFont('Helvetica-Bold', 14)
    c.drawString(0.62*inch, 2.28*inch, 'The screen that matters')
    c.setFillColor(MUTED); c.setFont('Helvetica', 12.5)
    c.drawString(0.62*inch, 1.95*inch, 'Clinics screen rhythm, not symptoms. In the gap between “first symptom” and “first ECG”,')
    c.drawString(0.62*inch, 1.70*inch, 'strokes happen. NadiSense puts a screening-grade rhythm check in a device ASHA workers already carry.')
    footer('Public health estimates (WHO, ICMR-style reviews) — ranges cited, not single-point claims.')

    # ---- 03 insight ----
    page_header('A PPG sensor is already in every pocket', 'Why now')
    card(0.62, 1.75, 6.15, 4.9, fill=NAVY, line=None)
    c.setFillColor(white); c.setFont('Helvetica-Bold', 16)
    card(0.62, 1.55, 6.15, 4.35, fill=NAVY, line=None)
    c.setFillColor(white); c.setFont('Helvetica-Bold', 16)
    c.drawString(0.95*inch, 5.52*inch, 'Photoplethysmography (PPG), 101')
    wdraw(0.95, 5.10, 'Your fingertip is translucent; haemoglobin absorbs green light. Every beat '
                     'pumps blood — the green channel brightens and dims ~1x per second. Clinics '
                     'call this “reflectance PPG” when they put it in a Rs 60,000 pulse oximeter.',
          5.5, 13, color=HexColor('#C7D5E1'), leading=17)
    wdraw(0.95, 3.85, 'Smartphones have done this demo since 2013. The missing piece was never the '
                      'sensor — it was trustworthy on-device analysis.',
          5.5, 13, color=HexColor('#C7D5E1'), leading=17)
    wdraw(0.95, 2.75, 'Every beat is a data point. 60 s = ~70 beats of rhythm evidence, encoded in '
                      '12 HRV features.', 5.5, 13, color=HexColor('#2DD4BF'), bold=True, leading=17)
    right = [('Mobile penetration, rural India', '>90% of households; ~85% smartphones'),
             ('On-device AI is now 6 KB, not 600 MB', 'MLP 12->20->10->1 - ~2 ms - no cloud'),
             ('The workforce that can screen', '~10 lakh ASHA workers, door-to-door, daily')]
    for i, (t, v) in enumerate(right):
        y = 4.55 - i*1.5
        card(7.1, y, 5.6, 1.38, fill=white, line=LINE)
        c.setFillColor(MUTED); c.setFont('Helvetica', 12)
        c.drawString(7.35*inch, (y+1.05)*inch, t)
        c.setFillColor(TEAL); c.setFont('Helvetica-Bold', 15)
        c.drawString(7.35*inch, (y+0.52)*inch, v)
    footer()

    # ---- 04 how ----
    page_header('From fingertip to care decision in four steps', 'The solution')
    steps = [('1 · Cover the camera', 'Fingertip on the lens. Green-channel ROI is summed per frame — the image is never stored.'),
             ('2 · 60 seconds of signal', 'Live waveform + signal-quality meter. Motion is rejected, not “corrected”.'),
             ('3 · On-device AI reads it', '12 HRV features -> tiny neural net -> P(irregular rhythm). ~2 ms, offline.'),
             ('4 · One clear next step', 'Green -> routine. Amber -> repeat in 2 weeks. Red -> ECG within 7 days. EN / Hindi / Tamil.')]
    for i, (t, d) in enumerate(steps):
        x = 0.62 + i*3.06
        card(x, 2.4, 2.92, 3.0, fill=white, line=LINE)
        c.setFillColor(TEAL); c.roundRect(x*inch, 5.0*inch, 2.92*inch, 0.62*inch, 0.09*inch, stroke=0, fill=1)
        c.setFillColor(white); c.setFont('Helvetica-Bold', 13.5)
        c.drawCentredString((x+1.46)*inch, 5.19*inch, t)
        wdraw(x + 0.22, 4.68, d, 2.5, 11.5, color=MUTED, leading=15)
    c.setFillColor(INK); c.setFont('Helvetica-Bold', 13.5)
    c.drawString(0.62*inch, 2.05*inch, '…then the app writes the screening report on the spot — print, share, or file with the PHC.')
    footer()

    # ---- 05 product ----
    page_header('What the ASHA worker actually sees', 'The product')
    img('ui_mock.png', 0.62, 1.30, w=7.25)
    card(8.95, 1.62, 3.75, 4.3, fill=NAVY, line=None)
    c.setFillColor(HexColor('#2DD4BF')); c.setFont('Helvetica-Bold', 12)
    c.drawString(9.2*inch, 6.3*inch, 'BUILT AND SHIPPED')
    feats = ['Totally offline — no data leaves the phone',
             'English · Hindi · Tamil UI + voice questionnaire',
             'Live waveform, quality meter, live HR',
             'Guardrails: retake prompts · ±3σ hardening',
             'Printable screening report + local logbook',
             'Single-file build — runs from a USB stick']
    for i, t in enumerate(feats):
        c.setFillColor(HexColor('#2DD4BF')); c.setFont('Helvetica-Bold', 12)
        c.drawString(9.2*inch, (5.75 - i*0.62)*inch, '✓')
        wdraw(9.5, 5.72 - i*0.62, t, 3.0, 10.5, color=HexColor('#E2E8F0'), leading=13)
    footer()

    # ---- 06 signal ----
    page_header('The beat interval tells the story', 'The signal')
    img('tach_pair.png', 0.62, 1.75, w=8.35)
    c.setFillColor(INK); c.setFont('Helvetica-Bold', 12.5)
    c.drawString(0.62*inch, 2.35*inch, 'Each bar is one heartbeat. Healthy: bars march in step.')
    c.setFillColor(MUTED); c.setFont('Helvetica', 12)
    c.drawString(0.62*inch, 2.10*inch, 'AFib: bars wander chaotically — beat-to-beat differences explode. Our 12 features')
    c.drawString(0.62*inch, 1.87*inch, '(SDNN, RMSSD, pNN50, SD1/SD2, LF/HF, spectral entropy, turning-point ratio…')
    c.drawString(0.62*inch, 1.64*inch, 'are the same markers cardiologists read on 24-hour Holter tapes.')
    card(9.35, 1.75, 3.35, 3.9, fill=white, line=LINE)
    c.setFillColor(INK); c.setFont('Helvetica-Bold', 12.5)
    c.drawString(9.55*inch, 5.35*inch, 'Pipeline (in the phone)')
    pl = [('Detrend + band-pass FFT', 'removes motion baseline'),
          ('2-pass adaptive peak finder', 'drops false beats'),
          ('12 HRV features', 'clinical definitions'),
          ('Winsorise ±3σ -> MLP', '6 KB · ~2 ms'),
          ('Care level + report', 'quality guardrails')]
    for i, (a, b) in enumerate(pl):
        c.setFillColor(INK); c.setFont('Helvetica-Bold', 11)
        c.drawString(9.55*inch, (4.95 - i*0.55)*inch, a)
        wdraw(9.55, 4.72 - i*0.55, b, 2.95, 10, color=MUTED, leading=12)
    footer()

    # ---- 07 model ----
    page_header('A 6 KB classifier — trained and evaluated honestly', 'The AI')
    rows = [('Feature set', '12 HRV features (fixed, documented)', ''),
            ('Architecture', 'MLP 12->20->10->1, tanh/tanh/sigmoid', ''),
            ('Training data', '12,000 windows, PhysioNet-style synthetic PPG + augmentation', ''),
            ('Held-out validation', 'acc 99.5% · sens 99.6% · spec 99.4% · F1 0.996', '(synthetic distribution)'),
            ('Input hardening', '±3σ winsorisation + quality guard (Q<0.6 -> retake)', '')]
    yy = 5.88
    for i, (a, b, c3) in enumerate(rows):
        rh = 0.52
        c.setFillColor(white if i % 2 == 0 else LIGHT)
        c.rect(0.62*inch, (yy - rh)*inch, 7.6*inch, rh*inch, stroke=0, fill=1)
        c.setStrokeColor(LINE); c.setLineWidth(0.4)
        c.rect(0.62*inch, (yy - rh)*inch, 7.6*inch, rh*inch, stroke=1, fill=0)
        c.setFillColor(INK); c.setFont('Helvetica-Bold', 10.5)
        c.drawString(0.75*inch, (yy - rh + 0.19)*inch, a)
        c.setFillColor(INK); c.setFont('Helvetica', 10.5)
        c.drawString(2.5*inch, (yy - rh + 0.19)*inch, b[:52])
        c.setFillColor(MUTED); c.setFont('Helvetica', 9.5)
        c.drawString(7.0*inch, (yy - rh + 0.19)*inch, c3)
        yy -= rh + 0.03
    c.setFillColor(INK); c.setFont('Helvetica-Bold', 11.5)
    c.drawString(0.62*inch, 2.82*inch, 'Two reference implementations keep train and inference honest:')
    c.setFillColor(MUTED); c.setFont('Helvetica', 11.5)
    c.drawString(0.62*inch, 2.55*inch, 'tools/train_mlp.py (NumPy) and js/dsp.js are a line-for-line mirror — verified')
    c.drawString(0.62*inch, 2.30*inch, 'cross-language correlation ~ 0.998 — and 30 automated pipeline tests guard every release.')
    card(8.6, 2.62, 4.1, 3.0, fill=NAVY, line=None)
    c.setFillColor(HexColor('#2DD4BF')); c.setFont('Helvetica-Bold', 11.5)
    c.drawString(8.85*inch, 5.72*inch, 'WHAT IS VALIDATED vs NOT')
    c.setFillColor(HexColor('#E2E8F0')); c.setFont('Helvetica', 10.5)
    c.drawString(8.85*inch, 5.35*inch, '✓  End-to-end pipeline, deterministic, tested')
    c.drawString(8.85*inch, 4.95*inch, '✗  Real-patient benchmark (MIT-BIH AF/NSR)')
    c.drawString(8.85*inch, 4.72*inch, '    still pending — one-command retrain ships')
    c.drawString(8.85*inch, 4.49*inch, '    with the repo')
    c.setFillColor(HexColor('#2DD4BF')); c.setFont('Helvetica-Oblique', 10.5)
    c.drawString(8.85*inch, 3.85*inch, 'We show this on purpose: a screening tool that')
    c.drawString(8.85*inch, 3.62*inch, 'hides its limits is a hazard, not a product.')
    img('poincare_pair.png', 8.6, 0.58, w=4.1)
    footer()

    # ---- 08 trust ----
    page_header('Safety by guardrails, not by promises', 'Trust')
    cards = [('No images. Ever.', 'The camera ROI is summed to ONE number per frame inside the app. Nothing is stored, uploaded or mirrored — there is no server in the architecture.'),
             ('Guardrails not guesses', 'Quality < 0.6 -> “retake”. HR outside 40–180 -> retake. < 12 clean beats -> error, no verdict. The tool knows when it cannot read.'),
             ('Conservative by design', 'P < 0.35 green · 0.35–0.65 amber · > 0.65 red. Red says “ECG within 7 days” — never “you have AFib”.'),
             ('Honest limits, shipped', 'Synthetic-only validation disclosed in-app and in this deck; MIT-BIH retrain is one command. Screening ≠ diagnosis.')]
    for i, (t, d) in enumerate(cards):
        x = 0.62 + i*3.06
        card(x, 2.6, 2.92, 3.3, fill=white, line=LINE)
        c.setFillColor(TEAL); c.circle((x+0.52)*inch, 5.85*inch, 0.27*inch, stroke=0, fill=1)
        c.setFillColor(white); c.setFont('Helvetica-Bold', 14)
        c.drawCentredString((x+0.52)*inch, 5.70*inch, '✓')
        c.setFillColor(INK); c.setFont('Helvetica-Bold', 14)
        c.drawString((x+0.25)*inch, 5.25*inch, t)
        wdraw(x + 0.25, 4.90, d, 2.45, 11, color=MUTED, leading=14)
    footer('Ethics: our success metric is avoidable strokes prevented, not downloads — the benchmark script is public.')

    # ---- 09 scale ----
    page_header('Screening as a habit, not an event', 'At scale')
    rows = [('Rhythm screening today (rural PHC)', 'One-touch ECG Rs 45k–80k + technician + patient travel', '~Rs 300–800 / screened patient'),
            ('NadiSense (existing smartphone)', 'Rs 0 hardware, Rs 0 per test, ASHA worker in the field', '~Rs 0 incremental per screen'),
            ('One PHC circuit, 100 villages', 'One app on a phone already in the CHC budget', 'Screens every adult > 40')]
    yy = 6.0
    for i, (a, b, c3) in enumerate(rows):
        rh = 0.62
        c.setFillColor(HexColor('#0F766E') if i == 0 else (white if i % 2 else LIGHT))
        c.rect(0.62*inch, (yy - rh)*inch, 12.1*inch, rh*inch, stroke=0, fill=1)
        c.setStrokeColor(LINE); c.setLineWidth(0.4)
        c.rect(0.62*inch, (yy - rh)*inch, 12.1*inch, rh*inch, stroke=1, fill=0)
        c.setFillColor(white if i == 0 else INK)
        c.setFont('Helvetica-Bold', 11.5)
        c.drawString(0.78*inch, (yy - rh + 0.23)*inch, a[:46])
        c.setFillColor(white if i == 0 else INK); c.setFont('Helvetica', 11.5)
        c.drawString(5.2*inch, (yy - rh + 0.23)*inch, b[:48])
        c.setFillColor(HexColor('#2DD4BF') if i == 0 else TEAL)
        c.setFont('Helvetica-Bold', 11.5)
        c.drawString(10.2*inch, (yy - rh + 0.23)*inch, c3)
        yy -= rh + 0.04
    stats = [('Rs 0', 'hardware per screening', 'the phone already exists'),
             ('10K+', 'screens per PHC / year', 'one ASHA worker, 4 calls/day'),
             ('7 days', 'flag -> ECG in protocol', 'printed on the report'),
             ('~70 beats', 'of evidence per screen', 'at 30 samples/s, 2 ms analysis')]
    for i, (v, t, d) in enumerate(stats):
        x = 0.62 + i*3.06
        card(x, 1.5, 2.92, 2.0, fill=white, line=LINE)
        c.setFillColor(TEAL); c.setFont('Helvetica-Bold', 26)
        c.drawString((x+0.18)*inch, 3.1*inch, v)
        c.setFillColor(INK); c.setFont('Helvetica-Bold', 12)
        c.drawString((x+0.18)*inch, 2.72*inch, t)
        c.setFillColor(MUTED); c.setFont('Helvetica', 10.5)
        c.drawString((x+0.18)*inch, 2.42*inch, d[:34])
    footer()

    # ---- 10 roadmap ----
    page_header('From this build to a national screening programme', 'Roadmap')
    items = [('NOW · v0.9', 'Camera PPG + DSP + 6 KB MLP + vernacular UI, offline, report, tests. Delivered.', TEAL),
             ('Q4 2026 · v1.0', 'Retrain on MIT-BIH AF/NSR + local PHC pilot (2 circuits); clinical review', HexColor('#E11D48')),
             ('H1 2027 · v1.1', 'Multi-class rhythm model + follow-up scheduling + report handoff', HexColor('#D97706')),
             ('2027+ · v2.0', 'ASHA-assistant: screening calendar, hypertension/diabetes trends, ANM integration', TEAL)]
    for i, (t, d, col) in enumerate(items):
        x = 0.62 + i*3.06
        card(x, 2.2, 2.92, 3.7, fill=white, line=LINE)
        c.setFillColor(col); c.roundRect(x*inch, 5.5*inch, 2.92*inch, 0.58*inch, 0.08*inch, stroke=0, fill=1)
        c.setFillColor(white); c.setFont('Helvetica-Bold', 12.5)
        c.drawCentredString((x+1.46)*inch, 5.67*inch, t)
        wdraw(x + 0.22, 5.05, d, 2.5, 11.5, color=MUTED, leading=15)
    c.setFillColor(INK); c.setFont('Helvetica-Bold', 12.5)
    c.drawString(0.62*inch, 1.60*inch, 'The blocker is not engineering — it is clinical evidence. That is why the pilot is built into v1.0,')
    c.setFillColor(MUTED); c.setFont('Helvetica', 12)
    c.drawString(0.62*inch, 1.28*inch, 'and why every metric in this deck is reproducible from the repo.')
    footer()

    # ---- 11 business ----
    page_header('Who pays, and what the prize would buy', 'Business')
    card(0.62, 1.55, 6.0, 4.3, fill=white, line=LINE)
    c.setFillColor(INK); c.setFont('Helvetica-Bold', 14)
    c.drawString(0.9*inch, 5.58*inch, 'Customers')
    c.setFillColor(INK); c.setFont('Helvetica', 12)
    cust = [('State NHM / district health societies', 'screening programme software'),
            ('PHCs & CHCs', 'zero-cost screening layer over existing phones'),
            ('Insurers & TPAs', 'pre-policy and chronic-care risk screening'),
            ('CSR / NCD programmes', 'camps for factories, IT parks, districts')]
    for i, (a, b) in enumerate(cust):
        c.setFillColor(TEAL); c.setFont('Helvetica-Bold', 12)
        c.drawString(0.9*inch, (5.12 - i*0.62)*inch, '●')
        c.setFillColor(INK); c.setFont('Helvetica-Bold', 12)
        c.drawString(1.2*inch, (5.12 - i*0.62)*inch, a)
        wdraw(1.2, 4.93 - i*0.62, b, 4.9, 11, color=MUTED, leading=13)
    c.setFillColor(INK); c.setFont('Helvetica-Bold', 14)
    c.drawString(0.9*inch, 2.62*inch, 'Monetisation')
    wdraw(0.9, 2.28, 'Free for public health · per-active-screen SaaS for insurance/private · no '
                    'capex ever asked of a PHC.', 5.5, 11.5, color=MUTED, leading=14)
    card(6.9, 1.55, 5.8, 4.3, fill=NAVY, line=None)
    c.setFillColor(white); c.setFont('Helvetica-Bold', 15)
    c.drawString(7.2*inch, 6.3*inch, 'If we win Rs 1,00,000')
    plan = [('Rs 40,000', 'PhysioNet retrain + 2-week PHC pilot (2 circuits)'),
            ('Rs 25,000', 'field research: 200 ASHA-worker sessions, Hindi + Tamil'),
            ('Rs 20,000', 'clinical review & IRB pathway for v1.0'),
            ('Rs 15,000', 'open benchmark dataset + public model card')]
    for i, (a, b) in enumerate(plan):
        c.setFillColor(HexColor('#2DD4BF')); c.setFont('Helvetica-Bold', 13)
        c.drawString(7.2*inch, (5.05 - i*0.85)*inch, a)
        wdraw(8.2, 5.05 - i*0.85, b, 4.35, 11.5, color=HexColor('#E2E8F0'), leading=14)
    footer()

    # ---- 12 why win ----
    page_header('Three things this entry will not lose on', 'Why us')
    wins = [('HARDWARE-FREE', 'Rs 0 extra cost, zero calibration, the ASHA worker’s own phone. No competitor pitch survives “and it costs nothing to deploy”.'),
            ('TRULY ON-DEVICE', 'No uploads, no cloud, no accounts — privacy is the architecture. And zero server bills forever.'),
            ('HONEST ENGINEERING', 'Dual reference pipelines, 43 automated tests, disclosed validation limits, one-command retrain on real data. Judges can verify everything.')]
    for i, (t, d) in enumerate(wins):
        x = 0.62 + i*4.05
        card(x, 2.4, 3.9, 3.5, fill=white, line=LINE)
        c.setFillColor(TEAL); c.roundRect(x*inch, 5.6*inch, 3.9*inch, 0.6*inch, 0.09*inch, stroke=0, fill=1)
        c.setFillColor(white); c.setFont('Helvetica-Bold', 13.5)
        c.drawCentredString((x+1.95)*inch, 5.78*inch, t)
        wdraw(x + 0.28, 5.12, d, 3.35, 11.5, color=MUTED, leading=15)
    c.setFillColor(INK); c.setFont('Helvetica-Bold', 12.5)
    c.drawString(0.62*inch, 1.7*inch, 'And the demo is not a slide — open nadi.html, choose a scenario, and watch a real')
    c.setFillColor(MUTED); c.setFont('Helvetica', 12)
    c.drawString(0.62*inch, 1.42*inch, 'AFib-like trace move the needle to red in 60 seconds. We will do it live.')
    footer()

    # ---- 13 runbook ----
    page_header('Live demo runbook', 'Demo')
    rows = [('Scenario', 'Input', 'What the judges see'),
            ('A · Healthy rhythm', 'Demo -> “Normal sinus rhythm”', 'HR 72 bpm · needle green · “rhythm looks regular” · ~0% risk'),
            ('B · AFib-like', 'Demo -> “Atrial fibrillation-like”', 'HR ~95 bpm · needle red · “irregular — refer for ECG” · 99% risk'),
            ('C · Guardrail', 'Demo -> “Heavy motion”', 'Quality sinks to ~45% -> retake prompt. The app refuses to guess.'),
            ('D · Voice + report', 'Voice questionnaire (Hindi)', 'Vernacular Q&A -> printable on-device screening report'),
            ('E · Real capture', 'Camera + fingertip, any phone', 'Same pipeline on live PPG — waveform, HR, peaks, result')]
    yy = 5.88
    for i, row in enumerate(rows):
        rh = 0.58
        c.setFillColor(HexColor('#0F766E') if i == 0 else (white if i % 2 else LIGHT))
        c.rect(0.62*inch, (yy - rh)*inch, 12.1*inch, rh*inch, stroke=0, fill=1)
        c.setStrokeColor(LINE); c.setLineWidth(0.4)
        c.rect(0.62*inch, (yy - rh)*inch, 12.1*inch, rh*inch, stroke=1, fill=0)
        c.setFillColor(white if i == 0 else INK)
        c.setFont('Helvetica-Bold' if i == 0 else 'Helvetica', 10.5)
        c.drawString(0.78*inch, (yy - rh + 0.21)*inch, row[0][:26])
        c.setFillColor(white if i == 0 else INK); c.setFont('Helvetica', 10.5)
        c.drawString(3.4*inch, (yy - rh + 0.21)*inch, row[1][:34])
        c.setFillColor(HexColor('#2DD4BF') if i == 0 else MUTED)
        c.setFont('Helvetica-Bold' if i == 0 else 'Helvetica', 10)
        c.drawString(8.2*inch, (yy - rh + 0.21)*inch, row[2][:56])
        yy -= rh + 0.04
    c.setFillColor(MUTED); c.setFont('Helvetica', 11)
    c.drawString(0.62*inch, 1.85*inch, 'Full 3-minute presenter script and a 90-second video plan: deliverables/demo-script.md —')
    c.drawString(0.62*inch, 1.62*inch, 'the demo needs no internet, no account and no permissions (Demo Mode).')
    footer()

    # ---- 14 closing ----
    c.setFillColor(NAVY); c.rect(0, 0, W, H, stroke=0, fill=1)
    img('wave_banner_afib.png', 0, 0, w=13.333, h=1.5)
    c.setFillColor(white); c.setFont('Helvetica-Bold', 36)
    c.drawString(0.62*inch, H-1.7*inch, 'The ECG will never reach every village.')
    c.setFillColor(HexColor('#2DD4BF')); c.setFont('Helvetica-Bold', 28)
    c.drawString(0.62*inch, H-2.6*inch, 'So we brought the screen to the phone instead.')
    c.setFillColor(HexColor('#C7D5E1')); c.setFont('Helvetica', 15)
    c.drawString(0.62*inch, H-3.6*inch, '60 seconds. One phone. Zero hardware. A screening-grade rhythm check at the doorstep —')
    c.drawString(0.62*inch, H-3.85*inch, 'offline, vernacular, private, and honest about what it does and does not know yet.')
    c.setFillColor(TEAL); c.roundRect(0.62*inch, H-5.2*inch, 2.9*inch, 0.62*inch, 0.2*inch, stroke=0, fill=1)
    c.setFillColor(white); c.setFont('Helvetica-Bold', 13)
    c.drawCentredString(2.07*inch, H-5.06*inch, 'DEMO IN 60 SECONDS')
    c.setFillColor(HexColor('#2DD4BF')); c.setFont('Helvetica-Bold', 14)
    c.drawString(3.9*inch, H-4.85*inch, 'Team Matric Phase · Aditya Mehra · Abhishek Singh · Siddesh Wagh')
    c.setFillColor(HexColor('#94A3B8')); c.setFont('Helvetica', 11.5)
    c.drawString(3.9*inch, H-5.15*inch, 'Thakur College of Engineering and Technology · Mumbai University · Maharashtra')
    c.setFillColor(white); c.setFont('Helvetica', 14)
    c.drawString(0.62*inch, H-5.95*inch, 'Thank you — questions welcome at the demo table.')
    c.showPage()

    c.save()
    print('wrote', path, f'({os.path.getsize(path)//1024} KB)')

if __name__ == '__main__':
    os.makedirs(ASSETS, exist_ok=True)
    build_summary()
    build_deck()
