/* ============================================================
   CITY GUESSER — drop into a mystery place's scene, click the world
   map to guess where it is, score GeoGuessr-style on great-circle
   distance. Our twist on virtualvacation's guesser: the scene is the
   shared Walkthrough player, so it's fully skippable / seekable.

   Depends on: Leaflet, State+Geo (state.js), API (api.js),
               Walkthrough (walkthrough.js), Destinations (destinations.js).
   ============================================================ */

const TOTAL_ROUNDS = 5;
const MAX_PER_ROUND = 5000;
const SCORE_SCALE = 2000;   // km; smaller = harsher distance falloff
const PERFECT_KM  = 25;     // within this counts as a bullseye

let gmap;                              // the guess/reveal Leaflet map
let pool = [], order = [];             // all playable places + this game's shuffled queue
let regionFilter = 'all';              // 'all' | <region id> — which slice of the world to play
let roundNum = 0, totalScore = 0, results = [];
let current = null;                    // { loc, handle }
let guessLatLng = null, phase = 'idle';   // 'guess' | 'reveal'
let guessMarker = null, actualMarker = null, lineLayer = null;

const $ = id => document.getElementById(id);
const sceneEl = () => $('scene');

/* ---------------- boot ---------------- */
async function init() {
  pool = (await Destinations.loadAll()).filter(l => l.coordinates &&
    typeof l.coordinates.lat === 'number' && typeof l.coordinates.lng === 'number');
  initGuessMap();
  wire();
  showStart();   // pick a region before the first game
}

/* Places matching the active region filter (the pool a game draws from). */
function activePool() {
  return regionFilter === 'all' ? pool : pool.filter(l => l.region_id === regionFilter);
}

/* Distinct regions present in the pool, with a flag + count — built from the
   data so new regions appear here automatically. */
function regionsInPool() {
  const seen = new Map();
  pool.forEach(l => {
    const r = seen.get(l.region_id) ||
      { id: l.region_id, name: l.region_name, flag: l.region_flag, count: 0 };
    r.count++;
    seen.set(l.region_id, r);
  });
  return [...seen.values()].sort((a, b) => b.count - a.count);
}

/* ---------------- start screen ---------------- */
function showStart() {
  const regions = regionsInPool();
  const chip = (id, flag, name, count) =>
    `<button class="g-region${id === regionFilter ? ' on' : ''}" data-region="${id}">
       <span class="g-region-flag">${flag}</span>
       <span class="g-region-name">${esc(name)}</span>
       <span class="g-region-count">${count}</span>
     </button>`;

  $('start').innerHTML = `
    <div class="g-card">
      <div class="g-final-emoji">🌍</div>
      <h2>City Guesser</h2>
      <p class="g-start-sub">Dropped into a mystery place — read the clip, then pin it on the
        map. ${TOTAL_ROUNDS} rounds. Pick your corner of the world:</p>
      <div class="g-region-grid">
        ${chip('all', '🌍', 'Everywhere', pool.length)}
        ${regions.map(r => chip(r.id, r.flag, r.name, r.count)).join('')}
      </div>
      <div class="g-final-actions">
        <button class="btn btn-gold" id="start-btn">Start guessing →</button>
        <a href="index.html" class="btn btn-ghost">← Back to the map</a>
      </div>
    </div>`;

  $('start').querySelectorAll('.g-region').forEach(b =>
    b.addEventListener('click', () => {
      regionFilter = b.dataset.region;
      $('start').querySelectorAll('.g-region').forEach(x => x.classList.toggle('on', x === b));
    }));
  $('start-btn').addEventListener('click', () => {
    $('start').classList.remove('show');
    newGame();
  });
  $('start').classList.add('show');
}

function initGuessMap() {
  gmap = L.map('guess-map', {
    zoomControl: true, worldCopyJump: true,
    minZoom: 1, maxZoom: 8, center: [20, 0], zoom: 1, attributionControl: false
  });
  L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    subdomains: 'abcd', maxZoom: 19
  }).addTo(gmap);
  gmap.on('click', e => { if (phase === 'guess') placeGuess(e.latlng); });
}

function wire() {
  $('guess-btn').addEventListener('click', openSheet);
  $('sheet-close').addEventListener('click', closeSheet);
  $('confirm-btn').addEventListener('click', () => {
    if (phase === 'guess') reveal();
    else if (phase === 'reveal') nextRound();
  });
}

/* ---------------- game flow ---------------- */
function newGame() {
  totalScore = 0; roundNum = 0; results = [];
  order = shuffle([...activePool()]);
  $('final').classList.remove('show');
  nextRound();
}

async function nextRound() {
  if (current && current.handle) current.handle.destroy();
  clearMapLayers();
  guessLatLng = null;
  closeSheet();
  phase = 'idle';

  roundNum++;
  if (roundNum > TOTAL_ROUNDS) { endGame(); return; }
  updateHud();
  setActions(false);
  $('g-hint').classList.remove('hide');

  const picked = await pickPlayable();
  if (!picked) { endGame(); return; }   // ran out of playable places
  current = picked;
  setActions(true);
}

/* Pull from the shuffled queue until we get a scene that actually has
   content — guarantees no "no imagery" dead round (honest-empty rule). */
async function pickPlayable() {
  for (let i = 0; i < 8 && order.length; i++) {
    const loc = order.shift();
    // noVideo: a curated YouTube walk's title bar would reveal the answer.
    const handle = Walkthrough.renderScene(sceneEl(), loc, { blind: true, noVideo: true });
    if (handle.kind === 'video') return { loc, handle };
    const ok = await handle.ready;
    if (ok) return { loc, handle };
    handle.destroy();
  }
  return null;
}

function openSheet() {
  if (phase === 'reveal') return;
  phase = 'guess';
  $('g-hint').classList.add('hide');
  $('sheet-title').textContent = 'Where in the world is this?';
  $('foot-note').textContent = 'Click anywhere on the map to drop your pin.';
  $('sheet-close').classList.remove('hide');
  $('visit-link').style.display = 'none';
  const c = $('confirm-btn'); c.textContent = 'Confirm guess'; c.disabled = true;
  $('sheet').classList.add('show');
  setTimeout(() => gmap.invalidateSize(), 320);   // map was hidden until now
}

function closeSheet() {
  $('sheet').classList.remove('show');
  if (phase === 'guess') phase = 'idle';
}

function placeGuess(latlng) {
  guessLatLng = latlng;
  if (guessMarker) guessMarker.setLatLng(latlng);
  else guessMarker = L.circleMarker(latlng, {
    radius: 8, color: '#c9a84c', fillColor: '#e4c06e', fillOpacity: 0.95, weight: 2
  }).addTo(gmap);
  $('foot-note').textContent = 'Pin dropped — confirm when ready.';
  $('confirm-btn').disabled = false;
}

function reveal() {
  if (!guessLatLng) return;
  phase = 'reveal';
  const loc = current.loc;
  const actual = { lat: loc.coordinates.lat, lng: loc.coordinates.lng };
  const dist = Geo.km({ lat: guessLatLng.lat, lng: guessLatLng.lng }, actual);
  const pts = dist <= PERFECT_KM ? MAX_PER_ROUND : Math.round(MAX_PER_ROUND * Math.exp(-dist / SCORE_SCALE));
  totalScore += pts;
  results.push({ name: loc.name, country: loc.country, flag: loc.country_flag || '', dist, pts });

  actualMarker = L.circleMarker([actual.lat, actual.lng], {
    radius: 8, color: '#22c55e', fillColor: '#22c55e', fillOpacity: 0.9, weight: 2
  }).addTo(gmap).bindTooltip(`${loc.name}`, { permanent: true, direction: 'top', className: 'g-answer-tip' }).openTooltip();
  lineLayer = L.polyline([[guessLatLng.lat, guessLatLng.lng], [actual.lat, actual.lng]], {
    color: '#c9a84c', weight: 2, dashArray: '6 7', opacity: 0.8
  }).addTo(gmap);
  gmap.fitBounds(L.featureGroup([guessMarker, actualMarker]).getBounds().pad(0.45));

  $('sheet-title').innerHTML = `It was <b>${esc(loc.name)}</b> · ${esc(loc.country)} ${loc.country_flag || ''}`;
  $('foot-note').innerHTML = `${dist.toLocaleString()} km away · <b>+${pts.toLocaleString()}</b> pts`;
  $('sheet-close').classList.add('hide');
  const v = $('visit-link'); v.href = `location.html?id=${loc.id}`; v.style.display = '';
  const c = $('confirm-btn'); c.disabled = false;
  c.textContent = roundNum >= TOTAL_ROUNDS ? 'See results 🏆' : 'Next round →';
  updateHud();
}

function endGame() {
  setActions(false); closeSheet();
  const max = TOTAL_ROUNDS * MAX_PER_ROUND;
  const ratio = totalScore / max;
  const medal = ratio >= 0.9 ? '🏆' : ratio >= 0.7 ? '🥇' : ratio >= 0.45 ? '🥈' : ratio >= 0.2 ? '🧭' : '🌍';
  const grade = ratio >= 0.9 ? 'Seasoned globetrotter!' : ratio >= 0.7 ? 'Sharp eye.'
    : ratio >= 0.45 ? 'Not bad at all.' : ratio >= 0.2 ? 'Keep wandering.' : 'The world is wide…';

  $('final').innerHTML = `
    <div class="g-card">
      <div class="g-final-emoji">${medal}</div>
      <h2>${grade}</h2>
      <div class="g-final-region">${esc(regionLabel())}</div>
      <div class="g-final-score"><b>${totalScore.toLocaleString()}</b> / ${max.toLocaleString()} pts</div>
      <ul class="g-final-list">
        ${results.map((r, i) => `<li>
          <span>${i + 1}. ${esc(r.name)} ${r.flag}</span>
          <span>${r.dist.toLocaleString()} km · ${r.pts.toLocaleString()} pts</span></li>`).join('')}
      </ul>
      <div class="g-final-actions">
        <button class="btn btn-gold" id="again-btn">↻ Play again</button>
        <button class="btn btn-ghost" id="share-btn">📋 Share score</button>
        <button class="btn btn-ghost" id="region-btn">🌍 Change region</button>
      </div>
    </div>`;
  $('final').classList.add('show');
  $('again-btn').addEventListener('click', newGame);
  $('region-btn').addEventListener('click', () => { $('final').classList.remove('show'); showStart(); });
  $('share-btn').addEventListener('click', shareScore);
}

/* Human label for the region currently being played. */
function regionLabel() {
  if (regionFilter === 'all') return '🌍 Everywhere';
  const r = regionsInPool().find(x => x.id === regionFilter);
  return r ? `${r.flag} ${r.name}` : '🌍 Everywhere';
}

/* Wordle-style shareable summary — copied to the clipboard, no spoilers. */
async function shareScore() {
  const max = TOTAL_ROUNDS * MAX_PER_ROUND;
  const square = pts => {
    const f = pts / MAX_PER_ROUND;
    return f >= 0.8 ? '🟩' : f >= 0.5 ? '🟨' : f >= 0.2 ? '🟧' : '⬛';
  };
  const text =
    `🌍 One World Tour — City Guesser\n` +
    `${regionLabel()} · ${totalScore.toLocaleString()} / ${max.toLocaleString()} pts\n` +
    `${results.map(r => square(r.pts)).join('')}`;

  const btn = $('share-btn');
  try {
    await navigator.clipboard.writeText(text);
    btn.textContent = '✓ Copied!';
  } catch (_) {
    btn.textContent = '⚠ Copy failed';
  }
  setTimeout(() => { if (btn) btn.textContent = '📋 Share score'; }, 2200);
}

/* ---------------- helpers ---------------- */
function updateHud() {
  $('g-round').textContent = `Round ${Math.min(roundNum, TOTAL_ROUNDS)} / ${TOTAL_ROUNDS}`;
  $('g-score').textContent = `${totalScore.toLocaleString()} pts`;
}
function setActions(show) { $('actions').classList.toggle('hide', !show); }
function clearMapLayers() {
  [guessMarker, actualMarker, lineLayer].forEach(l => { if (l) gmap.removeLayer(l); });
  guessMarker = actualMarker = lineLayer = null;
}
function shuffle(a) {
  for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; }
  return a;
}
function esc(s) {
  return String(s).replace(/[&<>"']/g, c =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

init();
