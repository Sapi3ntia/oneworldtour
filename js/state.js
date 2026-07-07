/* ============================================================
   STATE — single source of truth, localStorage backed
   ============================================================ */
const State = {
  currentLocation: null,
  filter: 'all',

  get visited() {
    return JSON.parse(localStorage.getItem('owt_visited') || '[]');
  },
  get notes() {
    return JSON.parse(localStorage.getItem('owt_notes') || '{}');
  },
  get saved() {
    return JSON.parse(localStorage.getItem('owt_saved') || '[]');
  },

  completion: {
    street_view_clicked: false,
    photos_viewed:       false,
    guide_read:          false
  },
  photosViewedCount: 0,

  markVisited(id) {
    const v = this.visited;
    if (!v.includes(id)) {
      v.push(id);
      localStorage.setItem('owt_visited', JSON.stringify(v));
    }
  },
  isVisited(id) { return this.visited.includes(id); },

  saveNote(id, text) {
    const n = this.notes;
    n[id] = text;
    localStorage.setItem('owt_notes', JSON.stringify(n));
  },
  getNote(id) { return this.notes[id] || ''; },

  isSaved(id) { return this.saved.includes(id); },
  toggleSaved(id) {
    const s = this.saved;
    const i = s.indexOf(id);
    if (i >= 0) s.splice(i, 1); else s.push(id);
    localStorage.setItem('owt_saved', JSON.stringify(s));
    return i < 0;   // true if now saved
  },

  /* ---- Trip planner: an ordered list of stops ---- */
  get trip() { return JSON.parse(localStorage.getItem('owt_trip') || '[]'); },
  inTrip(id) { return this.trip.includes(id); },
  _saveTrip(t) { localStorage.setItem('owt_trip', JSON.stringify(t)); },
  addTrip(id) {
    const t = this.trip;
    if (!t.includes(id)) { t.push(id); this._saveTrip(t); }
  },
  removeTrip(id) { this._saveTrip(this.trip.filter(x => x !== id)); },
  toggleTrip(id) {
    if (this.inTrip(id)) { this.removeTrip(id); return false; }
    this.addTrip(id); return true;
  },
  moveTrip(id, dir) {
    const t = this.trip, i = t.indexOf(id), j = i + dir;
    if (i < 0 || j < 0 || j >= t.length) return;
    [t[i], t[j]] = [t[j], t[i]];
    this._saveTrip(t);
  },
  clearTrip() { localStorage.removeItem('owt_trip'); },

  resetCompletion() {
    this.completion = { street_view_clicked: false, photos_viewed: false, guide_read: false };
    this.photosViewedCount = 0;
  },

  triggerInteraction(type) {
    if (type === 'photos_viewed') {
      this.photosViewedCount++;
      if (this.photosViewedCount >= 2) this.completion.photos_viewed = true;
    } else {
      this.completion[type] = true;
    }
  },

  getProgressPct() {
    const done = Object.values(this.completion).filter(Boolean).length;
    return Math.round((done / 3) * 100);
  },
  isComplete() { return Object.values(this.completion).every(Boolean); }
};

/* Shared geo helpers — great-circle distance, interpolation, bearing. */
const Geo = {
  km(a, b) {
    const R = 6371, toRad = d => d * Math.PI / 180;
    const dLat = toRad(b.lat - a.lat), dLng = toRad(b.lng - a.lng);
    const s = Math.sin(dLat / 2) ** 2 +
      Math.cos(toRad(a.lat)) * Math.cos(toRad(b.lat)) * Math.sin(dLng / 2) ** 2;
    return Math.round(2 * R * Math.asin(Math.sqrt(s)));
  },

  /* Point a fraction f (0..1) of the way along the great circle a→b. */
  interpolate(a, b, f) {
    const toRad = d => d * Math.PI / 180, toDeg = r => r * 180 / Math.PI;
    const lat1 = toRad(a.lat), lng1 = toRad(a.lng);
    const lat2 = toRad(b.lat), lng2 = toRad(b.lng);
    const d = 2 * Math.asin(Math.sqrt(
      Math.sin((lat2 - lat1) / 2) ** 2 +
      Math.cos(lat1) * Math.cos(lat2) * Math.sin((lng2 - lng1) / 2) ** 2));
    if (!d) return { lat: a.lat, lng: a.lng };
    const A = Math.sin((1 - f) * d) / Math.sin(d);
    const B = Math.sin(f * d) / Math.sin(d);
    const x = A * Math.cos(lat1) * Math.cos(lng1) + B * Math.cos(lat2) * Math.cos(lng2);
    const y = A * Math.cos(lat1) * Math.sin(lng1) + B * Math.cos(lat2) * Math.sin(lng2);
    const z = A * Math.sin(lat1) + B * Math.sin(lat2);
    return { lat: toDeg(Math.atan2(z, Math.hypot(x, y))), lng: toDeg(Math.atan2(y, x)) };
  },

  /* Initial compass bearing (deg, clockwise from north) for a→b. */
  bearing(a, b) {
    const toRad = d => d * Math.PI / 180, toDeg = r => r * 180 / Math.PI;
    const lat1 = toRad(a.lat), lat2 = toRad(b.lat), dLng = toRad(b.lng - a.lng);
    const y = Math.sin(dLng) * Math.cos(lat2);
    const x = Math.cos(lat1) * Math.sin(lat2) - Math.sin(lat1) * Math.cos(lat2) * Math.cos(dLng);
    return (toDeg(Math.atan2(y, x)) + 360) % 360;
  }
};
