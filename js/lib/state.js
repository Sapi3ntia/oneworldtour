/* ============================================================
   STATE — localStorage-backed passport state. Same keys as v1
   (owt_*) so nobody loses their stamps in the redesign.
   ============================================================ */
const read = (k, fallback) => {
  try { return JSON.parse(localStorage.getItem(k)) ?? fallback; }
  catch { return fallback; }
};
const write = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch {} };

export const State = {
  get visited() { return read('owt_visited', []); },
  markVisited(id) {
    const v = this.visited;
    if (!v.includes(id)) { v.push(id); write('owt_visited', v); }
  },
  isVisited(id) { return this.visited.includes(id); },

  get saved() { return read('owt_saved', []); },
  isSaved(id) { return this.saved.includes(id); },
  toggleSaved(id) {
    const s = this.saved, i = s.indexOf(id);
    if (i >= 0) s.splice(i, 1); else s.push(id);
    write('owt_saved', s);
    return i < 0;
  },

  get notes() { return read('owt_notes', {}); },
  getNote(id) { return this.notes[id] || ''; },
  saveNote(id, text) {
    const n = this.notes; n[id] = text; write('owt_notes', n);
  },

  /* Flight departure point for the arrival animation. */
  get lastPos() { return read('owt_last_pos', null); },
  setLastPos(pos) { write('owt_last_pos', pos); },

  /* Last Virtual Window opened. */
  get lastWindow() { return read('owt_last_window', null); },
  setLastWindow(id) { write('owt_last_window', id); },

  get soundOff() { return read('owt_sound_off', false); },
  setSoundOff(v) { write('owt_sound_off', !!v); },
};
