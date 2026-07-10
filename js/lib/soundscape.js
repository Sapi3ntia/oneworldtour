/* ============================================================
   SOUNDSCAPE — procedural ambient audio via the Web Audio API.
   No audio files needed: every location's "sound" is synthesised
   live from filtered noise + drones, so it works offline and never
   404s. Map a data sound filename → a synth recipe by keyword.
   ============================================================ */
const Soundscape = {
  ctx: null,
  master: null,
  voices: [],
  type: null,
  target: 0.22,

  /* Pick a recipe from a data filename like "arctic-wind.mp3". */
  typeFor(name) {
    if (!name) return null;
    const s = name.toLowerCase();
    if (s.includes('arctic'))    return 'wind-cold';
    if (s.includes('wind'))      return 'wind';
    if (s.includes('tidal') || s.includes('ocean') || s.includes('wave')) return 'waves';
    if (s.includes('waterfall')) return 'waterfall';
    if (s.includes('plaza') || s.includes('city')) return 'city';
    if (s.includes('wilderness') || s.includes('forest')) return 'forest';
    return 'wind';
  },

  label(type) {
    return ({
      'wind-cold': 'Arctic wind',
      'wind':      'Open-air breeze',
      'waves':     'Rolling waves',
      'waterfall': 'Rushing water',
      'city':      'City hum',
      'forest':    'Quiet wilderness'
    })[type] || 'Ambience';
  },

  _ensure() {
    if (this.ctx) return;
    const AC = window.AudioContext || window.webkitAudioContext;
    this.ctx = new AC();
    this.master = this.ctx.createGain();
    this.master.gain.value = 0;
    this.master.connect(this.ctx.destination);
  },

  _noise() {
    const len = this.ctx.sampleRate * 2;
    const buf = this.ctx.createBuffer(1, len, this.ctx.sampleRate);
    const data = buf.getChannelData(0);
    for (let i = 0; i < len; i++) data[i] = Math.random() * 2 - 1;
    const src = this.ctx.createBufferSource();
    src.buffer = buf; src.loop = true;
    return src;
  },

  /* A slow oscillator wired into an AudioParam to animate it. */
  _lfo(param, freq, depth, base) {
    const osc = this.ctx.createOscillator();
    const amp = this.ctx.createGain();
    osc.frequency.value = freq;
    amp.gain.value = depth;
    param.value = base;
    osc.connect(amp).connect(param);
    osc.start();
    this.voices.push(osc, amp);
  },

  _build(type) {
    const c = this.ctx;
    const out = c.createGain();
    out.gain.value = 1;
    out.connect(this.master);

    const noise = this._noise();
    this.voices.push(noise);

    if (type === 'wind' || type === 'wind-cold') {
      const bp = c.createBiquadFilter();
      bp.type = 'bandpass';
      bp.frequency.value = type === 'wind-cold' ? 900 : 520;
      bp.Q.value = 0.6;
      const gust = c.createGain();
      noise.connect(bp).connect(gust).connect(out);
      this._lfo(gust.gain, 0.08, 0.35, 0.45);          // slow gusting
      this._lfo(bp.frequency, 0.05, type === 'wind-cold' ? 260 : 160,
                              type === 'wind-cold' ? 900 : 520);
    }
    else if (type === 'waves') {
      const lp = c.createBiquadFilter();
      lp.type = 'lowpass'; lp.frequency.value = 650; lp.Q.value = 0.4;
      const swell = c.createGain();
      noise.connect(lp).connect(swell).connect(out);
      this._lfo(swell.gain, 0.13, 0.32, 0.4);           // rhythmic swell
      this._lfo(lp.frequency, 0.13, 220, 600);
    }
    else if (type === 'waterfall') {
      const hp = c.createBiquadFilter();
      hp.type = 'highpass'; hp.frequency.value = 450;
      const lp = c.createBiquadFilter();
      lp.type = 'lowpass'; lp.frequency.value = 5200;
      const g = c.createGain(); g.gain.value = 0.55;
      noise.connect(hp).connect(lp).connect(g).connect(out);
      this._lfo(g.gain, 0.5, 0.05, 0.55);               // subtle shimmer
    }
    else if (type === 'city') {
      // distant low rumble
      const lp = c.createBiquadFilter();
      lp.type = 'lowpass'; lp.frequency.value = 380;
      const rg = c.createGain(); rg.gain.value = 0.3;
      noise.connect(lp).connect(rg).connect(out);
      // two detuned low drones = the "hum"
      [58, 87].forEach((f, i) => {
        const o = c.createOscillator();
        o.type = 'triangle'; o.frequency.value = f;
        const og = c.createGain(); og.gain.value = i ? 0.05 : 0.08;
        o.connect(og).connect(out); o.start();
        this.voices.push(o, og);
      });
      this._lfo(rg.gain, 0.07, 0.12, 0.3);
    }
    else { // forest
      const bp = c.createBiquadFilter();
      bp.type = 'bandpass'; bp.frequency.value = 1100; bp.Q.value = 0.5;
      const g = c.createGain(); g.gain.value = 0.22;
      noise.connect(bp).connect(g).connect(out);
      this._lfo(g.gain, 0.06, 0.12, 0.22);              // gentle breeze
      this._lfo(bp.frequency, 0.04, 300, 1100);
    }

    noise.start();
  },

  start(type) {
    if (!type) return;
    this._ensure();
    if (this.ctx.state === 'suspended') this.ctx.resume();
    if (this.type === type && this.voices.length) {        // already running
      this.master.gain.cancelScheduledValues(this.ctx.currentTime);
      this.master.gain.linearRampToValueAtTime(this.target, this.ctx.currentTime + 1.2);
      return;
    }
    this._teardown();
    this.type = type;
    this._build(type);
    this.master.gain.cancelScheduledValues(this.ctx.currentTime);
    this.master.gain.setValueAtTime(0, this.ctx.currentTime);
    this.master.gain.linearRampToValueAtTime(this.target, this.ctx.currentTime + 1.6);
  },

  stop() {
    if (!this.ctx) return;
    this.master.gain.cancelScheduledValues(this.ctx.currentTime);
    this.master.gain.linearRampToValueAtTime(0, this.ctx.currentTime + 0.5);
    const t = this.type;
    setTimeout(() => { if (this.type === t) this._teardown(); }, 600);
  },

  _teardown() {
    this.voices.forEach(v => { try { v.stop && v.stop(); } catch (e) {} try { v.disconnect(); } catch (e) {} });
    this.voices = [];
    this.type = null;
  },

  get playing() { return !!this.type; }
};

export { Soundscape };
