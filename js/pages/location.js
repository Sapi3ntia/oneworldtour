/* ============================================================
   LOCATION — arrive somewhere. One stage, tab-switchable scenes:
   🚶 walk · 🏛️ each monument · 🔴 live street cam · 🪟 live window.
   Scenes that don't exist simply aren't offered (honest gaps).
   A scene whose YouTube id has rotted removes its own tab live.
   ============================================================ */
import { loadAll, byId, search } from '../lib/data.js';
import { walkFor, liveFor, windowFor, monumentsFor, sceneFlags } from '../lib/media.js';
import { State } from '../lib/state.js';
import { Culture, weatherInfo } from '../lib/culture.js';
import { Radio } from '../lib/radio.js';
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

/* ---------------- the stage ---------------- */
const stageState = { mounted: null, scenes: [], active: null };

function destroyStage() {
  if (stageState.mounted?.destroy) stageState.mounted.destroy();
  stageState.mounted = null;
  const stage = qs('#stage');
  stage.innerHTML = '';   // yt.mount owns the host's contents — rebuild empties on demand
  stage.classList.remove('window-vignette');
}

function sourceBadge(scene) {
  if (scene.media?.source === 'curated') return 'hand-picked';
  if (scene.media?.source === 'auto') return 'auto-found & vetted';
  return '';
}

function showEmptyStage(place) {
  const stage = qs('#stage');
  let e = stage.querySelector('.frame-empty');
  if (!e) { e = el('div', { class: 'frame-empty' }); stage.appendChild(e); }
  e.hidden = false;
  e.innerHTML = '';
  e.append(
    el('div', { class: 'big' }, '🌫️'),
    el('div', { class: 'why' },
      `No scenes for ${place.name} yet — no walking tour or live cam we could honestly verify. `,
      'They fill in city by city; nothing fake stands in meanwhile.'),
  );
  e.hidden = false;
}

function renderScene(place, scene) {
  destroyStage();
  stageState.active = scene.id;
  const stage = qs('#stage');
  const cap = qs('#stage-caption');
  cap.innerHTML = '';

  const dead = () => {
    // the id rotted — remove this tab honestly and move on
    stageState.scenes = stageState.scenes.filter(s => s.id !== scene.id);
    buildTabs(place);
    toast(`That ${scene.kindLabel.toLowerCase()} feed has gone offline — removed.`);
    const next = stageState.scenes[0];
    if (next) renderScene(place, next);
    else { destroyStage(); showEmptyStage(place); }
  };

  const m = scene.media;
  if (m?.yt) {
    stageState.mounted = yt.mount(stage, {
      videoId: m.yt,
      start: m.start || 0,
      muted: true,
      controls: scene.id === 'window' ? 0 : 1,
      loop: scene.id === 'window',
      onError: dead,
    });
  } else if (m?.channel) {
    const ifr = el('iframe', {
      src: `https://www.youtube.com/embed/live_stream?channel=${m.channel}&autoplay=1&mute=1&modestbranding=1`,
      allow: 'autoplay; encrypted-media; fullscreen', allowfullscreen: true,
    });
    stage.appendChild(ifr);
    stageState.mounted = { destroy: () => ifr.remove() };
  }

  if (scene.id === 'window') stage.classList.add('window-vignette');

  /* caption: honesty badges */
  const badgeCls = { walk: 'badge-walk', live: 'badge-live', window: 'badge-window', monument: 'badge-monu' }[scene.type];
  cap.append(...[
    el('span', { class: `badge ${badgeCls}` },
      scene.type === 'live' || scene.type === 'window' ? el('span', { class: 'dot' }) : null,
      scene.kindLabel),
    m?.title ? el('span', {}, m.title) : null,
    el('span', { class: 'faint' }, sourceBadge(scene)),
    scene.type === 'walk' ? el('span', { class: 'faint' }, 'muted · seek freely') : null,
    scene.type === 'window' ? el('span', { class: 'faint' }, 'a real live view — not a loop') : null,
  ].filter(Boolean));
  buildTabs(place);
}

function buildTabs(place) {
  const bar = qs('#stage-tabs');
  bar.innerHTML = '';
  for (const s of stageState.scenes) {
    bar.append(el('button', {
      class: 'chip' + (s.id === stageState.active ? ' active' : ''),
      onclick: () => renderScene(place, s),
    },
      (s.type === 'live' || s.type === 'window') ? el('span', { class: 'live-dot' }) : null,
      s.tabLabel,
    ));
  }
  // honest gaps stay visible — a missing scene is a fact, not a bug.
  // (Also reappears when a rotted feed removes its own tab.)
  const ghosts = [
    ['walk', '🚶 no walking tour yet'],
    ['live', '🔴 no live cam yet'],
    ['window', '🪟 no window yet'],
  ];
  for (const [id, label] of ghosts) {
    if (stageState.scenes.some(s => s.id === id)) continue;
    bar.append(el('span', {
      class: 'chip chip-ghost',
      title: 'Nothing we could verify as real for this place yet — no loop or still ever stands in. It fills in when the pipeline finds one.',
    }, label));
  }
}

function initStage(place) {
  const scenes = [];
  const walk = walkFor(place);
  if (walk) scenes.push({ id: 'walk', type: 'walk', tabLabel: '🚶 Walking tour', kindLabel: 'Walking tour', media: walk });
  for (const [i, mo] of monumentsFor(place).entries()) {
    scenes.push({
      id: `mon-${i}`, type: 'monument',
      tabLabel: `🏛️ ${mo.name}`, kindLabel: mo.name,
      media: { yt: mo.yt, start: mo.start || 0, source: 'curated' },
    });
  }
  const live = liveFor(place);
  if (live) scenes.push({ id: 'live', type: 'live', tabLabel: 'Live cam', kindLabel: 'Live · street', media: live });
  const win = windowFor(place);
  if (win) scenes.push({ id: 'window', type: 'window', tabLabel: 'Window', kindLabel: 'Live · window view', media: win });

  stageState.scenes = scenes;
  if (scenes.length) renderScene(place, scenes[0]);
  else { destroyStage(); showEmptyStage(place); buildTabs(place); }
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
  initNews(place);
  initGallery(place);
  initGuide(place);
  initNearby(place, places);
}

window.addEventListener('pagehide', () => {
  if (clockTimer) clearInterval(clockTimer);
  Radio.stop();
  if (Soundscape.playing) Soundscape.stop();
});

boot().catch(err => {
  console.error(err);
  toast('Something broke on arrival — check the console.');
});
