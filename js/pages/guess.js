/* ============================================================
   CITY GUESSER — dropped into a mystery scene, pin it on the map.
   Scored GeoGuessr-style on great-circle distance, 5 rounds.
   The guess map is the same SVG engine as home, in 'pick' mode —
   clicks come back as exact lat/lng via the projection inverse.
   ============================================================ */
import { loadAll } from '../lib/data.js';
import { walkFor } from '../lib/media.js';
import { WorldMap } from '../worldmap.js';
import { km } from '../lib/geo.js';
import * as yt from '../lib/yt.js';
import { el, qs } from '../lib/dom.js';
import { photoFor } from '../lib/photos.js';

const ROUNDS = 5;
const MAX_PTS = 5000;
const SCALE_KM = 2000;
const BULLSEYE_KM = 25;

let pool = [], order = [], regionFilter = 'all';
let round = 0, total = 0, results = [];
let guess = null, phase = 'idle', mounted = null;
let map;

function toast(msg) {
  const t = qs('#toast');
  t.textContent = msg;
  t.classList.add('show');
  clearTimeout(t._h);
  t._h = setTimeout(() => t.classList.remove('show'), 2600);
}

const active = () => regionFilter === 'all' ? pool : pool.filter(l => l.region_id === regionFilter);

/* ---------------- start screen ---------------- */
function showStart() {
  qs('#g-start').hidden = false;
  qs('#g-game').hidden = true;
  qs('#g-final').hidden = true;
  const regions = new Map();
  for (const l of pool) {
    const r = regions.get(l.region_id) || { id: l.region_id, name: l.region_name, flag: l.region_flag, count: 0 };
    r.count++;
    regions.set(l.region_id, r);
  }
  const wrap = qs('#g-regions');
  wrap.innerHTML = '';
  const chip = (id, flag, name, count) => el('button', {
    class: 'chip' + (id === regionFilter ? ' active' : ''),
    onclick: ev => {
      regionFilter = id;
      for (const c of wrap.children) c.classList.toggle('active', c === ev.currentTarget);
    },
  }, `${flag} ${name} · ${count}`);
  wrap.append(chip('all', '🌍', 'Everywhere', pool.length));
  for (const r of [...regions.values()].sort((a, b) => b.count - a.count)) {
    wrap.append(chip(r.id, r.flag, r.name, r.count));
  }
}

/* ---------------- rounds ---------------- */
function newGame() {
  order = [...active()].sort(() => Math.random() - 0.5).slice(0, ROUNDS);
  if (order.length < ROUNDS) order = order.concat(order).slice(0, ROUNDS);
  round = 0; total = 0; results = [];
  qs('#g-start').hidden = true;
  qs('#g-final').hidden = true;
  qs('#g-game').hidden = false;
  nextRound();
}

async function renderScene(loc) {
  const scene = qs('#g-scene');
  if (mounted?.destroy) mounted.destroy();
  mounted = null;
  scene.innerHTML = '';

  const walk = walkFor(loc);
  if (walk?.yt) {
    // controls=0 keeps the video title (usually the city name!) hidden
    mounted = yt.mount(scene, {
      videoId: walk.yt, start: (walk.start || 0) + 120, muted: true, controls: 0,
      onError: () => renderPhotoScene(loc, scene),
    });
  } else {
    renderPhotoScene(loc, scene);
  }
}

async function renderPhotoScene(loc, scene) {
  const url = await photoFor(loc, 1100);
  scene.innerHTML = '';
  scene.append(el('div', {
    class: 'frame-empty',
    style: url
      ? `background:url("${url}") center/cover no-repeat;position:absolute;inset:0`
      : '',
  }, url ? '' : el('div', { class: 'big' }, loc.emoji || '🌍')));
}

function nextRound() {
  round++;
  guess = null;
  phase = 'guess';
  map.clearMarks();
  map.setMode('pick');
  map.reset(0);
  qs('#g-reveal').hidden = true;
  qs('#g-round').textContent = `Round ${round} / ${ROUNDS}`;
  qs('#g-score').textContent = `${total.toLocaleString()} pts`;
  qs('#g-hint').textContent = 'Watch the scene, then click the map';
  const btn = qs('#g-confirm');
  btn.disabled = true;
  btn.textContent = 'Drop the pin first';
  renderScene(order[round - 1]);
}

function onPick(ll) {
  if (phase !== 'guess') return;
  guess = ll;
  map.clearMarks();
  map.addPin(ll.lat, ll.lng);
  const btn = qs('#g-confirm');
  btn.disabled = false;
  btn.textContent = '✔ Confirm guess';
}

function ptsFor(d) {
  if (d <= BULLSEYE_KM) return MAX_PTS;
  return Math.round(MAX_PTS * Math.exp(-d / SCALE_KM));
}

function reveal() {
  phase = 'reveal';
  const loc = order[round - 1];
  const d = km(guess, loc.coordinates);
  const pts = ptsFor(d);
  total += pts;
  results.push({ d, pts });

  map.setMode('explore');
  map.addPin(loc.coordinates.lat, loc.coordinates.lng, 'wmap-pin-answer');
  map.drawLine(guess, loc.coordinates);
  map.flyToPlaces([
    { coordinates: guess }, { coordinates: loc.coordinates },
  ].map(p => ({ ...p, _pt: undefined })), 600);

  qs('#g-score').textContent = `${total.toLocaleString()} pts`;
  const r = qs('#g-reveal');
  r.hidden = false;
  r.innerHTML = '';
  r.append(
    el('div', { class: 'r-dist' }, d <= BULLSEYE_KM ? '🎯 Bullseye!' : `${d.toLocaleString()} km away`),
    el('div', { class: 'r-place' }, `It was ${loc.emoji || ''} ${loc.name}, ${loc.country_flag || ''} ${loc.country}`),
    el('div', { class: 'r-pts' }, `+${pts.toLocaleString()} points`),
    el('button', {
      class: 'btn btn-gold',
      onclick: () => round >= ROUNDS ? finish() : nextRound(),
    }, round >= ROUNDS ? 'See final score →' : 'Next round →'),
  );
  const btn = qs('#g-confirm');
  btn.disabled = true;
  btn.textContent = 'Revealed';
}

function medal(pts) {
  if (pts >= 4500) return '🟩';
  if (pts >= 3000) return '🟨';
  if (pts >= 1200) return '🟧';
  return '🟥';
}

function finish() {
  if (mounted?.destroy) mounted.destroy();
  qs('#g-game').hidden = true;
  const f = qs('#g-final');
  f.hidden = false;
  f.innerHTML = '';
  const line = results.map(r => medal(r.pts)).join('');
  f.append(
    el('div', { class: 'g-big' }, total >= MAX_PTS * ROUNDS * 0.8 ? '🏆' : total >= MAX_PTS * ROUNDS * 0.5 ? '🥈' : '🧭'),
    el('h2', {}, 'Journey complete'),
    el('div', { class: 'g-final-score' }, `${total.toLocaleString()} pts`),
    el('div', { class: 'muted' }, `of a possible ${(MAX_PTS * ROUNDS).toLocaleString()}`),
    el('div', { class: 'g-rounds' }, line),
    el('div', { class: 'g-actions' },
      el('button', {
        class: 'btn btn-gold', onclick: () => {
          navigator.clipboard?.writeText(
            `🌍 City Guesser — ${total.toLocaleString()} pts\n${line}\n`).then(() => toast('Score copied — spoiler-free 📋'));
        },
      }, '📋 Share score'),
      el('button', { class: 'btn', onclick: () => showStart() }, '↻ Play again'),
    ),
    el('div', { class: 'g-share-note' }, 'Share is a spoiler-free emoji line.'),
  );
}

/* ---------------- boot ---------------- */
async function boot() {
  pool = (await loadAll()).filter(l =>
    l.coordinates && typeof l.coordinates.lat === 'number');
  map = new WorldMap(qs('#g-map'), { mode: 'pick', onPick });
  await map.loadWorld();
  qs('#g-start-btn').addEventListener('click', newGame);
  qs('#g-confirm').addEventListener('click', () => { if (phase === 'guess' && guess) reveal(); });
  showStart();
}

boot().catch(console.error);
