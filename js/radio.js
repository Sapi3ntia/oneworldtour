/* ============================================================
   RADIO — plays live local radio streams through a single
   <audio> element. Streams come from the Radio Browser API
   (see API.getStations). No CORS crossOrigin is set, so the
   browser can play stations that don't send CORS headers
   (most of them); the equaliser is a CSS animation, not a
   real analyser, for that reason.
   States emitted: 'loading' | 'playing' | 'error' | 'stopped'
   ============================================================ */
const Radio = {
  _audio: null,
  _onState: null,
  current: null,

  _el() {
    if (!this._audio) {
      const a = new Audio();
      a.preload = 'none';
      a.volume = 0.85;
      a.onplaying = () => this._emit('playing');
      a.onerror   = () => this._emit('error');
      a.onstalled = () => this._emit('loading');
      a.onwaiting = () => this._emit('loading');
      this._audio = a;
    }
    return this._audio;
  },

  onState(cb) { this._onState = cb; },

  play(station) {
    const a = this._el();
    this.current = station;
    this._emit('loading');
    a.src = station.url;
    const p = a.play();
    if (p && p.catch) p.catch(() => this._emit('error'));
  },

  stop() {
    if (!this._audio) return;
    this._audio.pause();
    this._audio.removeAttribute('src');
    try { this._audio.load(); } catch (e) {}
    this.current = null;
    this._emit('stopped');
  },

  get playing() {
    return !!(this._audio && this.current && !this._audio.paused);
  },

  setVolume(v) { this._el().volume = Math.max(0, Math.min(1, v)); },

  _emit(state) { if (this._onState) this._onState(state, this.current); }
};
