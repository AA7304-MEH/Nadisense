/*
 * ppgcamera.js — fingertip camera PPG capture
 * --------------------------------------------
 * Uses the phone's camera as a reflectance photoplethysmograph: the
 * green channel of a small ROI (fingertip) tracks blood volume changes
 * with each beat. Frames are averaged down to ~30 Hz and timestamped.
 *
 * Why green? Haemoglobin absorbs green light strongly, so green-channel
 * pulsatility is the highest-contrast proxy for the pulse waveform.
 *
 * Design constraint honoured: NO image data ever leaves the device.
 * All processing is the mean of an NxN ROI per frame - nothing is
 * stored, nothing is uploaded.
 */

const PpgCamera = (() => {
  'use strict';

  class Source {
    constructor() {
      this.queue = [];        // {t, v}
      this.started = 0;
      this.stream = null;
      this.video = null;
      this.raf = 0;
    }

    async start(videoEl, roiSize = 24) {
      this.stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment', width: { ideal: 640 }, height: { ideal: 480 } },
        audio: false,
      });
      this.video = videoEl;
      this.video.srcObject = this.stream;
      await this.video.play();
      this.started = performance.now();

      // draw loop: read ROI from the live frame, push green-channel mean
      const ctx = document.createElement('canvas').getContext('2d', { willReadFrequently: true });
      const cw = roiSize, ch = roiSize;
      ctx.canvas.width = cw; ctx.canvas.height = ch;

      let lastPush = 0;
      const tick = () => {
        if (!this.stream) return;
        const t = this.video.currentTime;
        if (t !== lastPush) {
          lastPush = t;
          try {
            const w = this.video.videoWidth, h = this.video.videoHeight;
            const cx = w / 2, cy = h / 2;
            ctx.drawImage(this.video,
              cx - cw / 2, cy - ch / 2, cw, ch, 0, 0, cw, ch);
            const d = ctx.getImageData(0, 0, cw, ch).data;
            let g = 0;
            for (let i = 0; i < d.length; i += 4) g += d[i + 1]; // green channel
            this.queue.push({
              t: (performance.now() - this.started) / 1000,
              v: g / (d.length / 4),
            });
          } catch (e) { /* frame not ready yet — skip */ }
        }
        this.raf = requestAnimationFrame(tick);
      };
      this.raf = requestAnimationFrame(tick);
    }

    /* Uniform 30 Hz down-sampling of whatever we've collected. */
    read(secs) {
      const span = Math.max(1e-3, this.started ? (performance.now() - this.started) / 1000 - 0 : 0.001);
      const q = this.queue;
      const tEnd = q.length ? q[q.length - 1].t : 0;
      const tStart = Math.max(0, tEnd - secs);
      const out = new Float64Array(Math.floor(secs * 30));
      let j = 0;
      for (let i = 0; i < out.length; i++) {
        const g = tStart + secs * i / out.length;
        while (j < q.length - 1 && q[j].t < g) j++;
        const a = q[Math.max(0, j - 1)], b = q[Math.min(q.length - 1, j)];
        const d = Math.max(b.t - a.t, 1e-9);
        out[i] = a.v + (b.v - a.v) * ((g - a.t) / d);
      }
      return out;
    }

    stop() {
      cancelAnimationFrame(this.raf);
      if (this.stream) {
        this.stream.getTracks().forEach(t => t.stop());
        this.stream = null;
      }
      if (this.video) this.video.srcObject = null;
    }
  }

  return { Source };
})();

if (typeof module !== 'undefined') module.exports = PpgCamera;
