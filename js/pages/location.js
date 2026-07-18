/* ============================================================
   LOCATION — arrive somewhere. One stage, four panes at once:
   🚶 walk (top-left) · 🚗 drive (top-right) · 🔴 live street cam
   (bottom-left) · 🪟 live window (bottom-right). Clicking a pane's
   bar enlarges it; clicking it again evens the grid back out.
   A scene that doesn't exist shows its honest gap in place, and a
   scene whose YouTube id has rotted empties its own pane live.
   🏛️ Monuments swap into the walk pane via chips above the grid.
   ============================================================ */
import { loadAll, byId, search } from '../lib/data.js';
import { tripsThrough } from '../lib/trips.js';
import { walkFor, driveFor, liveFor, windowFor, monumentsFor, sceneFlags } from '../lib/media.js';
import { State } from '../lib/state.js';
import { Culture, weatherInfo } from '../lib/culture.js';
import { Radio } from '../lib/radio.js';
import { channelsFor, tvGeneratedDate, mountHls } from '../lib/tv.js';
import { Soundscape } from '../lib/soundscape.js';
import * as api from '../lib/api.js';
import * as yt from '../lib/yt.js';
import { el, qs } from '../lib/dom.js';
import { lazyPhoto } from '../lib/photos.js';
import { km } from '../lib/geo.js';

const go = p => { location.href = `location.html?id=${encodeURIComponent(p.id)}`; };

function toast(msg) {
  const t = qs('#toast');
  t.textContent = msg;
  t.classList.add('show');
  clearTimeout(t._h);
  t._h = setTimeout(() => t.classList.remove('show'), 2800);
}

/* ---------------- the stage: four panes, one grid ---------------- */
const PANES = [
  { id: 'walk',   icon: '🚶', label: 'Walking tour', badge: 'badge-walk',
    resolve: walkFor,   ghost: 'No walking tour yet' },
  { id: 'drive',  icon: '🚗', label: 'Driving tour', badge: 'badge-drive',
    resolve: driveFor,  ghost: 'No driving tour yet' },
  { id: 'live',   icon: '🔴', label: 'Live cam', badge: 'badge-live', live: true,
    resolve: liveFor,   ghost: 'No live cam yet' },
  { id: 'window', icon: '🪟', label: 'Window', badge: 'badge-window', live: true,
    resolve: windowFor, ghost: 'No window yet' },
];

const stageState = { panes: new Map(), walkShowing: 'walk' };   // pane id → { node, mounted }

const GHOST_TIP = 'Nothing we could verify as real for this place yet — ' +
  'no loop or still ever stands in. It fills in when the pipeline finds one.';

function sourceBadge(media) {
  if (media?.source === 'curated') return 'hand-picked';
  if (media?.source === 'auto') return 'auto-found & vetted';
  return '';
}

/* One pane grows; clicking the grown pane's bar evens the grid out. */
function setFocus(id) {
  const grid = qs('#stage-grid');
  if (id && grid.dataset.focus !== id) grid.dataset.focus = id;
  else grid.removeAttribute('data-focus');
}

/* Replace a pane in place (grid position comes from source order). */
function swapPane(def, fresh) {
  const old = stageState.panes.get(def.id);
  if (old) {
    old.mounted?.destroy?.();
    old.node.replaceWith(fresh.node);
  } else {
    qs('#stage-grid').append(fresh.node);
  }
  stageState.panes.set(def.id, fresh);
}

/* Honest gap: the pane stays, dashed, and says why it's empty. */
function ghostPane(def, why) {
  const node = el('div', { class: 'quad quad-ghost', 'data-quad': def.id, title: why ? '' : GHOST_TIP },
    el('div', { class: 'quad-bar' },
      el('span', { class: `badge ${def.badge}` }, `${def.icon} ${def.label}`)),
    el('div', { class: 'frame quad-frame' },
      el('div', { class: 'frame-empty' },
        el('div', { class: 'big' }, '🌫️'),
        el('div', { class: 'why' }, why || `${def.ghost} — nothing fake stands in.`))),
  );
  return { node, mounted: null };
}

/* A playing pane. `view` lets monuments borrow the walk pane:
   { label, badge, icon, onDead } override the pane's own identity. */
function scenePane(place, def, media, view = {}) {
  const label = view.label || def.label;
  const frame = el('div', { class: 'frame quad-frame' });
  if (def.id === 'window') frame.classList.add('window-vignette');

  const node = el('div', { class: 'quad', 'data-quad': def.id },
    el('button', {
      class: 'quad-bar', title: 'Click to enlarge / shrink this pane',
      onclick: () => setFocus(def.id),
    },
      el('span', { class: `badge ${view.badge || def.badge}` },
        def.live ? el('span', { class: 'dot' }) : null,
        def.live ? label : `${view.icon || def.icon} ${label}`),
      media.title ? el('span', { class: 'quad-title' }, media.title) : null,
      el('span', { class: 'quad-src faint' }, sourceBadge(media)),
      el('span', { class: 'quad-zoom' }, '⛶'),
    ),
    frame,
  );

  const dead = view.onDead || (() => {
    // the id rotted — empty this pane honestly, in place
    toast(`That ${label.toLowerCase()} feed has gone offline — removed.`);
    swapPane(def, ghostPane(def,
      `The ${label.toLowerCase()} went dark — an honest gap until a new one is verified.`));
    if (qs('#stage-grid').dataset.focus === def.id) setFocus(null);
  });

  let mounted = null;
  if (media.yt) {
    mounted = yt.mount(frame, {
      videoId: media.yt,
      start: media.start || 0,
      muted: true,
      controls: def.id === 'window' ? 0 : 1,
      loop: def.id === 'window',
      onError: dead,
    });
  } else if (media.channel) {
    const ifr = el('iframe', {
      src: `https://www.youtube.com/embed/live_stream?channel=${media.channel}&autoplay=1&mute=1&modestbranding=1`,
      allow: 'autoplay; encrypted-media; fullscreen', allowfullscreen: true,
    });
    frame.appendChild(ifr);
    mounted = { destroy: () => ifr.remove() };
  }
  return { node, mounted };
}

/* 🏛️ Monuments share the walk pane (the seekable-video seat).
   Chips above the grid swap them in; the walk chip swaps back. */
function buildMonumentChips(place) {
  const bar = qs('#stage-tabs');
  const mons = monumentsFor(place);
  bar.innerHTML = '';
  if (!mons.length) { bar.hidden = true; return; }
  bar.hidden = false;

  const walkDef = PANES[0];
  const walk = walkFor(place);
  const setActive = key => {
    stageState.walkShowing = key;
    bar.querySelectorAll('.chip').forEach(c =>
      c.classList.toggle('active', c.dataset.key === key));
  };
  const showMonument = (mo, key) => {
    swapPane(walkDef, scenePane(place, walkDef,
      { yt: mo.yt, start: mo.start || 0, source: 'curated' },
      { label: mo.name, badge: 'badge-monu', icon: '🏛️',
        onDead: () => {
          toast(`The ${mo.name} video has rotted — removed.`);
          bar.querySelector(`[data-key="${key}"]`)?.remove();
          showWalk();
        } }));
    qs('#stage-grid').dataset.focus = 'walk';   // force, don't toggle
    setActive(key);
  };
  const showWalk = () => {
    swapPane(walkDef, walk ? scenePane(place, walkDef, walk) : ghostPane(walkDef));
    setActive('walk');
  };

  if (walk) {
    bar.append(el('button', { class: 'chip', 'data-key': 'walk',
      onclick: () => { if (stageState.walkShowing !== 'walk') showWalk(); },
    }, '🚶 Walking tour'));
  }
  mons.forEach((mo, i) => {
    const key = `mon-${i}`;
    bar.append(el('button', { class: 'chip', 'data-key': key,
      onclick: () => {
        if (stageState.walkShowing === key) { if (walk) showWalk(); return; }
        showMonument(mo, key);
      },
    }, `🏛️ ${mo.name}`));
  });

  // no walk? the first monument takes the seat rather than a ghost
  if (walk) setActive('walk');
  else showMonument(mons[0], 'mon-0');
}

function initStage(place) {
  const grid = qs('#stage-grid');
  grid.innerHTML = '';
  stageState.panes.clear();
  stageState.walkShowing = 'walk';

  for (const def of PANES) {
    const media = def.resolve(place);
    const pane = media ? scenePane(place, def, media) : ghostPane(def);
    grid.append(pane.node);
    stageState.panes.set(def.id, pane);
  }

  buildMonumentChips(place);   // may hand the walk pane to a monument

  // feature the first real scene so arrival has a main view
  // (direct set, not setFocus — that one toggles on repeat clicks)
  const first = (walkFor(place) || monumentsFor(place).length)
    ? PANES[0] : PANES.find(d => d.resolve(place));
  if (first) grid.dataset.focus = first.id;
  else grid.removeAttribute('data-focus');
}

/* ---------------- right now ---------------- */
let clockTimer = null;
async function initRightNow(place) {
  const wx = await api.weather(place.coordinates.lat, place.coordinates.lng);
  const wEl = qs('#rn-weather');
  if (wx) {
    const info = weatherInfo(wx.code, wx.isDay);
    wEl.innerHTML = '';
    wEl.append(
      el('span', { class: 'wx-icon' }, info.icon),
      `${wx.tempC}°C · ${info.label}`,
    );
    const tick = () => {
      const local = new Date(Date.now() + wx.offsetSec * 1000);
      qs('#rn-clock').textContent = local.toLocaleTimeString('en-GB',
        { hour: '2-digit', minute: '2-digit', second: '2-digit', timeZone: 'UTC' });
    };
    tick();
    clockTimer = setInterval(tick, 1000);
  } else {
    wEl.innerHTML = '<span class="faint">sky unknown right now</span>';
    qs('#rn-clock').textContent = '–:–';
  }

  /* ambience */
  const btn = qs('#ambience-btn');
  const type = Soundscape.typeFor((place.sounds || [])[0]);
  btn.addEventListener('click', () => {
    if (Soundscape.playing) {
      Soundscape.stop();
      btn.classList.remove('on');
      btn.textContent = '🔊 Ambience';
    } else {
      Soundscape.start(type || 'wind');
      btn.classList.add('on');
      btn.textContent = `🔊 ${Soundscape.label(type || 'wind')}`;
    }
  });
}

/* ---------------- panels ---------------- */
async function initAbout(place) {
  const t = qs('#about-text');
  t.textContent = place.blurb || '…';
  const extract = await api.wikiSummary(place.wikipedia_slug);
  if (extract && extract.length > (place.blurb || '').length) {
    t.textContent = extract;
  }
  if (place.fun_fact) {
    const ff = qs('#fun-fact');
    ff.hidden = false;
    ff.append(el('b', {}, 'Did you know? '), place.fun_fact);
  }
  if (place.aa_claim) {
    const aa = qs('#aa-panel');
    aa.hidden = false;
    aa.append(
      el('b', {}, `🤫 Ancient Apocalypse · S${place.aa_season || 1} E${place.aa_episode || '?'} `),
      el('div', {}, place.aa_claim),
    );
  }
  const hl = qs('#highlights');
  for (const h of (place.highlights || []).slice(0, 8)) {
    hl.append(el('span', { class: 'hl' }, `✦ ${h.name}`));
  }
}

function initCulture(place) {
  const c = Culture.get(place.country);
  const facts = Culture.facts(place.country);
  const panel = qs('#culture-panel');
  const body = qs('#culture-body');
  panel.hidden = false;
  const row = (k, v) => el('div', { class: 'culture-row' }, el('span', { class: 'k' }, k), el('div', {}, v));
  body.append(...[
    row('Language', c.lang),
    row('Currency', c.currency),
    row('Eat this', c.dish),
    ...(c.phrases || []).map(([en, native]) =>
      row(en, el('div', { class: 'phrase' }, el('span', { class: 'native' }, native)))),
    facts ? row('Fast facts', `${facts.capital} · pop ${facts.pop} · drives ${facts.drives?.toLowerCase()}`) : null,
  ].filter(Boolean));
  /* live FX — quiet best-effort */
  const cur = Culture.currencyCode(place.country);
  if (cur && cur !== 'USD') {
    api.rates('USD').then(r => {
      if (r?.[cur]) body.append(row('1 USD', `${r[cur].toFixed(2)} ${cur} right now`));
    });
  }
}

async function initRadio(place) {
  const code = place.country_code || Culture.code(place.country);
  if (!code) return;
  const list = await api.stations(code, 10);
  if (!list.length) return;
  qs('#radio-panel').hidden = false;
  const wrap = qs('#radio-list');
  const items = new Map();
  const stateIcon = { loading: '…', playing: '🔊', error: '⚠️', stopped: '▸' };
  Radio.onState((state, station) => {
    for (const [st, node] of items) {
      const on = station && st.url === station.url && state !== 'stopped' && state !== 'error';
      node.classList.toggle('playing', on);
      node.querySelector('.r-state').textContent = on ? (stateIcon[state] || '▸') : '▸';
    }
    if (state === 'error') toast('That station wouldn\'t stream — try another.');
  });
  for (const s of list) {
    const node = el('button', {
      class: 'radio-item',
      onclick: () => {
        if (Radio.playing && Radio.current?.url === s.url) Radio.stop();
        else Radio.play(s);
      },
    },
      el('span', { class: 'r-state' }, '▸'),
      el('span', { class: 'r-name' }, s.name),
      s.tags.length ? el('span', { class: 'r-tags' }, s.tags.slice(0, 2).join(' · ')) : null,
    );
    items.set(s, node);
    wrap.append(node);
  }
}

/* ---------------- live tv ----------------
   National channels for this place's country — every one verified
   actually live when data/tv.json was generated. Same honesty rules
   as the stage: a feed that rots removes itself with a toast. Sound
   is on (a user click started it), so starting TV stops the radio
   and starting the radio stops the TV. */
const tvState = { mounted: null, active: null };

function stopTv() {
  if (tvState.mounted?.destroy) tvState.mounted.destroy();
  tvState.mounted = null;
  tvState.active = null;
  const frame = qs('#tv-frame');
  if (frame) { frame.hidden = true; frame.innerHTML = ''; }
  qs('#tv-list')?.querySelectorAll('.tv-item.playing')
    .forEach(n => { n.classList.remove('playing'); n.querySelector('.t-state').textContent = '▸'; });
}

async function initTv(place) {
  const code = place.country_code || Culture.code(place.country);
  const chans = await channelsFor(code);
  if (!chans.length) return;
  qs('#tv-panel').hidden = false;

  const when = await tvGeneratedDate();
  qs('#tv-note').textContent =
    `What ${place.country} broadcasts, live — national channels, verified streaming${when ? ' as of ' + when : ''}.`;

  const frame = qs('#tv-frame'), list = qs('#tv-list');
  const drop = (ch, node) => {
    stopTv();
    node.remove();
    toast(`${ch.name} wouldn't stream right now — removed.`);
    if (!list.children.length) qs('#tv-panel').hidden = true;
  };

  for (const ch of chans) {
    const node = el('button', { class: 'tv-item' },
      el('span', { class: 't-state' }, '▸'),
      el('span', { class: 't-name' }, ch.name),
      ch.lang ? el('span', { class: 't-lang' }, ch.lang) : null,
    );
    node.addEventListener('click', () => {
      if (tvState.active === ch) { stopTv(); return; }
      stopTv();
      Radio.stop();
      tvState.active = ch;
      frame.hidden = false;
      frame.innerHTML = '';
      if (ch.yt) {
        tvState.mounted = yt.mount(frame, {
          videoId: ch.yt, muted: false, onError: () => drop(ch, node),
        });
      } else {
        tvState.mounted = mountHls(frame, ch.url, { onError: () => drop(ch, node) });
      }
      node.classList.add('playing');
      node.querySelector('.t-state').textContent = '🔊';
    });
    list.append(node);
  }

  // the radio list starting a station is the cue to quiet the TV
  qs('#radio-list')?.addEventListener('click', ev => {
    if (ev.target.closest('.radio-item') && tvState.active) stopTv();
  });
}

async function initNews(place) {
  const arts = await api.news(place.name, place.country, 5);
  if (!arts.length) return;   // GDELT rate-limits — hide honestly
  qs('#news-panel').hidden = false;
  const ul = qs('#news-list');
  for (const a of arts) {
    const when = a.seendate ? `${a.seendate.slice(6, 8)}/${a.seendate.slice(4, 6)}` : '';
    ul.append(el('li', {}, el('a', { href: a.url, target: '_blank', rel: 'noopener' },
      a.title, el('span', { class: 'n-src' }, `${a.domain}${when ? ' · ' + when : ''}`))));
  }
}

async function initGallery(place) {
  const photos = await api.galleryPhotos(place.wikipedia_slug, 4);
  if (!photos.length) return;
  qs('#gallery-panel').hidden = false;
  const g = qs('#gallery');
  for (const src of photos) g.append(el('img', { src, loading: 'lazy', alt: place.name }));
}

function initGuide(place) {
  const form = qs('#guide-form'), input = qs('#guide-q'), log = qs('#guide-log');
  form.addEventListener('submit', async ev => {
    ev.preventDefault();
    const q = input.value.trim();
    if (!q) return;
    input.value = '';
    log.append(el('div', { class: 'g-q' }, q));
    const a = el('div', { class: 'g-a' }, '…');
    log.append(a);
    a.textContent = await api.askGuide(place.name, q,
      `${place.name}, ${place.country}. ${place.blurb || ''}`);
  });
}

/* ---------------- "you're on a route" ----------------
   With ?trip=, this place is a numbered stop and the strip carries you
   onward. Without it, we still say which curated routes pass through —
   that's how most people find the trips at all. */
async function initTripStrip(place) {
  const wanted = new URLSearchParams(location.search).get('trip');
  const through = await tripsThrough(place.id).catch(() => []);
  if (!through.length) return;

  const strip = qs('#trip-strip');
  const active = wanted ? through.find(t => t.trip.id === wanted) : null;

  if (!active) {
    /* passive: this place happens to be on curated routes */
    const links = [];
    through.slice(0, 3).forEach(({ trip }, i) => {
      if (i) links.push(' · ');
      links.push(el('a', { href: `trips.html?id=${encodeURIComponent(trip.id)}` },
        `${trip.emoji} ${trip.name}`));
    });
    strip.append(
      el('span', { class: 'ts-name' }, '🧭 On the route:'),
      el('span', { class: 'ts-where' }, links),
    );
    strip.hidden = false;
    return;
  }

  const { trip, index } = active;
  const prev = index > 0 ? trip.stops[index - 1] : null;
  const next = index < trip.stops.length - 1 ? trip.stops[index + 1] : null;
  const href = s => `location.html?id=${encodeURIComponent(s.place.id)}&trip=${encodeURIComponent(trip.id)}`;

  strip.append(
    el('span', { class: 'ts-name' },
      el('a', { href: `trips.html?id=${encodeURIComponent(trip.id)}` },
        `${trip.emoji} ${trip.name}`)),
    el('span', { class: 'ts-where' },
      `Stop ${index + 1} of ${trip.stops.length}` + (next ? '' : ' · end of the road')),
    el('span', { class: 'ts-dots' },
      trip.stops.map((s, i) => el('span', {
        class: 'ts-dot' + (i === index ? ' here' : State.isVisited(s.place.id) ? ' done' : ''),
        title: `${i + 1}. ${s.place.name}`,
      }))),
    el('span', { class: 'ts-nav' },
      prev ? el('a', { class: 'btn btn-sm', href: href(prev) }, `← ${prev.place.name}`) : null,
      next ? el('a', { class: 'btn btn-sm btn-gold', href: href(next) }, `${next.place.name} →`) : null,
    ),
  );
  strip.hidden = false;
}

async function initNearby(place, places) {
  const near = places
    .filter(p => p.id !== place.id)
    .map(p => ({ p, d: km(place.coordinates, p.coordinates) }))
    .sort((a, b) => a.d - b.d)
    .slice(0, 10);
  const railEl = qs('#next-rail');
  for (const { p, d } of near) {
    const f = sceneFlags(p);
    const card = el('a', { class: 'card place-card', href: `location.html?id=${encodeURIComponent(p.id)}` },
      el('div', { class: 'ph' }, p.emoji || '📍'),
      el('div', { class: 'badges' },
        f.live ? el('span', { class: 'badge badge-live' }, el('span', { class: 'dot' }), 'Live') : null,
        f.walk ? el('span', { class: 'badge badge-walk' }, '🚶') : null,
      ),
      el('div', { class: 'meta' },
        el('div', { class: 'name' }, p.name),
        el('div', { class: 'sub' }, `${p.country_flag || ''} ${p.country} · ${d.toLocaleString()} km`),
      ),
    );
    lazyPhoto(card.querySelector('.ph'), p, 480);
    railEl.append(card);
  }
}

/* ---------------- boot ---------------- */
async function boot() {
  const id = new URLSearchParams(location.search).get('id');
  const places = await loadAll();
  const place = places.find(p => p.id === id);
  if (!place) {
    qs('#notfound').hidden = false;
    return;
  }
  qs('#page').hidden = false;
  document.title = `${place.name} — One World Tour`;

  /* header */
  qs('#kicker').textContent =
    `${place.country_flag || '🌍'} ${place.country} · ${place.continent || ''}${place.collection ? ' · ' + place.collection : ''}`;
  qs('#place-name').textContent = `${place.emoji || ''} ${place.name}`.trim();
  qs('#blurb').textContent = place.blurb || '';

  const saveBtn = qs('#save-btn');
  const syncSave = () => {
    saveBtn.classList.toggle('on', State.isSaved(place.id));
    saveBtn.textContent = State.isSaved(place.id) ? '♥ Saved' : '♥ Save';
  };
  syncSave();
  saveBtn.addEventListener('click', () => { State.toggleSaved(place.id); syncSave(); });

  qs('#note-btn').addEventListener('click', () => {
    const cur = State.getNote(place.id);
    const txt = prompt(`Your note for ${place.name}:`, cur);
    if (txt !== null) { State.saveNote(place.id, txt); toast('Noted in your passport 📘'); }
  });

  if (windowFor(place) || liveFor(place)) {
    const wl = qs('#window-link');
    wl.hidden = false;
    wl.href = `window.html?id=${encodeURIComponent(place.id)}`;
  }

  qs('#surprise-top').addEventListener('click', () => {
    go(places[Math.floor(Math.random() * places.length)]);
  });

  State.markVisited(place.id);
  State.setLastPos({ lat: place.coordinates.lat, lng: place.coordinates.lng, id: place.id });

  /* scenes + panels (all independent; failures stay local) */
  initStage(place);
  initRightNow(place);
  initAbout(place);
  initCulture(place);
  initRadio(place);
  initTv(place);
  initNews(place);
  initGallery(place);
  initGuide(place);
  initTripStrip(place);
  initNearby(place, places);
}

window.addEventListener('pagehide', () => {
  if (clockTimer) clearInterval(clockTimer);
  Radio.stop();
  stopTv();
  if (Soundscape.playing) Soundscape.stop();
});

boot().catch(err => {
  console.error(err);
  toast('Something broke on arrival — check the console.');
});
