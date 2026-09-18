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

    // Try progressively simpler constraints so exotic devices / in-app
    // webviews that can't satisfy {facingMode,width,height} still work.
    // Any non-constraint error (blocked, busy, no camera…) is rethrown as-is
    // — the caller needs the real name to explain the fix to the user.
    async getStream() {
      const attempts = [
        { video: { facingMode: 'environment', width: { ideal: 640 }, height: { ideal: 480 } }, audio: false },
        { video: { facingMode: 'environment' }, audio: false },
        { video: true, audio: false },
      ];
      let last = null;
      for (const c of attempts) {
        try { return await navigator.mediaDevices.getUserMedia(c); }
        catch (e) {
          last = e;
          if (e.name !== 'OverconstrainedError' && e.name !== 'ConstraintNotSatisfiedError') throw e;
        }
      }
      throw last || new Error('camera constraints failed');
    }

    async start(videoEl, roiSize = 48) {     // 48x48 px: ≈4× more photons than 24 → cleaner pulse
      this.stream = await this.getStream();
      this.video = videoEl;
      this.video.srcObject = this.stream;
      await this.video.play();
      this.started = performance.now();

      // Fingertip PPG needs transmitted light: turn the torch ON if the
      // hardware supports it (Chrome/Android). Without it the red glow is
      // too weak and the capture correctly fails the quality gate.
      this.track = this.stream.getVideoTracks()[0] || null;
      this.torch = false;
      if (this.track) {
        try {
          const caps = this.track.getCapabilities ? this.track.getCapabilities() : {};
          if (caps && caps.torch) {
            await this.track.applyConstraints({ advanced: [{ torch: true }] });
            this.torch = true;
          }
        } catch (e) { /* torch unsupported or user-blocked — continue */ }
      }

      // draw loop: read ROI from the live frame, push green-channel mean.
      // Throttle by wall clock (not video.currentTime — that does not
      // advance on some desktop/UX stacks, which starved the queue and
      // crashed read()).
      const ctx = document.createElement('canvas').getContext('2d', { willReadFrequently: true });
      const cw = roiSize, ch = roiSize;
      ctx.canvas.width = cw; ctx.canvas.height = ch;

      let lastPushMs = 0;
      const tick = () => {
        if (!this.stream) return;
        const nowMs = performance.now();
        if (nowMs - lastPushMs >= 1000 / 30) {   // ~30 Hz sampling
          lastPushMs = nowMs;
          try {
            const w = this.video.videoWidth, h = this.video.videoHeight;
            if (w > 0 && h > 0 && this.video.readyState >= 2) { // HAVE_CURRENT_DATA
              const cx = w / 2, cy = h / 2;
              ctx.drawImage(this.video,
                cx - cw / 2, cy - ch / 2, cw, ch, 0, 0, cw, ch);
              const d = ctx.getImageData(0, 0, cw, ch).data;
              // capture ALL channels: with the flash pressed behind the
              // fingertip, GREEN often saturates (clips to 255 = flat);
              // transmissive-mode pulsatility then only survives in RED.
              // The consumer picks the usable channel per window.
              let r = 0, g = 0, b = 0;
              for (let i = 0; i < d.length; i += 4) { r += d[i]; g += d[i + 1]; b += d[i + 2]; }
              const npx = d.length / 4;
              const rM = r / npx, gM = g / npx, bM = b / npx;
              this.queue.push({
                t: (nowMs - this.started) / 1000,
                v: gM,            // legacy field = green mean (tests & old readers)
                r: rM, g: gM, b: bM,
              });
            }
          } catch (e) { /* frame not ready yet — skip */ }
        }
        this.raf = requestAnimationFrame(tick);
      };
      this.raf = requestAnimationFrame(tick);
    }

    /* Uniform 30 Hz right-edge window of whatever we've collected.
       * Safe on an empty queue: returns zeros (flat signal) so the DSP
       * layer can report "poor/insufficient signal" instead of crashing. */
    read(secs) {
      const q = this.queue;
      const n = Math.max(2, Math.floor(secs * 30));
      if (!q.length) return new Float64Array(n);      // no frames yet → flat
      const tEnd = q[q.length - 1].t;
      const tStart = Math.max(0, tEnd - secs);
      const out = new Float64Array(n);
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

    async _tryTorch() {
      if (!this.track) return false;
      try {
        const caps = this.track.getCapabilities ? this.track.getCapabilities() : {};
        if (!caps || !caps.torch) return false;
        await this.track.applyConstraints({ advanced: [{ torch: true }] });
        const st = this.track.getSettings ? this.track.getSettings() : {};
        return st.torch !== false;   // some browsers don't echo the setting
      } catch (e) { return false; }
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
