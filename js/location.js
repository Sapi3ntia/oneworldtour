/* ============================================================
   LOCATION — arrival cinematic + media-first scroll experience.
   The hero is the single best REAL view of the place (walk > live cam >
   window > photo), always chipped with what it is. Everything else flows
   underneath: more views, monuments, about, highlights, photos, guide in
   the main column; mini-map, flavor, radio, news, nearby in the side rail.
   TODO: set GMAPS_KEY for real Street View
   ============================================================ */
const GMAPS_KEY = 'YOUR_GOOGLE_MAPS_API_KEY';

let loc = null, wikiContext = '', miniMap = null, arrivalTimer = null, allLocs = [];
let heroPhotoUrl = null;   // captured for the postcard studio
let arrivalPhoto = Promise.resolve(null);   // the hero falls back to this
let heroTier = null;       // which media tier the hero took: walk|live|window|null

async function init() {
  const id = new URLSearchParams(window.location.search).get('id');
  if (!id) { window.location.href = 'index.html'; return; }

  // One shared, cross-page-cached loader — all regions in parallel, plus the
  // Windy cam index (loadAll hands it to Webcam). See js/destinations.js.
  allLocs = await Destinations.loadAll();

  loc = allLocs.find(l => l.id === id);
  if (!loc) { window.location.href = 'index.html'; return; }

  document.title = `${loc.name} — One World Tour`;
  State.resetCompletion();

  const sub = loc.region || loc.province || '';
  document.getElementById('arrival-name').textContent = loc.name;
  document.getElementById('arrival-province').textContent =
    [sub, loc.country].filter(Boolean).join(', ');
  document.getElementById('arrival-tag').innerHTML =
    `<span class="badge ${loc.tag === 'hidden' ? 'badge-hidden' : 'badge-famous'}">
       ${loc.tag === 'hidden' ? '🗺️ Local Secret' : '📸 Famous Spot'}
     </span>`;

  arrivalPhoto = API.getArrivalPhoto(loc.wikipedia_slug).then(url => {
    const el = document.getElementById('arrival-photo');
    if (url) { heroPhotoUrl = url; const i = new Image(); i.onload = () => { el.style.backgroundImage = `url(${url})`; }; i.src = url; }
    else el.style.background = 'linear-gradient(135deg,#1a2535 0%,#080c14 100%)';
    return url;
  });

  // Skippable arrival — click anywhere on the overlay to enter early.
  // A place you've already stamped barely pauses; a new one gets a beat.
  const overlay = document.getElementById('arrival-overlay');
  overlay.addEventListener('click', enterExperience);
  arrivalTimer = setTimeout(enterExperience, State.isVisited(loc.id) ? 1200 : 2600);
}

let entered = false;
function enterExperience() {
  if (entered) return;
  entered = true;
  clearTimeout(arrivalTimer);
  const overlay = document.getElementById('arrival-overlay');
  overlay.classList.add('hidden');
  setTimeout(() => {
    overlay.style.display = 'none';
    document.getElementById('experience').classList.add('visible');
    loadExperience();
  }, 600);
}

function loadExperience() {
  const sub = loc.region || loc.province || '';

  document.getElementById('panel-location-name').textContent = loc.name;
  document.getElementById('panel-province').innerHTML =
    `<span>${[sub, loc.country].filter(Boolean).join(', ')} ${loc.country_flag || ''}</span>
     <span class="badge ${loc.tag === 'hidden' ? 'badge-hidden' : 'badge-famous'}" style="margin-left:6px">
       ${loc.tag === 'hidden' ? '🗺️ Local Secret' : '📸 Famous Spot'}
     </span>`;

  renderSave();
  setupTour();
  renderConditions();
  setupHero();
  setupOutside();
  setupMonuments();
  fillAbout();
  setupHancock();
  renderCulture();
  setupAmbient();
  setupRadio();
  setupPostcard();
  renderNews();
  renderHighlights();
  setupMap();
  loadGallery();
  watchGuide();
  renderNearby();

  if (State.isVisited(loc.id)) {
    document.getElementById('progress-fill').style.width = '100%';
    const ss = document.getElementById('stamp-status');
    ss.textContent = '✓ Stamp earned';
    ss.style.color = 'var(--success)';
  }
}

/* Save / wishlist toggle. */
function renderSave() {
  const btn = document.getElementById('save-btn');
  const sync = () => {
    const s = State.isSaved(loc.id);
    btn.classList.toggle('saved', s);
    btn.innerHTML = s ? '♥ Saved' : '♡ Save';
  };
  sync();
  btn.addEventListener('click', () => { State.toggleSaved(loc.id); sync(); });
}

/* Add / remove this stop from the planned tour. */
function setupTour() {
  const btn = document.getElementById('tour-btn');
  if (!btn) return;
  const sync = () => {
    const inTour = State.inTrip(loc.id);
    btn.classList.toggle('in-tour', inTour);
    btn.innerHTML = inTour ? '✓ In tour' : '➕ Tour';
  };
  sync();
  btn.addEventListener('click', () => { State.toggleTrip(loc.id); sync(); });
}

/* Media tiers, honestly labelled and never conflated:
     • 🚶 Walk     — a RECORDED street-level stroll (muted, so it never fights
                     the radio/ambient; native YouTube controls stay on, so
                     it's skippable/seekable).
     • 🔴 Live cam — real live footage only; a recorded clip never sits here.
     • 🪟 Window   — a stationary out-the-window view: Windy's live timelapse
                     or an honestly-labelled recorded loop.
   The hero takes the best tier (walk > live > window > 📷 photo); "More Views"
   shows whatever real footage remains. No off-site launcher links stand in for
   any of these — embed the real thing or say it doesn't exist yet. */
const OUTSIDE_EMBED = 'autoplay=1&mute=1&rel=0&playsinline=1&modestbranding=1&iv_load_policy=3';

function resolveMedia() {
  const vid = typeof loc.walk === 'string' ? loc.walk : (loc.walk && loc.walk.yt);
  const walk = vid ? {
    src: `https://www.youtube.com/embed/${vid}?${OUTSIDE_EMBED}`,
    video: vid, kind: 'walk', source: 'youtube',
    title: (loc.walk && loc.walk.title) || 'Walking tour',
  } : null;
  return { walk, live: Webcam.liveFor(loc), window: Webcam.windowFor(loc) };
}

/* The one caption per tier — the same honest label whether it caps a tile or
   chips the hero. The red 🔴 treatment is reserved for real live streams. */
function kindCap(tier, v) {
  if (tier === 'live') return '🔴 <span class="outside-live">Live cam · streaming now</span>';
  if (tier === 'walk') return `🚶 <span class="outside-recorded">${escapeHtml(v.title || 'Walking tour')}</span>`;
  return v.kind === 'timelapse'
    ? '🪟 <span class="outside-recorded">Window · live timelapse, updates through the day</span>'
    : '🪟 <span class="outside-recorded">Window · a recorded view of the place</span>';
}

/* Mount a tier's media into `stage`. A curated YouTube surface goes through
   YTEmbed so a rotted id (deleted / private / embedding-off) fires onError; we
   then fall back to the place's Windy window — which self-handles an offline
   cam — and, failing that, an honest empty state. A Windy surface is already
   self-healing, so it mounts as a plain iframe. `opts.cap` is the caption to
   relabel on fallback; `opts.onGone` lets a caller own the fallback entirely
   (the hero drops all the way back to its arrival photo). */
function mountEmbed(stage, v, tier, opts = {}) {
  if (v.source === 'youtube' && v.video) {
    YTEmbed.mount(stage, {
      videoId: v.video,
      start: v.start || 0,
      loop: tier === 'window',                       // the recorded ambient window loops
      frameClass: 'outside-frame',
      onError: opts.onGone || (() => mediaRotted(stage, tier, opts.cap)),
    });
  } else {
    mountPlainEmbed(stage, v);
  }
}

function mountPlainEmbed(stage, v) {
  stage.innerHTML = '';
  const ifr = document.createElement('iframe');
  ifr.className = 'outside-frame';
  ifr.allow = 'autoplay; encrypted-media; picture-in-picture; fullscreen';
  ifr.allowFullscreen = true;
  ifr.src = v.src;
  stage.appendChild(ifr);
}

/* A curated YouTube embed rotted. Fall back to Windy (self-healing), and only
   if there's none, to an honest empty state — never a broken frame, never a
   fake feed. A walk has no Windy equivalent, so it goes straight to honest. */
function mediaRotted(stage, tier, cap) {
  const fb = tier === 'live'   ? (Webcam.windyLiveFor(loc) || Webcam.windyWindowFor(loc))
           : tier === 'window' ? Webcam.windyWindowFor(loc)
           :                     null;
  if (fb) {
    mountPlainEmbed(stage, fb);
    // Relabel to the tier we actually fell into: a rotted recorded window that
    // lands on Windy is now a live timelapse; a rotted live that lands on
    // Windy /live is still live.
    if (cap) cap.innerHTML = kindCap(fb.kind === 'timelapse' ? 'window' : 'live', fb);
    return;
  }
  const [ico, txt] = tier === 'walk' ? ['🚶', 'This walking tour is no longer available']
                   : tier === 'live' ? ['📹', 'This live cam has gone offline']
                   :                    ['🪟', 'This window view is no longer available'];
  stage.className = 'outside-stage outside-empty';
  stage.innerHTML = `
    <span class="outside-empty-ico">${ico}</span>
    <span class="outside-empty-txt">${txt}</span>
    <span class="outside-empty-sub">The curated feed rotted — we won't show a broken or fake one.</span>`;
}

/* HERO — the best real view of the place, big. Falls back to the arrival
   photo (chipped 📷, never dressed up as footage) when no tier exists. */
function setupHero() {
  const stage = document.getElementById('hero-stage');
  const chip  = document.getElementById('hero-chip');
  const m = resolveMedia();
  heroTier = m.walk ? 'walk' : m.live ? 'live' : m.window ? 'window' : null;

  if (!heroTier) {
    chip.innerHTML = '📷 <span class="outside-recorded">Photo</span>';
    stage.classList.add('hero-photo');
    arrivalPhoto.then(url => {
      if (url) stage.style.backgroundImage = `url(${url})`;
      else stage.style.background = 'linear-gradient(135deg,#1a2535 0%,#080c14 100%)';
    });
    return;
  }

  const v = m[heroTier];
  chip.innerHTML = kindCap(heroTier, v);
  mountEmbed(stage, v, heroTier, { cap: chip, onGone: () => heroRotted(stage, chip) });
  // The hero counts toward your stamp like the tile it replaced: watching the
  // place live ≈ Street View; a walk or window ≈ viewing photos.
  State.triggerInteraction(heroTier === 'live' ? 'street_view_clicked' : 'photos_viewed');
  updateProgress();
}

/* The hero's curated view rotted. Try the place's Windy window (relabel the
   chip honestly); with none, fall the hero all the way back to the arrival
   photo — the same honest 📷 state a place with no footage shows. */
function heroRotted(stage, chip) {
  const fb = heroTier === 'live'   ? (Webcam.windyLiveFor(loc) || Webcam.windyWindowFor(loc))
           : heroTier === 'window' ? Webcam.windyWindowFor(loc)
           :                         null;
  if (fb) {
    mountPlainEmbed(stage, fb);
    chip.innerHTML = kindCap(fb.kind === 'timelapse' ? 'window' : 'live', fb);
    heroTier = fb.kind === 'live' ? 'live' : 'window';
    return;
  }
  stage.innerHTML = '';
  stage.classList.add('hero-photo');
  chip.innerHTML = '📷 <span class="outside-recorded">Photo</span>';
  arrivalPhoto.then(url => {
    if (url) stage.style.backgroundImage = `url(${url})`;
    else stage.style.background = 'linear-gradient(135deg,#1a2535 0%,#080c14 100%)';
  });
}

/* MORE VIEWS — whatever real footage the hero isn't already showing. Tiers
   with nothing real are simply absent; nothing real at all → one combined
   honest empty state (the hero is a photo then, and says so). */
function setupOutside() {
  const sec  = document.getElementById('outside-section');
  const wrap = document.getElementById('outside-tiles');
  if (!wrap) return;
  const m = resolveMedia();

  if (!heroTier) {
    wrap.innerHTML = `
      <div class="outside-stage outside-empty outside-combined">
        <span class="outside-empty-ico">📹</span>
        <span class="outside-empty-txt">No live cam, window view, or walking tour of this place yet</span>
        <span class="outside-empty-sub">Real footage appears here the moment it exists — never a fake feed.</span>
      </div>`;
    return;
  }

  const rest = [['live', m.live], ['window', m.window], ['walk', m.walk]]
    .filter(([tier, v]) => tier !== heroTier && v);
  if (!rest.length) { sec.style.display = 'none'; return; }
  rest.forEach(([tier, v]) => wrap.appendChild(buildTile(tier, v)));
}

function buildTile(tier, v) {
  const tile = document.createElement('div');
  tile.className = 'outside-tile' + (tier === 'walk' ? ' outside-tile-lg' : '');
  const cap = document.createElement('div');
  cap.className = 'outside-cap';
  cap.innerHTML = kindCap(tier, v);
  const stage = document.createElement('div');
  stage.className = 'outside-stage';
  tile.append(cap, stage);
  mountEmbed(stage, v, tier, { cap });
  State.triggerInteraction(tier === 'live' ? 'street_view_clicked' : 'photos_viewed');
  updateProgress();
  return tile;
}

/* MONUMENTS — up to 3 named landmark tours for this city (e.g. Eiffel Tower for
   Paris). A separate category from the walk and the window: these are RECORDED
   videos of specific landmarks. A small tab picker swaps which one plays in the
   shared stage. `loc.monuments` is an array of { name, yt, start? } (or a bare
   'id' / 'id?start=ss' string); capped at 3 for now. None → section stays hidden. */
function normMonument(m) {
  if (!m) return null;
  if (typeof m === 'string') {
    const mm = m.match(/^([A-Za-z0-9_-]{11})(?:[?&].*?start=(\d+))?/);
    if (!mm) return null;
    return { name: 'Landmark', yt: mm[1], start: parseInt(mm[2], 10) || 0 };
  }
  if (m.yt) return { name: m.name || 'Landmark', yt: m.yt, start: parseInt(m.start, 10) || 0 };
  return null;
}

function setupMonuments() {
  const sec = document.getElementById('monuments-section');
  if (!sec) return;
  const list = (Array.isArray(loc.monuments) ? loc.monuments : [])
    .map(normMonument).filter(Boolean).slice(0, 3);
  if (!list.length) return;   // section stays display:none

  const tabs  = document.getElementById('mon-tabs');
  const stage = document.getElementById('mon-stage');
  const cap   = document.getElementById('mon-cap');
  sec.style.display = 'block';

  const play = (i) => {
    const m = list[i];
    tabs.querySelectorAll('.mon-tab').forEach((b, j) => b.classList.toggle('active', j === i));
    cap.innerHTML = `🏛️ <span class="outside-recorded">${escapeHtml(m.name)}</span>`;
    stage.className = 'outside-stage';                // reset if a prior tab rotted
    // A landmark tour has no Windy equivalent, so a rotted id → honest empty
    // state for that tab (the other tabs + the photo gallery still stand).
    YTEmbed.mount(stage, {
      videoId: m.yt, start: m.start || 0, frameClass: 'outside-frame',
      onError: () => {
        stage.className = 'outside-stage outside-empty';
        stage.innerHTML = `
          <span class="outside-empty-ico">🏛️</span>
          <span class="outside-empty-txt">This landmark tour is no longer available</span>
          <span class="outside-empty-sub">Pick another landmark above, or explore its photos below.</span>`;
      },
    });
  };

  // Only show tabs when there's more than one monument to choose between.
  tabs.innerHTML = list.length > 1
    ? list.map((m, i) => `<button class="mon-tab" type="button" data-i="${i}">${escapeHtml(m.name)}</button>`).join('')
    : '';
  tabs.querySelectorAll('.mon-tab').forEach(b => b.addEventListener('click', () => play(+b.dataset.i)));

  play(0);
  State.triggerInteraction('photos_viewed');
  updateProgress();
}

/* Ancient Apocalypse — if this is a Graham Hancock site, show which
   episode featured it and the claim he makes about it. Framed clearly
   as *his* claim, not settled fact. */
function setupHancock() {
  const sec = document.getElementById('hancock-section');
  if (!sec || !loc.aa_claim) return;
  const title = loc.aa_season === 2 ? 'Ancient Apocalypse: The Americas' : 'Ancient Apocalypse';
  document.getElementById('hancock-ep').textContent =
    `🤫 ${title} · Season ${loc.aa_season}, Episode ${loc.aa_episode}`;
  document.getElementById('hancock-claim').textContent = loc.aa_claim;
  sec.style.display = 'block';
}

/* "Right Now" — live weather + a ticking local clock.
   Open-Meteo gives us the exact IANA timezone, so the clock is
   DST-correct; if the fetch fails we approximate from longitude. */
let clockTimer = null;
async function renderConditions() {
  const { lat, lng } = loc.coordinates;
  const w = await API.getWeather(lat, lng);

  const iconEl = document.getElementById('weather-icon');
  const tempEl = document.getElementById('weather-temp');
  const labEl  = document.getElementById('weather-label');

  let tz = null, offsetSec = null;
  if (w) {
    const info = weatherInfo(w.code, w.isDay);
    iconEl.textContent = info.icon;
    tempEl.textContent = `${w.tempC}°C`;
    labEl.textContent  = `${info.label} · wind ${w.windKmh} km/h`;
    tz = w.timezone; offsetSec = w.offsetSec;
  } else {
    iconEl.textContent = '🌍';
    tempEl.textContent = '';
    labEl.textContent  = 'Weather unavailable';
    offsetSec = Math.round(lng / 15) * 3600;   // rough fallback
  }

  startClock(tz, offsetSec);
}

function startClock(tz, offsetSec) {
  const clockEl = document.getElementById('local-clock');
  const tzEl    = document.getElementById('local-tz');
  if (tz) tzEl.textContent = tz.split('/').pop().replace(/_/g, ' ') + ' time';

  const tick = () => {
    let h, m;
    if (tz) {
      const parts = new Intl.DateTimeFormat('en-GB', {
        timeZone: tz, hour: '2-digit', minute: '2-digit', hour12: false
      }).formatToParts(new Date());
      h = parts.find(p => p.type === 'hour').value;
      m = parts.find(p => p.type === 'minute').value;
    } else {
      const now = new Date(Date.now() + (offsetSec || 0) * 1000 + new Date().getTimezoneOffset() * 60000);
      h = String(now.getHours()).padStart(2, '0');
      m = String(now.getMinutes()).padStart(2, '0');
    }
    clockEl.textContent = `${h}:${m}`;
    clockEl.classList.toggle('tick', clockEl.classList.contains('tick') ? false : true);
  };
  tick();
  if (clockTimer) clearInterval(clockTimer);
  clockTimer = setInterval(tick, 1000);
}

/* "Local Flavor" — language, phrases, currency, signature dish. */
function renderCulture() {
  const c = Culture.get(loc.country);
  document.getElementById('flavor-lang').textContent     = c.lang;
  document.getElementById('flavor-currency').textContent = c.currency;
  document.getElementById('flavor-dish').textContent     = c.dish;

  const list = document.getElementById('phrase-list');
  list.innerHTML = c.phrases.map(([en, native]) => `
    <div class="phrase">
      <span class="phrase-native">${native}</span>
      <span class="phrase-en">${en}</span>
    </div>`).join('');

  renderFacts();
  document.getElementById('flavor-section').style.display = 'block';
  renderExchange();
}

/* Quick country facts — capital, population, driving side, plug. */
function renderFacts() {
  const f = Culture.facts(loc.country);
  if (!f) return;
  document.getElementById('fact-capital').textContent = f.capital;
  document.getElementById('fact-pop').textContent     = f.pop;
  document.getElementById('fact-drives').textContent  = f.drives;
  document.getElementById('fact-plug').textContent    = f.plug;
  document.getElementById('facts-grid').style.display = 'grid';
}

/* Live exchange rate: what $1 buys in the local currency. */
async function renderExchange() {
  const cur = Culture.currencyCode(loc.country);
  if (!cur) return;
  const rates = await API.getRates('USD');
  if (!rates) return;
  // For the US, reference the euro instead so the line still says something.
  const ref = cur === 'USD' ? 'EUR' : cur;
  const rate = rates[ref];
  if (!rate) return;
  const val = rate >= 100 ? Math.round(rate).toLocaleString() : rate.toFixed(2);
  document.getElementById('flavor-fx-val').textContent = `$1 ≈ ${val} ${ref}`;
  document.getElementById('flavor-fx').style.display = 'flex';
}

/* Ambient soundscape — synthesised live, with a visible toggle.
   Module-level state so the radio can switch it off (the two
   audio sources are mutually exclusive). */
let ambientType = null;
let ambientOn = false;

function applyAmbient() {
  const btn = document.getElementById('ambient-toggle');
  const lab = document.getElementById('ambient-label');
  if (!btn || !ambientType) return;
  btn.classList.toggle('on', ambientOn);
  lab.textContent = ambientOn ? Soundscape.label(ambientType) : 'Sound off';
  if (ambientOn) { Radio.stop(); Soundscape.start(ambientType); }
  else Soundscape.stop();
}

function setupAmbient() {
  const btn = document.getElementById('ambient-toggle');
  ambientType = Soundscape.typeFor((loc.sounds && loc.sounds[0]) || '');
  if (!ambientType) { btn.style.display = 'none'; return; }

  ambientOn = localStorage.getItem('owt_sound_off') !== '1';
  applyAmbient();   // first call runs inside the arrival click → audio is allowed

  btn.addEventListener('click', () => {
    ambientOn = !ambientOn;
    localStorage.setItem('owt_sound_off', ambientOn ? '0' : '1');
    applyAmbient();
  });
}

/* Local radio — live streams for this country, right now. */
async function setupRadio() {
  const sec    = document.getElementById('radio-section');
  const code   = Culture.code(loc.country);
  if (!code) return;

  const playBtn  = document.getElementById('radio-play');
  const select   = document.getElementById('radio-select');
  const randomB  = document.getElementById('radio-random');
  const nameEl   = document.getElementById('radio-station');
  const statusEl = document.getElementById('radio-status');

  statusEl.textContent = 'Scanning the airwaves…';
  sec.style.display = 'block';

  const stations = await API.getStations(code);
  if (!stations.length) { sec.style.display = 'none'; return; }

  select.innerHTML = stations
    .map((s, i) => `<option value="${i}">${s.name.replace(/</g, '')}${s.bitrate ? ` · ${s.bitrate}k` : ''}</option>`)
    .join('');
  statusEl.textContent = `${stations.length} stations · ${loc.country}`;
  nameEl.textContent = 'Tap play to tune in';

  let idx = 0;

  Radio.onState((state, st) => {
    sec.classList.toggle('radio-on', state === 'playing');
    sec.classList.toggle('radio-loading', state === 'loading');
    playBtn.textContent = (state === 'playing' || state === 'loading') ? '⏸' : '▶';
    if (state === 'loading')      statusEl.textContent = 'Tuning in…';
    else if (state === 'playing') {
      const tags = st && st.tags && st.tags.length ? st.tags.join(' · ') : `${loc.country} · live`;
      statusEl.textContent = `🔴 Live · ${tags}`;
    }
    else if (state === 'error')   statusEl.textContent = 'Signal dropped — try another station';
    else if (state === 'stopped') statusEl.textContent = `${stations.length} stations · ${loc.country}`;
  });

  const tuneTo = (i) => {
    idx = i;
    select.value = String(i);
    nameEl.textContent = stations[i].name;
    // Switching on the radio silences the ambient soundscape.
    if (ambientOn) { ambientOn = false; localStorage.setItem('owt_sound_off', '1'); applyAmbient(); }
    Radio.play(stations[i]);
  };

  playBtn.addEventListener('click', () => {
    if (Radio.playing) { Radio.stop(); nameEl.textContent = stations[idx].name; }
    else tuneTo(idx);
  });
  select.addEventListener('change', () => tuneTo(parseInt(select.value, 10) || 0));
  randomB.addEventListener('click', () => tuneTo(Math.floor(Math.random() * stations.length)));
}

/* Local headlines — recent articles about this place, via GDELT. */
async function renderNews() {
  const sec  = document.getElementById('news-section');
  const list = document.getElementById('news-list');
  if (!sec || !list) return;

  sec.style.display = 'block';
  list.innerHTML = '<div class="news-loading">Catching up on local headlines…</div>';

  const items = await API.getNews(loc.name, loc.country);
  if (!items.length) { sec.style.display = 'none'; return; }

  list.innerHTML = items.map(a => {
    const when = newsAge(a.seendate);
    const meta = [a.domain, when].filter(Boolean).join(' · ');
    return `<a class="news-item" href="${a.url}" target="_blank" rel="noopener">
        <span class="news-title">${escapeHtml(a.title)}</span>
        <span class="news-meta">${escapeHtml(meta)}</span>
      </a>`;
  }).join('');
}

/* "20260622T110000Z" → "3h ago" */
function newsAge(s) {
  const m = /^(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})(\d{2})Z$/.exec(s || '');
  if (!m) return '';
  const t = Date.UTC(+m[1], +m[2] - 1, +m[3], +m[4], +m[5], +m[6]);
  const mins = Math.round((Date.now() - t) / 60000);
  if (mins < 2) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.round(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.round(hrs / 24)}d ago`;
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, c =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

/* Postcard studio — compose a downloadable keepsake on a canvas. */
function setupPostcard() {
  const overlay = document.getElementById('postcard-overlay');
  const openBtn = document.getElementById('postcard-btn');
  const msg     = document.getElementById('postcard-message');

  const close = () => overlay.classList.remove('show');
  openBtn.addEventListener('click', () => {
    msg.value = State.getNote(loc.id) || '';
    overlay.classList.add('show');
    drawPostcard();
  });
  document.getElementById('postcard-close').addEventListener('click', close);
  document.getElementById('postcard-cancel').addEventListener('click', close);
  overlay.addEventListener('click', e => { if (e.target === overlay) close(); });
  msg.addEventListener('input', () => drawPostcard());
  document.getElementById('postcard-download').addEventListener('click', downloadPostcard);
}

function drawPostcard(cb) {
  const cv = document.getElementById('postcard-canvas');
  const ctx = cv.getContext('2d');
  const W = cv.width, H = cv.height;

  const paint = (img) => {
    ctx.clearRect(0, 0, W, H);
    // Background: photo (cover) or themed gradient.
    if (img) {
      const r = Math.max(W / img.width, H / img.height);
      const w = img.width * r, h = img.height * r;
      ctx.drawImage(img, (W - w) / 2, (H - h) / 2, w, h);
    } else {
      const g = ctx.createLinearGradient(0, 0, W, H);
      g.addColorStop(0, '#1a2535'); g.addColorStop(1, '#080c14');
      ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
    }
    // Darken bottom for legible text.
    const sh = ctx.createLinearGradient(0, H * 0.45, 0, H);
    sh.addColorStop(0, 'rgba(8,12,20,0)'); sh.addColorStop(1, 'rgba(8,12,20,0.92)');
    ctx.fillStyle = sh; ctx.fillRect(0, 0, W, H);

    // Gold frame.
    ctx.strokeStyle = 'rgba(201,168,76,0.9)'; ctx.lineWidth = 6;
    ctx.strokeRect(16, 16, W - 32, H - 32);

    // "Postcard" stamp (top-right).
    ctx.save();
    ctx.fillStyle = 'rgba(8,12,20,0.55)';
    ctx.fillRect(W - 150, 40, 110, 130);
    ctx.strokeStyle = 'rgba(255,255,255,0.5)'; ctx.lineWidth = 2;
    ctx.setLineDash([6, 5]); ctx.strokeRect(W - 150, 40, 110, 130);
    ctx.setLineDash([]);
    ctx.font = '54px serif'; ctx.textAlign = 'center';
    ctx.fillText(loc.emoji || '✈️', W - 95, 115);
    ctx.font = '600 14px Inter, sans-serif'; ctx.fillStyle = 'rgba(255,255,255,0.7)';
    ctx.fillText('ONE WORLD', W - 95, 150); ctx.fillText('TOUR', W - 95, 164);
    ctx.restore();

    // Place name + country.
    ctx.textAlign = 'left';
    ctx.fillStyle = '#fff';
    ctx.font = '700 58px Georgia, serif';
    ctx.fillText(truncate(ctx, loc.name, W - 90), 48, H - 150);
    ctx.fillStyle = '#c9a84c';
    ctx.font = '600 26px Inter, sans-serif';
    const sub = [(loc.region || loc.province || ''), loc.country].filter(Boolean).join(', ');
    ctx.fillText(sub.toUpperCase(), 50, H - 110);

    // Handwritten-style message.
    const note = (document.getElementById('postcard-message').value || '').trim();
    if (note) {
      ctx.fillStyle = 'rgba(255,255,255,0.92)';
      ctx.font = 'italic 28px Georgia, serif';
      wrapText(ctx, `“${note}”`, 50, H - 64, W - 100, 34);
    }
    if (cb) cb();
  };

  if (heroPhotoUrl) {
    const img = new Image();
    img.crossOrigin = 'anonymous';
    img.onload = () => paint(img);
    img.onerror = () => paint(null);
    img.src = heroPhotoUrl;
  } else {
    paint(null);
  }
}

function truncate(ctx, text, maxW) {
  if (ctx.measureText(text).width <= maxW) return text;
  let t = text;
  while (t.length > 4 && ctx.measureText(t + '…').width > maxW) t = t.slice(0, -1);
  return t + '…';
}

function wrapText(ctx, text, x, y, maxW, lh) {
  const words = text.split(' ');
  let line = '', yy = y, lines = 0;
  for (const w of words) {
    const test = line + w + ' ';
    if (ctx.measureText(test).width > maxW && line) {
      ctx.fillText(line.trim(), x, yy); line = w + ' '; yy += lh;
      if (++lines >= 1) break;   // keep to 2 lines max on the card
    } else line = test;
  }
  ctx.fillText(line.trim(), x, yy);
}

function downloadPostcard() {
  drawPostcard(() => {
    const cv = document.getElementById('postcard-canvas');
    try {
      const a = document.createElement('a');
      a.download = `postcard-${loc.id}.png`;
      a.href = cv.toDataURL('image/png');
      a.click();
      // Save the message as a note too, for continuity.
      const note = document.getElementById('postcard-message').value.trim();
      if (note) State.saveNote(loc.id, note);
    } catch (e) {
      console.warn('[Postcard]', e);
      alert('Could not export the postcard (the photo blocked it). Try again — a plain version will still download.');
    }
  });
}

/* Nearby destinations — quick hops to keep the tour going. */
function renderNearby() {
  const others = allLocs
    .filter(l => l.id !== loc.id)
    .map(l => ({ l, d: Geo.km(loc.coordinates, l.coordinates) }))
    .sort((a, b) => a.d - b.d)
    .slice(0, 4);
  if (!others.length) return;

  const sec = document.getElementById('nearby-section');
  const list = document.getElementById('nearby-list');
  sec.style.display = 'block';
  list.innerHTML = '';
  others.forEach(({ l, d }) => {
    const a = document.createElement('a');
    a.className = 'nearby-card';
    a.href = `location.html?id=${l.id}`;
    a.innerHTML = `
      <span class="nearby-emoji">${l.emoji}</span>
      <span class="nearby-info">
        <strong>${l.name}</strong>
        <small>${l.country_flag} ${l.country} · ${d.toLocaleString()} km away</small>
      </span>
      ${State.isVisited(l.id) ? '<span class="nearby-check">✓</span>' : '<span class="nearby-go">→</span>'}`;
    list.appendChild(a);
  });
}

/* About text — authored blurb if present, else live Wikipedia summary. */
async function fillAbout() {
  const blurbEl = document.getElementById('blurb-text');
  const guideEl = document.getElementById('guide-blurb');
  const factEl  = document.getElementById('fun-fact');

  if (loc.blurb) {
    blurbEl.textContent = loc.blurb;
    guideEl.textContent = loc.blurb;
  } else {
    blurbEl.textContent = 'Loading a little about this place…';
  }

  if (loc.fun_fact) {
    factEl.innerHTML = `<strong>Did you know?</strong> ${loc.fun_fact}`;
  } else {
    factEl.style.display = 'none';
  }

  if (loc.hidden_gem_tip) {
    const tip = document.getElementById('hidden-tip');
    tip.style.display = 'block';
    tip.textContent = `💡 Local tip: ${loc.hidden_gem_tip}`;
  }

  const summary = await API.getWikiSummary(loc.wikipedia_slug);
  if (summary) {
    wikiContext = summary;
    if (!loc.blurb) { blurbEl.textContent = summary; guideEl.textContent = summary; }
  } else if (!loc.blurb) {
    blurbEl.textContent = `${loc.name} is one of the stops on your tour. Explore the highlights and photos below.`;
  }
}

/* ---- Highlights: each landmark is independently explorable ---- */
function renderHighlights() {
  const section = document.getElementById('highlights-section');
  const chips   = document.getElementById('highlight-chips');
  const list    = loc.highlights || [];
  if (!list.length) { section.style.display = 'none'; return; }

  section.style.display = 'block';
  document.getElementById('highlights-count').textContent = `${list.length} to explore`;
  chips.innerHTML = '';
  list.forEach((h, i) => {
    const btn = document.createElement('button');
    btn.className = 'hl-chip';
    btn.textContent = h.name;
    btn.addEventListener('click', () => openHighlight(h, btn));
    chips.appendChild(btn);
  });
}

const loadedHighlights = new Set();
async function openHighlight(h, btn) {
  document.querySelectorAll('.hl-chip').forEach(c => c.classList.remove('active'));
  btn.classList.add('active');

  const detail = document.getElementById('highlight-detail');
  detail.innerHTML = `
    <h4>${h.name}</h4>
    <div class="hl-gallery">
      ${'<div class="hl-thumb shimmer"></div>'.repeat(3)}
    </div>
    <p class="hl-summary">Loading…</p>`;
  detail.classList.add('open');

  // Exploring highlights counts toward your stamp.
  State.triggerInteraction('photos_viewed');
  updateProgress();
  loadedHighlights.add(h.name);

  const [summary, photos] = await Promise.all([
    API.getWikiSummary(h.wikipedia_slug),
    API.getGalleryPhotos(h.wikipedia_slug, 3)
  ]);

  const gallery = detail.querySelector('.hl-gallery');
  if (gallery) {
    gallery.innerHTML = '';
    for (let i = 0; i < 3; i++) {
      const d = document.createElement('div');
      d.className = 'hl-thumb';
      if (photos[i]) d.style.backgroundImage = `url(${photos[i]})`;
      else d.classList.add('hl-thumb-empty');
      gallery.appendChild(d);
    }
  }
  const sEl = detail.querySelector('.hl-summary');
  if (sEl) {
    sEl.innerHTML = (summary || `A signature highlight of ${loc.name}.`) +
      ` <a href="https://en.wikipedia.org/wiki/${encodeURIComponent(h.wikipedia_slug)}" target="_blank" rel="noopener">Read more ↗</a>`;
  }
}

function setupMap() {
  // street_view is optional — fall back to the plain coordinates so a missing
  // panorama object can never crash the page (and authoring a place is lighter).
  const sv = loc.street_view || { ...loc.coordinates, heading: 0, pitch: 0, fov: 90 };

  if (GMAPS_KEY !== 'YOUR_GOOGLE_MAPS_API_KEY') {
    // With a key, real Street View joins the views as a full-width tile.
    // A click-shield makes the first look-around count toward your stamp.
    const wrap = document.getElementById('outside-tiles');
    const tile = document.createElement('div');
    tile.className = 'outside-tile outside-tile-lg';
    tile.innerHTML = '<div class="outside-cap">👁️ <span class="outside-recorded">Street View · look around</span></div>';
    const stage = document.createElement('div');
    stage.className = 'outside-stage';
    const ifr = document.createElement('iframe');
    ifr.className = 'outside-frame';
    ifr.allowFullscreen = true;
    ifr.src = `https://www.google.com/maps/embed/v1/streetview?key=${GMAPS_KEY}` +
      `&location=${sv.lat},${sv.lng}&heading=${sv.heading}&pitch=${sv.pitch}&fov=${sv.fov}`;
    stage.appendChild(ifr);
    const shield = document.createElement('div');
    shield.style.cssText = 'position:absolute;inset:0;cursor:pointer';
    shield.addEventListener('click', () => {
      shield.remove();
      State.triggerInteraction('street_view_clicked');
      updateProgress();
    }, { once: true });
    stage.appendChild(shield);
    tile.appendChild(stage);
    wrap.prepend(tile);
    document.getElementById('outside-section').style.display = 'block';
  }

  // The mini-map card in the side rail — always there, so you always know
  // where on Earth you're standing.
  requestAnimationFrame(() => {
    miniMap = L.map('mini-map', { center: [sv.lat, sv.lng], zoom: 11, zoomControl: true });
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      attribution: '&copy; OpenStreetMap &copy; CARTO', subdomains: 'abcd', maxZoom: 19
    }).addTo(miniMap);

    const pin = L.divIcon({
      className: '',
      html: `<div style="position:relative;width:20px;height:20px">
        <div style="position:absolute;inset:0;border-radius:50%;background:rgba(201,168,76,0.25);animation:map-pulse 2s ease-in-out infinite"></div>
        <div style="position:absolute;inset:3px;border-radius:50%;background:var(--gold);border:2px solid rgba(255,255,255,0.9);box-shadow:0 0 12px rgba(201,168,76,0.7)"></div>
      </div>`,
      iconSize: [20, 20], iconAnchor: [10, 10]
    });
    L.marker([sv.lat, sv.lng], { icon: pin }).addTo(miniMap);

    if (!document.getElementById('map-pulse-style')) {
      const s = document.createElement('style');
      s.id = 'map-pulse-style';
      s.textContent = `@keyframes map-pulse {0%,100%{transform:scale(1);opacity:0.6}50%{transform:scale(2.2);opacity:0}}`;
      document.head.appendChild(s);
    }

    let tracked = false;
    const track = () => {
      if (tracked) return;
      tracked = true;
      State.triggerInteraction('street_view_clicked');
      updateProgress();
    };
    miniMap.on('dragstart zoomstart click', track);
  });
}

async function loadGallery() {
  const gallery = document.getElementById('photo-gallery');
  gallery.classList.remove('gallery-empty');
  gallery.innerHTML = Array(6).fill('<div class="gallery-photo shimmer"></div>').join('');

  const photos = await API.getGalleryPhotos(loc.wikipedia_slug, 6);
  gallery.innerHTML = '';

  if (!photos.length) {
    // Honest empty state instead of a permanent shimmer.
    gallery.classList.add('gallery-empty');
    gallery.innerHTML = '<div class="gallery-none">No photos found for this place yet.</div>';
    return;
  }

  // Render only the photos we actually have — no shimmering placeholders.
  photos.forEach(src => {
    const div = document.createElement('div');
    div.className = 'gallery-photo';
    div.style.backgroundImage = `url(${src})`;
    div.addEventListener('click', () => { State.triggerInteraction('photos_viewed'); updateProgress(); });
    gallery.appendChild(div);
  });
}

function watchGuide() {
  // The page itself scrolls now, so the observer roots on the viewport.
  const guideEl = document.getElementById('guide-section');
  const io = new IntersectionObserver(entries => {
    if (entries[0].isIntersecting) {
      State.triggerInteraction('guide_read');
      updateProgress();
      io.disconnect();
    }
  }, { threshold: 0.4 });
  io.observe(guideEl);
}

function updateProgress() {
  const pct = State.getProgressPct();
  document.getElementById('progress-fill').style.width = `${pct}%`;
  const label = document.getElementById('stamp-status');
  if (!State.isVisited(loc.id)) label.textContent = pct === 100 ? 'Stamp ready!' : `${pct}% explored`;
  if (pct === 100 && !State.isVisited(loc.id)) earnStamp();
}

function earnStamp() {
  State.markVisited(loc.id);
  document.getElementById('stamp-earned-display').innerHTML = `
    <div class="stamp stamp-animate" style="width:100px;height:100px;margin:0 auto var(--sp-lg)">
      <div class="ink-bloom"></div>
      <div class="stamp-emoji" style="font-size:2.2rem">${loc.emoji}</div>
      <div class="stamp-name">${loc.name.split('&')[0].split('/')[0].trim()}</div>
    </div>`;
  document.getElementById('stamp-earned-name').textContent = loc.name;
  document.getElementById('stamp-earned-overlay').classList.add('show');
  const ss = document.getElementById('stamp-status');
  ss.textContent = '✓ Stamp earned';
  ss.style.color = 'var(--success)';
}

async function askGuide() {
  const input = document.getElementById('guide-input');
  const q = input.value.trim();
  if (!q) return;
  const resp = document.getElementById('guide-response');
  resp.textContent = 'Thinking…';
  resp.classList.add('visible');
  input.value = '';
  resp.textContent = await API.askGuide(loc.name, q, wikiContext);
  State.triggerInteraction('guide_read');
  updateProgress();
}

document.getElementById('guide-ask-btn').addEventListener('click', askGuide);
document.getElementById('guide-input').addEventListener('keydown', e => { if (e.key === 'Enter') askGuide(); });
document.getElementById('stamp-earned-close').addEventListener('click', () => {
  document.getElementById('stamp-earned-overlay').classList.remove('show');
});
document.getElementById('back-btn').addEventListener('click', () => {
  Soundscape.stop();
  Radio.stop();
  if (clockTimer) clearInterval(clockTimer);
  if (miniMap) { miniMap.remove(); miniMap = null; }
  window.location.href = 'index.html';
});

init();
