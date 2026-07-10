/* ============================================================
   VIRTUAL WINDOW — open a live window onto somewhere else.
   Live only: a window is a real camera or it isn't offered.
   ?id=<place> opens that place; otherwise the last one you had
   open, otherwise somewhere random with a live view.
   ============================================================ */
import { loadAll } from '../lib/data.js';
import { bestWindow, windowFor, liveFor } from '../lib/media.js';
import { State } from '../lib/state.js';
import { weatherInfo } from '../lib/culture.js';
import * as api from '../lib/api.js';
import * as yt from '../lib/yt.js';
import { el, qs } from '../lib/dom.js';

let mounted = null, clockTimer = null;

function toast(msg) {
  const t = qs('#toast');
  t.textContent = msg;
  t.classList.add('show');
  clearTimeout(t._h);
  t._h = setTimeout(() => t.classList.remove('show'), 2800);
}

function teardown() {
  if (mounted?.destroy) mounted.destroy();
  mounted = null;
  if (clockTimer) { clearInterval(clockTimer); clockTimer = null; }
  qs('#win-frame').innerHTML = '';   // yt.mount owns the frame's contents
  qs('#sill-plate').innerHTML = '';
}

function openWindow(place, pool) {
  teardown();
  State.setLastWindow(place.id);
  document.title = `${place.name} · Virtual Window`;

  const view = bestWindow(place);
  const frame = qs('#win-frame');

  const fail = () => {
    frame.innerHTML = '';
    frame.append(el('div', { class: 'frame-empty' },
      el('div', { class: 'big' }, '🌫️'),
      el('div', { class: 'why' }, `The window onto ${place.name} just went dark — that's live cameras for you. Hop somewhere else?`),
    ));
  };

  if (view?.yt) {
    mounted = yt.mount(frame, {
      videoId: view.yt, muted: true, controls: 0, onError: fail,
    });
  } else {
    fail();
  }

  /* sill */
  const sp = qs('#sill-place');
  sp.innerHTML = '';
  sp.append(
    `${place.emoji || '📍'} ${place.name}`,
    el('span', { class: 'where' }, `${place.country_flag || ''} ${place.country}`),
    ' ',
    el('span', { class: `badge ${view?.kind === 'window' ? 'badge-window' : 'badge-live'}` },
      el('span', { class: 'dot' }), view?.kind === 'window' ? 'Live · window view' : 'Live · street'),
  );
  const vl = qs('#visit-link');
  vl.hidden = false;
  vl.href = `location.html?id=${encodeURIComponent(place.id)}`;

  /* weather + local-time plate */
  api.weather(place.coordinates.lat, place.coordinates.lng).then(wx => {
    if (!wx) return;
    const info = weatherInfo(wx.code, wx.isDay);
    const plate = qs('#sill-plate');
    plate.innerHTML = '';
    const clock = el('span', { class: 'plate-clock' }, '–:–');
    plate.append(clock, el('span', {}, `${info.icon} ${wx.tempC}°C · ${info.label}`));
    const tick = () => {
      clock.textContent = new Date(Date.now() + wx.offsetSec * 1000)
        .toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', timeZone: 'UTC' });
    };
    tick();
    clockTimer = setInterval(tick, 30_000);
  });
}

async function boot() {
  const places = await loadAll();
  const withView = places.filter(p => windowFor(p) || liveFor(p));
  if (!withView.length) { toast('No live windows available right now.'); return; }

  const wanted = new URLSearchParams(location.search).get('id') || State.lastWindow;
  const first = withView.find(p => p.id === wanted)
    || withView[Math.floor(Math.random() * withView.length)];
  openWindow(first, withView);

  qs('#hop-btn').addEventListener('click', () => {
    const others = withView.filter(p => p.id !== State.lastWindow);
    const next = others[Math.floor(Math.random() * others.length)];
    openWindow(next, withView);
  });
}

window.addEventListener('pagehide', teardown);

boot().catch(err => { console.error(err); toast('The window stuck — check the console.'); });
