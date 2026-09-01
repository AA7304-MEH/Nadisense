/*
 * asr.js — tiny wrapper around the Web Speech API for the
 * vernacular pre-screening questionnaire (en-IN / hi-IN / ta-IN).
 * Falls back to typing when the browser lacks speech recognition.
 */

const Asr = (() => {
  'use strict';

  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  let recog = null;

  function supported() { return !!SR; }

  /*
   * Recognise a single utterance returning the transcript via callback.
   * Kept promise-based with a 8 s timeout so the flow never hangs.
   */
  function once(langTag) {
    return new Promise((resolve, reject) => {
      if (!SR) return reject(new Error('unsupported'));
      try {
        recog = new SR();
        recog.lang = langTag || 'en-IN';
        recog.interimResults = false;
        recog.maxAlternatives = 1;
        let done = false;
        const finish = (err, txt) => {
          if (done) return;
          done = true;
          if (err) reject(err); else resolve(txt || '');
        };
        recog.onresult = (e) => finish(null, e.results[0][0].transcript);
        recog.onerror = (e) => finish(new Error(e.error || 'error'));
        recog.onend = () => finish(new Error('timeout'));
        recog.start();
        setTimeout(() => finish(new Error('timeout')), 8000);
      } catch (e) {
        reject(e);
      }
    });
  }

  function stop() { if (recog) { try { recog.stop(); } catch (e) {} } }

  return { supported, once, stop };
})();
