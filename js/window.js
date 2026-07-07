/* ============================================================
   VIRTUAL WINDOW — a "looking out of a window" onto a place.

   HYBRID, and always honest about which is which:
     🔴 LIVE    — a real public webcam, streaming right now (`webcam`).
     🎬 AMBIENT — a curated recorded "out the window" video, seeked to a
                  good moment and looped (`ambient`). Not live, and the
                  badge/chip/legend say so. This is the technique
                  virtualvacation.us/window uses to reach hundreds of
                  places — we adopt it but never pass recorded off as live.

   It never falls back to a still photo standing in for a window. If a
   place has neither a live cam nor an ambient view, it simply isn't a
   window here. No live AND no ambient anywhere → it says so plainly.

   Each window gets a live local-time / day-night / weather plate — that
   real-right-now data is honest regardless of whether the *footage* is
   live, and it's what makes the place feel alive. "Open another window"
   hops between views; it remembers your last one.

   Depends on: API (api.js), Webcam (webcam.js),
               Destinations (destinations.js), Soundscape (soundscape.js).
   ============================================================ */

const LAST_WINDOW_KEY = 'owt_last_window';

let cams = [], suggestions = [], current = null;
let soundOn = false;   // ambient bed — opt-in (Web Audio needs a user gesture)
let viewToken = 0;     // guards against a slow fetch landing after we've hopped

const $ = id => document.getElementById(id);
const pane = () => $('pane');

/* the resolved window view for a location, with its tier ('live'|'ambient') */
const view = loc => Webcam.forWindow(loc);
const kindOf = loc => { const v = view(loc); return v ? v.kind : null; };

async function init() {
  // Destinations.loadAll() fetches everything (cross-page cached) and hands
  // the Windy index to Webcam before resolving — so view()/forWindow() can
  // already see the hundreds of Windy windows when we filter.
  const all = await Destinations.loadAll();
  cams = all.filter(l => l.coordinates && view(l));

  if (!cams.length) {
    // Honest empty state — no fake window, no still stand-in.
    setBadge(null);
    $('w-name').textContent = 'No windows yet';
    pane().innerHTML =
      `<div class="w-loading">No window is available right now.<br>
        <span style="opacity:0.7">Live cams and ambient views get added over time — check back soon.</span></div>`;
    $('another-btn').disabled = true;
    return;
  }

  renderLegend();
  suggestions = buildSuggestions();
  renderSuggestions();
  $('another-btn').addEventListener('click', () => openWindow(randomCam()));
  $('sound-btn').addEventListener('click', toggleSound);

  // Open order: ?id=<id> deep link → your last window → a random one.
  // A non-window id falls through to a real one.
  const id = new URLSearchParams(location.search).get('id') || localStorage.getItem(LAST_WINDOW_KEY);
  const wanted = id && cams.find(l => l.id === id);
  openWindow(wanted || randomCam());
}

/* A one-line key so it's unmistakable which dot means what. Only mentions a
   tier we actually have. */
function renderLegend() {
  const live = cams.some(l => kindOf(l) === 'live');
  const tl   = cams.some(l => kindOf(l) === 'timelapse');
  const amb  = cams.some(l => kindOf(l) === 'ambient');
  const parts = [];
  if (live) parts.push('🔴 live cam · streaming now');
  if (tl)   parts.push('🪟 webcam · real recent view, updates through the day');
  if (amb)  parts.push('🎬 ambient view · recorded, looped');
  $('legend').textContent = parts.join('     ');
}

/* "Drop by" chips — live ones first (badged 🔴), then ambient (🎬), shuffled
   within each tier so it stays fresh. */
function buildSuggestions() {
  const live = shuffle(cams.filter(l => kindOf(l) === 'live'));
  const tl   = shuffle(cams.filter(l => kindOf(l) === 'timelapse'));
  const amb  = shuffle(cams.filter(l => kindOf(l) === 'ambient'));
  return live.concat(tl, amb).slice(0, 18);
}

function renderSuggestions() {
  const wrap = $('suggest');
  suggestions.forEach(l => {
    const b = document.createElement('button');
    b.className = 'w-chip';
    b.dataset.id = l.id;
    const k = kindOf(l);
    const mark = k === 'live' ? '🔴' : k === 'timelapse' ? '🪟' : '🎬';
    b.title = k === 'live' ? 'Live webcam — streaming now'
            : k === 'timelapse' ? 'Webcam — real recent view, updates through the day'
            : 'Ambient view — recorded, looped';
    b.innerHTML = `${mark} ${l.emoji || '📍'} ${esc(l.name)}`;
    b.addEventListener('click', () => openWindow(l));
    wrap.appendChild(b);
  });
}

/* ---------------- the window ---------------- */
function openWindow(loc) {
  if (!loc) return;
  const token = ++viewToken;
  current = loc;
  markActiveChip(loc.id);
  $('w-name').textContent = `📍 ${loc.name}, ${loc.country} ${loc.country_flag || ''}`;
  $('w-sub').textContent = '';
  pane().className = 'w-pane';
  const v = view(loc);
  renderCam(v);
  setBadge(v.kind);
  settle(loc, token);
}

function renderCam(v) {
  const p = pane();
  p.innerHTML = '';
  // A curated YouTube cam/ambient goes through YTEmbed so a rotted id fires
  // onError → fall back to this place's Windy window, else an honest empty
  // state. A Windy surface self-handles an offline cam, so it mounts plain.
  if (v.source === 'youtube' && v.video) {
    YTEmbed.mount(p, {
      videoId: v.video,
      start: v.start || 0,
      loop: v.kind === 'ambient',
      frameClass: 'w-pane-cam',
      onError: camRotted,
    });
    return;
  }
  const ifr = document.createElement('iframe');
  ifr.className = 'w-pane-cam';
  ifr.allow = 'autoplay; encrypted-media; picture-in-picture; fullscreen';
  ifr.allowFullscreen = true;
  ifr.src = v.src;
  p.appendChild(ifr);
}

/* The curated YouTube cam for the open window rotted. Fall back to its Windy
   window (relabel the badge), or an honest empty pane — never a broken frame. */
function camRotted() {
  const fb = Webcam.windyLiveFor(current) || Webcam.windyWindowFor(current);
  if (fb) {
    setBadge(fb.kind);
    const ifr = document.createElement('iframe');
    ifr.className = 'w-pane-cam';
    ifr.allow = 'autoplay; encrypted-media; picture-in-picture; fullscreen';
    ifr.allowFullscreen = true;
    ifr.src = fb.src;
    pane().innerHTML = '';
    pane().appendChild(ifr);
    return;
  }
  setBadge(null);
  pane().innerHTML =
    `<div class="w-loading">This window is no longer available.<br>
      <span style="opacity:0.7">The curated feed rotted — we won't show a broken or fake one.</span></div>`;
}

function settle(loc, token) {
  localStorage.setItem(LAST_WINDOW_KEY, loc.id);   // remember where we were
  updateAmbient();                                  // match the bed to this place (if on)
  loadLocalMoment(loc, token);
}

/* The pane badge — the primary "which is which" signal. */
function setBadge(kind) {
  const b = $('w-kind');
  if (!b) return;
  if (kind === 'live')          { b.textContent = '🔴 Live'; b.className = 'w-kind live'; }
  else if (kind === 'timelapse'){ b.textContent = '🪟 Live timelapse · updates through the day'; b.className = 'w-kind timelapse'; }
  else if (kind === 'ambient')  { b.textContent = '🎬 Ambient · recorded loop'; b.className = 'w-kind ambient'; }
  else                          { b.textContent = '🪟 Window'; b.className = 'w-kind'; }
}

/* Live "what it's like there right now": local time + day/night + temp.
   Real-time data — honest whether the footage is live or recorded. */
async function loadLocalMoment(loc, token) {
  const w = await API.getWeather(loc.coordinates.lat, loc.coordinates.lng);
  if (token !== viewToken) return;                 // window changed while fetching
  if (!w) { $('w-sub').textContent = ''; return; } // honest: no fake data
  const t = new Date(Date.now() + w.offsetSec * 1000);
  const h24 = t.getUTCHours();
  const m = String(t.getUTCMinutes()).padStart(2, '0');
  const ampm = h24 >= 12 ? 'PM' : 'AM';
  const h = h24 % 12 || 12;
  const icon = w.isDay ? '☀️' : '🌙';
  $('w-sub').textContent = `${icon} ${h}:${m} ${ampm} local · ${w.tempC}°C`;
}

/* ---------------- ambient sound (opt-in) ---------------- */
function toggleSound() {
  soundOn = !soundOn;
  updateAmbient();
}

/* Switch the synthesised ambience to match the current window. Safe to call
   on every hop: a no-op when sound is off. */
function updateAmbient() {
  $('sound-btn').classList.toggle('on', soundOn);
  const lab = $('sound-label');
  if (soundOn && current) {
    const type = Soundscape.typeFor((current.sounds && current.sounds[0]) || '') || 'wind';
    lab.textContent = `🔊 ${Soundscape.label(type)}`;
    Soundscape.start(type);   // first call is inside the toggle click → audio is allowed
  } else {
    lab.textContent = '🔇 Ambient sound';
    Soundscape.stop();
  }
}

/* ---------------- helpers ---------------- */
function randomCam() {
  if (cams.length === 1) return cams[0];
  let p; do { p = cams[Math.floor(Math.random() * cams.length)]; } while (current && p.id === current.id);
  return p;
}
function markActiveChip(id) {
  document.querySelectorAll('.w-chip').forEach(c => c.classList.toggle('on', c.dataset.id === id));
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
