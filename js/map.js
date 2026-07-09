/* ============================================================
   MAP — multi-region Leaflet world map
   Upgrades: resilient loading · marker clustering · search-with-autocomplete ·
   region + tag + live-content filters (window / tour / both) ·
   dark base + borders/labels overlay (legible placement) ·
   "Surprise me" teleport · richer stats
   ============================================================ */
let map, clusterGroups = {}, allLocations = [], loadedRegions = [], markerById = {};
let journeyLayer = null, journeyOn = false;
let nightLayer = null, sunMarker = null, nightTimer = null, nightOn = false;
let planning = false, tripLayer = null, touring = false;   // Fly-the-Tour planner
let dropOn = false;        // "Drop In": tap the map → watch the nearest place
let query = '';            // search text
let tagFilter = 'all';     // all | famous | hidden | saved
let regionFilter = 'all';  // all | <region id>

async function initMap() {
  // One shared, cross-page-cached loader (regions in parallel + the Windy
  // index, which loadAll hands to Webcam for us). See js/destinations.js.
  allLocations = await Destinations.loadAll();
  loadedRegions = Destinations.regions();

  // ---- Leaflet base ----
  // zoomAnimation:false matches the clustering's animate:false: with the
  // animated zoom on, tiles scale smoothly for ~250ms while clusters snap
  // instantly — the mismatch reads as glitching, and scaling two tile layers
  // per frame halves the zoom frame-rate on a software-rendered GPU (VM).
  // One coherent instant snap is both smoother-feeling and far cheaper.
  map = L.map('map', {
    zoomControl: false, worldCopyJump: true,
    zoomAnimation: false, fadeAnimation: false,
    minZoom: 2, maxZoom: 16, center: [48, 4], zoom: 4
  });

  // Base: CARTO Dark Matter WITHOUT labels — keeps the cinematic dark tone the gold
  // theme is tuned for. The plain dark base draws country BORDERS so faintly they're
  // invisible, which makes pins read as being in the wrong country (Lake Louise, in
  // Alberta, looked like it sat in the US). So borders + labels come from the crisp,
  // keyless, CORS-safe Esri "Dark Gray Reference" overlay added on top.
  // className lets CSS brighten the LAND per-tile (see .base-tiles in map.css):
  // at world zoom the raw tiles render the continents nearly as black as the
  // ocean, so the geography the pins sit on was invisible.
  L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_nolabels/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>',
    subdomains: 'abcd', maxZoom: 19, zIndex: 1, className: 'base-tiles'
  }).addTo(map);

  // Borders + place labels overlay (note Esri's {z}/{y}/{x} tile order). Sits above
  // the base but below the marker pane, so labels never cover the pins.
  L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}', {
    attribution: 'Labels &copy; <a href="https://www.esri.com/">Esri</a>',
    maxZoom: 16, zIndex: 2, opacity: 0.92
  }).addTo(map);

  L.control.zoom({ position: 'bottomright' }).addTo(map);

  // "Drop In": a background click (not on a marker) plays the nearest place.
  map.on('click', e => { if (dropOn && !planning && !touring) dropInAt(e.latlng); });

  buildAllMarkers();
  render();
  // Leaflet caches the container's pixel size at init. If layout settles even a
  // beat later (CDN Leaflet CSS applying, web-font swap, scrollbar), every marker
  // and tile renders offset against that stale size — a pin reads as sitting
  // mid-continent at rest and only snaps to its true spot once you zoom, and the
  // drag origin is mis-computed so the map "feels stuck" until a click re-syncs
  // it. Re-measuring forces correct placement + drag math. Do it before we fit,
  // again after the next paint, and on every resize.
  map.invalidateSize(false);
  fitToVisible();
  requestAnimationFrame(() => map.invalidateSize(false));
  if (window.ResizeObserver) {
    new ResizeObserver(() => map.invalidateSize(false)).observe(document.getElementById('map'));
  }
  setupRegionChips();

  // Dynamic country pill — a compact summary, NOT the region list (the chips
  // right below it already show that; the long flag list wrapped to two lines
  // under ~1450px and collided with the chips).
  const countryCount = new Set(allLocations.map(l => l.country)).size;
  document.querySelector('.country-pill').textContent =
    `🌍 ${countryCount} countries · ${allLocations.length} places`;
}

/* ---- Clustered marker layers: ONE cluster group PER CONTINENT ----
   A single world-wide group let pixel-distance clustering merge ACROSS seas
   at low zoom — Iberia fused with Morocco, Greece/Turkey with Egypt — and
   parked the bubble at the members' average position, so bubbles full of
   European cities literally rendered over Africa (the owner's "Europe is
   appearing in Africa" report; reproduced at 1100×800, zoom 2). Splitting
   by `loc.continent` (every location carries it) makes cross-continent
   merges impossible while keeping every liked behaviour: click-to-zoom into
   members, spiderfy at max zoom, lone pins open on one click. */
const CONTINENT_SHORT = { 'North America': 'N. America', 'South America': 'S. America' };
let contTotals = {};   // continent -> currently-visible marker count (set by render)

function clusterGroupFor(continent) {
  if (clusterGroups[continent]) return clusterGroups[continent];
  // animate:false is deliberate. With it on, zooming in makes every marker *slide*
  // from the cluster-centroid to its true coordinate over a few hundred ms — which
  // reads as "the pins keep moving / are in the wrong place as you zoom" (measured up
  // to ~114px of transient drift). Snapping markers straight to their correct spot
  // kills that illusion; resting placement was always pixel-perfect.
  const g = L.markerClusterGroup({
    // Generous radius keeps nearby cities grouped into ONE guiding bubble you can
    // click to drill into — the behaviour the owner liked ("click the circle and
    // it opens up to the places inside it"). Default is 80; 60 keeps Europe from
    // collapsing into a single mega-blob while still showing meaningful clusters.
    maxClusterRadius: 60,
    showCoverageOnHover: false,
    // Click behaviour is CUSTOM (see 'clusterclick' below), so both built-ins
    // are off — leaving either true double-handles the click.
    spiderfyOnMaxZoom: false,
    zoomToBoundsOnClick: false,
    // DELIBERATELY no `disableClusteringAtZoom`. Forcing every marker to decluster
    // at a fixed zoom (we tried 8, then 5) was the root cause of BOTH map bugs:
    //   • it exploded the clusters into 345 loose pins that scatter off-screen as
    //     you zoom in → "everything disappears when I zoom in";
    //   • and it made dense regions a multi-click drill.
    // Letting Leaflet cluster purely by pixel-distance means a lone city (no
    // neighbour within maxClusterRadius px) already renders as its OWN pin that
    // opens on one click, while genuinely overlapping cities stay a clickable
    // bubble. Zooming a cluster always reveals its members — never a blank map.
    animate: false,
    iconCreateFunction(cluster) {
      const n = cluster.getChildCount();
      const allVisited = cluster.getAllChildMarkers().every(m => m._visited);
      const size = n < 10 ? 38 : n < 30 ? 46 : n < 60 ? 54 : 62;
      // At continental scale, say WHICH continent the bubble is — an anonymous
      // number over the ocean/desert reads as misplaced even when it isn't.
      // Only the bubble(s) holding a real share of the continent get the
      // caption; labelling every fragment stamped "EUROPE" three times into
      // the same 200px and cluttered the map.
      const label = (map.getZoom() <= 4 && n >= 6 && n >= 0.22 * (contTotals[continent] || Infinity))
        ? `<div class="owt-cluster-label">${CONTINENT_SHORT[continent] || continent}</div>` : '';
      return L.divIcon({
        html: `<div class="owt-cluster ${allVisited ? 'owt-cluster-done' : ''}">${n}</div>${label}`,
        className: '', iconSize: [size, size]
      });
    }
  });
  // Custom click — NEVER zoom-to-bounds. Fitting the members' bounding box
  // centres the camera on the box MIDPOINT, which for any dispersed cluster
  // (island+mainland pairs, a wide continental spread) is open ocean or a
  // different continent — the "click a circle and get thrown into the water /
  // Ireland lands in Africa" bug that kept coming back. Two honest behaviours,
  // both anchored to where the user actually clicked:
  //   • Small clusters (or max zoom): FAN THE MEMBERS OUT IN PLACE. No camera
  //     move at all, so the view can never jump anywhere wrong.
  //   • Bigger clusters: step the camera straight IN toward the clicked bubble.
  //     Zooming toward the click point splits it into the sub-clusters inside
  //     it, right where they were — never re-framed around a far-off midpoint.
  g.on('clusterclick', e => {
    const c = e.layer;
    const z = map.getZoom();
    if (c.getChildCount() <= 8 || z >= map.getMaxZoom()) { c.spiderfy(); return; }
    map.setView(c.getLatLng(), Math.min(z + 3, map.getMaxZoom()), { animate: false });
  });
  map.addLayer(g);
  clusterGroups[continent] = g;
  return g;
}

/* Build a Leaflet marker for every location once; reuse on filter. */
function buildAllMarkers() {
  allLocations.forEach(loc => {
    const icon = L.divIcon({
      className: 'custom-marker',
      html: buildMarkerHTML(loc),
      iconSize: [38, 38], iconAnchor: [19, 19]
    });
    const m = L.marker([loc.coordinates.lat, loc.coordinates.lng], { icon })
      .on('click', () => onMarkerClick(loc));
    m._loc = loc;
    m._visited = State.isVisited(loc.id);
    markerById[loc.id] = m;
  });
}

function buildMarkerHTML(loc) {
  const visited  = State.isVisited(loc.id);
  const saved    = State.isSaved(loc.id);
  const isHidden = loc.tag === 'hidden';
  // A "collection" region (e.g. Ancient Apocalypse) carries an `accent` colour
  // in data/index.json — it gets its own look purely from data, no per-set CSS,
  // regardless of famous/hidden. Everything else uses the gold/teal variants.
  const isColl   = !!loc.accent;
  const variant  = isColl ? 'collection' : (isHidden ? 'hidden' : 'famous');
  const accent   = isColl ? ` style="--marker-accent:${loc.accent}"` : '';
  const win = hasWindow(loc), walk = hasWalk(loc);
  const kind = windowKind(loc);
  const winLabel = kind === 'live' ? '🔴 live window' : kind === 'timelapse' ? '🪟 webcam stills' : kind === 'ambient' ? '🎬 ambient window' : '';
  const liveRow = (win || walk)
    ? `<small class="marker-tip-live">${winLabel}${win && walk ? ' · ' : ''}${walk ? '🚶 walking tour' : ''}</small>`
    : '';
  // a little corner dot on the pin itself, so it stands out without hovering
  const liveDot = (win || walk) ? '<div class="marker-live-dot"></div>' : '';
  return `
    <div class="marker marker-${variant} ${visited ? 'marker-visited' : ''}"${accent}>
      <span>${loc.emoji}</span>
      ${visited ? '<div class="marker-check">✓</div>' : ''}
      ${saved && !visited ? '<div class="marker-heart">♥</div>' : ''}
      ${liveDot}
      <div class="marker-tip">${loc.name}<small>${loc.country_flag} ${loc.country}</small>${liveRow}</div>
    </div>`;
}

/* Rich content a place has: a window (🔴 live cam OR 🎬 ambient recorded view)
   and/or a walking tour (walk). Used by the content filters and the
   at-a-glance badges on markers + suggestions. `windowKind` keeps the two
   window tiers distinguishable so the map always says which is which. */
function hasWindow(loc)   { return !!windowKind(loc); }
function windowKind(loc)  { const v = window.Webcam && Webcam.forWindow && Webcam.forWindow(loc); return v ? v.kind : null; }
function hasWalk(loc)     { return !!loc.walk; }

/* The current visible set, given query + tag + region filters. */
function visibleLocations() {
  const q = query.trim().toLowerCase();
  return allLocations.filter(loc => {
    if (tagFilter === 'saved')       { if (!State.isSaved(loc.id)) return false; }
    else if (tagFilter === 'live')   { if (windowKind(loc) !== 'live') return false; }
    else if (tagFilter === 'window') { if (!hasWindow(loc)) return false; }
    else if (tagFilter === 'walk')   { if (!hasWalk(loc)) return false; }
    else if (tagFilter === 'both')   { if (!(hasWindow(loc) && hasWalk(loc))) return false; }
    else if (tagFilter !== 'all' && loc.tag !== tagFilter) return false;
    if (regionFilter !== 'all' && loc.region_id !== regionFilter) return false;
    if (!q) return true;
    const hay = [
      loc.name, loc.country, loc.region,
      ...(loc.highlights || []).map(h => h.name)
    ].join(' ').toLowerCase();
    return hay.includes(q);
  });
}

function render() {
  const list = visibleLocations();
  const byContinent = {};
  list.forEach(loc => {
    const c = loc.continent || 'World';
    (byContinent[c] = byContinent[c] || []).push(markerById[loc.id]);
  });
  contTotals = {};
  Object.entries(byContinent).forEach(([c, m]) => { contTotals[c] = m.length; });
  Object.values(clusterGroups).forEach(g => g.clearLayers());
  Object.entries(byContinent).forEach(([c, markers]) => clusterGroupFor(c).addLayers(markers));
  updateStats(list.length);
}

function fitToVisible() {
  const list = visibleLocations();
  if (!list.length) return;
  const bounds = L.latLngBounds(list.map(l => [l.coordinates.lat, l.coordinates.lng]));
  map.fitBounds(bounds, { padding: [70, 70], maxZoom: 7 });
}

/* A marker click either adds the place to the tour (planning mode)
   or flies there (normal mode). */
function onMarkerClick(loc) {
  if (planning) {
    const added = State.toggleTrip(loc.id);
    showToast(added ? `Added ${loc.name} to your tour` : `Removed ${loc.name}`);
    renderTripPanel();
    drawTripRoute();
    return;
  }
  flyTo(loc);
}

let flying = false;
function flyTo(loc) {
  if (flying) return;
  flying = true;   // guard against double-trigger; reset on pageshow (bfcache) too
  const dest = { lat: loc.coordinates.lat, lng: loc.coordinates.lng };
  try { localStorage.setItem('owt_last_pos', JSON.stringify(dest)); } catch (e) { /* ignore */ }

  // Opening a place is a NAVIGATION — make it behave EXACTLY like picking a
  // search result, which the owner confirmed always works. We do NOT animate
  // the map first: any ease/zoom here (a) leaves a Leaflet zoom-animation
  // running when we navigate, which gets stranded across the Back-button
  // bfcache restore — the "can't zoom after I clicked a place" bug — and
  // (b) adds a delay where the page "looks like nothing happened". So: go now.
  // The cinematic plane flight is reserved for Fly-the-Tour (which never
  // navigates — it ends by removing its own layers).
  window.location.href = `location.html?id=${loc.id}`;
}

/* Shared plane animation along the great-circle arc from → dest, drawing
   into `layer`. Used for both single flights and the multi-leg tour.
   opts: { dur, fit, guide, dot, delay }. Returns { plane, trail }. */
function animatePlane(from, dest, layer, opts, onDone) {
  const o = Object.assign({ dur: 2100, fit: true, guide: true, dot: false, delay: 0 }, opts);
  const steps = 96;
  const arc = [];
  for (let i = 0; i <= steps; i++) arc.push(Geo.interpolate(from, dest, i / steps));
  const latlngs = arc.map(p => [p.lat, p.lng]);

  if (o.guide) L.polyline(latlngs, { color: 'rgba(201,168,76,0.22)', weight: 1.5, dashArray: '3 9', interactive: false }).addTo(layer);
  const trail = L.polyline([latlngs[0]], { color: '#c9a84c', weight: 2.5, opacity: 0.95, interactive: false }).addTo(layer);
  if (o.dot) L.circleMarker(latlngs[0], { radius: 4, color: '#c9a84c', fillColor: '#c9a84c', fillOpacity: 1, weight: 0, interactive: false }).addTo(layer);
  const plane = L.marker(latlngs[0], {
    icon: L.divIcon({ className: '', html: '<div class="plane-marker">✈️</div>', iconSize: [30, 30], iconAnchor: [15, 15] }),
    interactive: false, zIndexOffset: 1000
  }).addTo(layer);

  if (o.fit) map.fitBounds(L.latLngBounds(latlngs), { padding: [90, 90], animate: true, duration: 0.7, maxZoom: 7 });

  let start = null;
  function frame(ts) {
    if (start === null) start = ts;
    const p = Math.min((ts - start) / o.dur, 1);
    const e = p < 0.5 ? 2 * p * p : 1 - ((-2 * p + 2) ** 2) / 2;   // easeInOutQuad
    const idx = Math.round(e * steps);
    trail.setLatLngs(latlngs.slice(0, idx + 1));
    const cur = arc[idx];
    plane.setLatLng([cur.lat, cur.lng]);
    const brg = idx < steps ? Geo.bearing(cur, arc[idx + 1]) : Geo.bearing(arc[steps - 1], arc[steps]);
    const el = plane.getElement();
    if (el) { const pm = el.querySelector('.plane-marker'); if (pm) pm.style.transform = `rotate(${brg - 45}deg)`; }
    if (p < 1) requestAnimationFrame(frame);
    else onDone();
  }
  setTimeout(() => requestAnimationFrame(frame), o.delay);
  return { plane, trail };
}

/* ============================================================
   FLY THE TOUR — plan an ordered multi-city route, then watch
   the plane fly the whole journey leg by leg.
   ============================================================ */
function tripLocs() {
  return State.trip.map(id => allLocations.find(l => l.id === id)).filter(Boolean);
}

function toggleTripPanel() {
  if (touring) return;
  planning = !planning;
  document.getElementById('trip-btn').classList.toggle('active', planning);
  document.getElementById('trip-panel').classList.toggle('open', planning);
  document.getElementById('plan-hint').classList.toggle('show', planning);
  if (planning) { renderTripPanel(); drawTripRoute(); }
  else if (tripLayer) { map.removeLayer(tripLayer); tripLayer = null; }
}

function renderTripPanel() {
  const list    = document.getElementById('trip-list');
  const summary = document.getElementById('trip-summary');
  const flyBtn  = document.getElementById('trip-fly');
  const locs = tripLocs();

  if (!locs.length) {
    list.innerHTML = '<div class="trip-empty">Tap cities on the map to build a route, then fly the whole tour. ✈️</div>';
    summary.textContent = '';
    flyBtn.disabled = true;
    return;
  }

  list.innerHTML = locs.map((l, i) => `
    <div class="trip-row">
      <span class="trip-num">${i + 1}</span>
      <span class="trip-emoji">${l.emoji}</span>
      <span class="trip-info"><strong>${l.name}</strong><small>${l.country_flag || ''} ${l.country}</small></span>
      <span class="trip-ctrls">
        <button class="trip-mv" data-id="${l.id}" data-dir="-1" ${i === 0 ? 'disabled' : ''} title="Move up">▲</button>
        <button class="trip-mv" data-id="${l.id}" data-dir="1" ${i === locs.length - 1 ? 'disabled' : ''} title="Move down">▼</button>
        <button class="trip-rm" data-id="${l.id}" title="Remove">✕</button>
      </span>
    </div>`).join('');

  list.querySelectorAll('.trip-mv').forEach(b => b.addEventListener('click', () => {
    State.moveTrip(b.dataset.id, parseInt(b.dataset.dir, 10));
    renderTripPanel(); drawTripRoute();
  }));
  list.querySelectorAll('.trip-rm').forEach(b => b.addEventListener('click', () => {
    State.removeTrip(b.dataset.id);
    renderTripPanel(); drawTripRoute();
  }));

  let km = 0;
  for (let i = 1; i < locs.length; i++) km += Geo.km(locs[i - 1].coordinates, locs[i].coordinates);
  summary.innerHTML = locs.length < 2
    ? '<strong>1</strong> stop · add another to fly'
    : `<strong>${locs.length}</strong> stops · <strong>${km.toLocaleString()}</strong> km`;
  flyBtn.disabled = locs.length < 2;
}

/* Faint dashed preview of the planned route, with numbered stops. */
function drawTripRoute() {
  if (tripLayer) { map.removeLayer(tripLayer); tripLayer = null; }
  const locs = tripLocs();
  if (!locs.length) return;
  tripLayer = L.layerGroup().addTo(map);

  for (let i = 1; i < locs.length; i++) {
    const pts = [];
    for (let s = 0; s <= 40; s++) pts.push(Geo.interpolate(locs[i - 1].coordinates, locs[i].coordinates, s / 40));
    L.polyline(pts.map(p => [p.lat, p.lng]),
      { color: '#c9a84c', weight: 2, opacity: 0.8, dashArray: '6 7', interactive: false }).addTo(tripLayer);
  }
  locs.forEach((l, i) => {
    L.marker([l.coordinates.lat, l.coordinates.lng], {
      icon: L.divIcon({ className: '', html: `<div class="journey-dot">${i + 1}</div>`, iconSize: [22, 22], iconAnchor: [11, 11] }),
      interactive: false
    }).addTo(tripLayer);
  });
}

/* Fly the planned route end-to-end, one leg at a time. */
function flyTour() {
  if (touring) return;
  const locs = tripLocs();
  if (locs.length < 2) { showToast('Add at least two stops to fly your tour ✈️'); return; }

  touring = true;
  planning = false;
  document.getElementById('trip-btn').classList.remove('active');
  document.getElementById('trip-panel').classList.remove('open');
  document.getElementById('plan-hint').classList.remove('show');
  if (tripLayer) { map.removeLayer(tripLayer); tripLayer = null; }

  const layer = L.layerGroup().addTo(map);
  // Faint full-route guide line under everything.
  for (let i = 1; i < locs.length; i++) {
    const pts = [];
    for (let s = 0; s <= 40; s++) pts.push(Geo.interpolate(locs[i - 1].coordinates, locs[i].coordinates, s / 40));
    L.polyline(pts.map(p => [p.lat, p.lng]),
      { color: 'rgba(201,168,76,0.18)', weight: 1.5, dashArray: '3 9', interactive: false }).addTo(layer);
  }
  const dropDot = (l, n) => L.marker([l.coordinates.lat, l.coordinates.lng], {
    icon: L.divIcon({ className: '', html: `<div class="journey-dot">${n}</div>`, iconSize: [22, 22], iconAnchor: [11, 11] }),
    interactive: false
  }).addTo(layer);
  dropDot(locs[0], 1);

  let totalKm = 0, plane = null;
  const leg = (i) => {
    if (i >= locs.length - 1) {
      showToast(`🧳 Tour complete · ${locs.length} stops · ${totalKm.toLocaleString()} km`);
      setTimeout(() => { map.removeLayer(layer); touring = false; }, 4500);
      return;
    }
    const from = locs[i].coordinates, dest = locs[i + 1].coordinates;
    totalKm += Geo.km(from, dest);
    showToast(`✈️ ${locs[i].name} → ${locs[i + 1].name}  ·  leg ${i + 1} of ${locs.length - 1}`);
    if (plane) layer.removeLayer(plane);
    const res = animatePlane(from, dest, layer, { dur: 1600, fit: true, guide: false, delay: i === 0 ? 600 : 250 }, () => {
      dropDot(locs[i + 1], i + 2);
      setTimeout(() => leg(i + 1), 200);
    });
    plane = res.plane;
  };
  leg(0);
}

function surpriseMe() {
  const list = visibleLocations();
  if (!list.length) return;
  const loc = list[Math.floor(Math.random() * list.length)];
  const pill = document.getElementById('country-label');
  pill.classList.add('flash');
  setTimeout(() => pill.classList.remove('flash'), 600);
  flyTo(loc);
}

/* ============================================================
   DROP IN — tap anywhere on the map and watch a video from there.
   v1: snap to the nearest place we know and play its walkthrough
   (curated tour video, else a Ken Burns photo flythrough). Like
   virtualvacation's "videarth", but the player is fully skippable.
   ============================================================ */
function nearestLocation(latlng) {
  let best = null, bestKm = Infinity;
  for (const l of allLocations) {
    const d = Geo.km({ lat: latlng.lat, lng: latlng.lng }, l.coordinates);
    if (d < bestKm) { bestKm = d; best = l; }
  }
  return best ? { loc: best, km: bestKm } : null;
}

// Beyond this, a tap is open ocean / empty interior — be honest, don't snap
// the user to a city thousands of km away.
const DROP_MAX_KM = 1500;

function dropInAt(latlng) {
  const hit = nearestLocation(latlng);
  if (!hit) return;
  if (hit.km > DROP_MAX_KM) {
    showToast('🌊 Nothing close enough out here — tap nearer a city to drop in');
    return;
  }
  const subtitle = hit.km < 25
    ? `${hit.loc.name}, ${hit.loc.country}`
    : `Nearest to your tap · ${hit.loc.name} · ${Math.round(hit.km).toLocaleString()} km`;
  Walkthrough.open(hit.loc, { subtitle });
}

function toggleDropIn() {
  dropOn = !dropOn;
  const btn = document.getElementById('dropin-btn');
  if (btn) btn.classList.toggle('active', dropOn);
  const mapEl = document.getElementById('map');
  if (mapEl) mapEl.classList.toggle('dropin-cursor', dropOn);
  showToast(dropOn
    ? '🎬 Drop In on — tap anywhere on the map to watch a video from there'
    : 'Drop In off');
}

/* ---- "My Journey": trace the route through visited places, in order ---- */
function visitedRoute() {
  // State.visited preserves chronological order (push on first visit).
  return State.visited
    .map(id => allLocations.find(l => l.id === id))
    .filter(Boolean);
}

function toggleJourney() {
  journeyOn = !journeyOn;
  const btn = document.getElementById('journey-btn');
  if (!journeyOn) { if (journeyLayer) { map.removeLayer(journeyLayer); journeyLayer = null; } btn.classList.remove('active'); return; }

  const route = visitedRoute();
  if (route.length < 2) {
    journeyOn = false;
    btn.classList.remove('active');
    showToast('Explore at least two places to trace your journey ✈️');
    return;
  }
  btn.classList.add('active');
  if (journeyLayer) map.removeLayer(journeyLayer);

  const pts = route.map(l => [l.coordinates.lat, l.coordinates.lng]);
  journeyLayer = L.layerGroup();
  L.polyline(pts, { color: '#c9a84c', weight: 2.5, opacity: 0.9, dashArray: '8 8', className: 'journey-line' }).addTo(journeyLayer);
  route.forEach((l, i) => {
    L.marker([l.coordinates.lat, l.coordinates.lng], {
      icon: L.divIcon({ className: '', html: `<div class="journey-dot">${i + 1}</div>`, iconSize: [22, 22], iconAnchor: [11, 11] })
    }).addTo(journeyLayer);
  });
  journeyLayer.addTo(map);

  let km = 0;
  for (let i = 1; i < route.length; i++) km += Geo.km(route[i - 1].coordinates, route[i].coordinates);
  map.fitBounds(L.latLngBounds(pts), { padding: [80, 80] });
  showToast(`✈️ Your journey: ${route.length} stops · ${km.toLocaleString()} km travelled`);
}

let toastTimer = null;
function showToast(msg) {
  let t = document.getElementById('owt-toast');
  if (!t) { t = document.createElement('div'); t.id = 'owt-toast'; t.className = 'toast'; document.body.appendChild(t); }
  t.textContent = msg;
  requestAnimationFrame(() => t.classList.add('show'));
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => t.classList.remove('show'), 3600);
}

function updateStats(showing) {
  const v = State.visited.length;
  const t = allLocations.length;
  const countries = new Set(allLocations.filter(l => State.isVisited(l.id)).map(l => l.country)).size;
  document.getElementById('stat-visited').innerHTML = `<strong>${v}</strong> / ${t} explored`;
  const cEl = document.getElementById('stat-countries');
  if (cEl) cEl.innerHTML = `<strong>${countries}</strong> ${countries === 1 ? 'country' : 'countries'}`;
  const sEl = document.getElementById('stat-showing');
  const sPill = document.getElementById('stat-showing-pill');
  if (sEl) {
    const filtered = showing !== t;
    sEl.textContent = filtered ? `${showing} shown` : '';
    if (sPill) sPill.style.display = filtered ? '' : 'none';
  }
}

/* Build a region filter chip per loaded region (+ All). */
function setupRegionChips() {
  const wrap = document.getElementById('region-bar');
  if (!wrap || loadedRegions.length < 2) return;
  const chips = [{ id: 'all', flag: '🌍', name: 'All' },
                 ...loadedRegions.map(r => ({ id: r.id, flag: r.flag, name: r.name, accent: r.accent }))];
  wrap.innerHTML = chips.map((c, i) => {
    const coll  = c.accent ? ' region-chip-collection' : '';
    const style = c.accent ? ` style="--chip-accent:${c.accent}"` : '';
    return `<button class="region-chip${coll} ${i === 0 ? 'active' : ''}" data-region="${c.id}"${style}>${c.flag} ${c.name}</button>`;
  }).join('');
  wrap.querySelectorAll('.region-chip').forEach(btn => {
    btn.addEventListener('click', () => {
      wrap.querySelectorAll('.region-chip').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      regionFilter = btn.dataset.region;
      render(); fitToVisible();
    });
  });
}

/* ============================================================
   Day / night terminator — shades the half of Earth in darkness
   right now, with a sun marker at the subsolar (local-noon) point.
   Standard low-precision solar position math; no dependencies.
   ============================================================ */
function solarPosition(date = new Date()) {
  const rad = Math.PI / 180, deg = 180 / Math.PI;
  const d = date / 86400000 + 2440587.5 - 2451545.0;   // days since J2000
  const g = (357.529 + 0.98560028 * d) * rad;          // mean anomaly
  const q =  280.459 + 0.98564736 * d;                 // mean longitude
  const L = (q + 1.915 * Math.sin(g) + 0.020 * Math.sin(2 * g)) * rad; // ecliptic lon
  const e = (23.439 - 0.00000036 * d) * rad;           // obliquity
  const delta = Math.asin(Math.sin(e) * Math.sin(L)) * deg;            // declination
  const RA = Math.atan2(Math.cos(e) * Math.sin(L), Math.cos(L)) * deg; // right ascension
  let GMST = (280.46061837 + 360.98564736629 * d) % 360;
  if (GMST < 0) GMST += 360;
  let subLng = (RA - GMST + 540) % 360 - 180;          // subsolar longitude
  return { delta, RA, GMST, subLat: delta, subLng };
}

function terminatorPolygon(sp) {
  const rad = Math.PI / 180, deg = 180 / Math.PI;
  const pts = [];
  for (let lng = -180; lng <= 180; lng += 1) {
    const ha = (sp.GMST + lng - sp.RA) * rad;           // hour angle
    const lat = Math.atan(-Math.cos(ha) / Math.tan(sp.delta * rad)) * deg;
    pts.push([lat, lng]);
  }
  // Close the ring around whichever pole is currently in darkness.
  if (sp.delta > 0) { pts.push([-90, 180], [-90, -180]); }
  else              { pts.push([ 90, 180], [ 90, -180]); }
  return pts;
}

function drawNight() {
  const sp = solarPosition();
  if (nightLayer) map.removeLayer(nightLayer);
  nightLayer = L.polygon(terminatorPolygon(sp), {
    stroke: true, color: 'rgba(120,150,200,0.35)', weight: 1,
    fill: true, fillColor: '#040810', fillOpacity: 0.42, interactive: false
  }).addTo(map);

  const sunIcon = L.divIcon({ className: '', html: '<div class="sun-marker">☀️</div>', iconSize: [30, 30], iconAnchor: [15, 15] });
  if (sunMarker) map.removeLayer(sunMarker);
  sunMarker = L.marker([sp.subLat, sp.subLng], { icon: sunIcon, interactive: false }).addTo(map);
}

function toggleDayNight() {
  nightOn = !nightOn;
  const btn = document.getElementById('daynight-btn');
  if (!nightOn) {
    if (nightLayer) { map.removeLayer(nightLayer); nightLayer = null; }
    if (sunMarker)  { map.removeLayer(sunMarker);  sunMarker = null; }
    if (nightTimer) { clearInterval(nightTimer); nightTimer = null; }
    btn.classList.remove('active');
    return;
  }
  btn.classList.add('active');
  drawNight();
  nightTimer = setInterval(drawNight, 60000);   // keep it current
}

/* ---- Wire controls ---- */
document.querySelectorAll('.filter-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    tagFilter = btn.dataset.filter;
    render();
    fitToVisible();   // bring the filtered set on-screen (esp. the few window/both places)
  });
});

/* ---- Search: live map filter + an autocomplete dropdown to pick from ---- */
const searchEl  = document.getElementById('search-input');
const suggestEl = document.getElementById('search-suggest');
let sugList = [], sugIdx = -1;

function escMap(s) {
  return String(s).replace(/[&<>"']/g, c =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

/* Rank matches so a name prefix ("poi" → Point Farms) beats a buried country hit. */
function buildSearchSuggestions(raw) {
  const q = raw.trim().toLowerCase();
  if (!q) return [];
  const scored = [];
  for (const loc of allLocations) {
    const name    = (loc.name || '').toLowerCase();
    const country = (loc.country || '').toLowerCase();
    const region  = (loc.region || loc.province || '').toLowerCase();
    const hls     = (loc.highlights || []).map(h => (h.name || '').toLowerCase());
    let score = -1;
    if (name.startsWith(q)) score = 0;
    else if (name.includes(q)) score = 1;
    else if (region.startsWith(q) || country.startsWith(q)) score = 2;
    else if (country.includes(q) || region.includes(q)) score = 3;
    else if (hls.some(h => h.includes(q))) score = 4;
    if (score >= 0) scored.push([score, loc]);
  }
  scored.sort((a, b) => a[0] - b[0] || a[1].name.localeCompare(b[1].name));
  return scored.slice(0, 8).map(s => s[1]);
}

function renderSuggest() {
  if (!suggestEl) return;
  if (!sugList.length) { closeSuggest(); return; }
  suggestEl.innerHTML = sugList.map((loc, i) => {
    const sub  = [loc.region || loc.province, loc.country].filter(Boolean).join(' · ');
    const walk = hasWalk(loc);
    const kind = windowKind(loc);
    const winMark = kind === 'live' ? '🔴' : kind === 'timelapse' ? '🪟' : kind === 'ambient' ? '🎬' : '';
    const tags = `${winMark}${walk ? '🚶' : ''}`;
    const title = [kind === 'live' && 'live window', kind === 'timelapse' && 'webcam stills', kind === 'ambient' && 'ambient window', walk && 'walking tour'].filter(Boolean).join(' + ');
    const badge = tags ? `<span class="ss-badge" title="${title}">${tags}</span>` : '';
    return `<button type="button" class="ss-item${i === sugIdx ? ' active' : ''}" role="option" data-i="${i}">
        <span class="ss-emoji">${loc.emoji || '📍'}</span>
        <span class="ss-text">
          <span class="ss-name">${escMap(loc.name)}</span>
          <span class="ss-sub">${escMap(sub)} ${loc.country_flag || ''}</span>
        </span>${badge}
      </button>`;
  }).join('');
  suggestEl.classList.add('open');
  if (searchEl) searchEl.setAttribute('aria-expanded', 'true');
  // mousedown (not click) so it fires before the input's blur closes the list.
  suggestEl.querySelectorAll('.ss-item').forEach(el => {
    el.addEventListener('mousedown', ev => {
      ev.preventDefault();
      const loc = sugList[+el.dataset.i];
      if (loc) chooseSuggestion(loc);
    });
  });
}

function chooseSuggestion(loc) {
  if (searchEl) searchEl.value = loc.name;
  closeSuggest();
  flyTo(loc);
}

function closeSuggest() {
  sugList = []; sugIdx = -1;
  if (suggestEl) { suggestEl.classList.remove('open'); suggestEl.innerHTML = ''; }
  if (searchEl) searchEl.setAttribute('aria-expanded', 'false');
}

function refreshSuggest() {
  sugList = buildSearchSuggestions(query);
  sugIdx = -1;
  renderSuggest();
}

if (searchEl) {
  searchEl.addEventListener('input', e => { query = e.target.value; render(); refreshSuggest(); });
  searchEl.addEventListener('focus', () => { if (query.trim()) refreshSuggest(); });
  searchEl.addEventListener('blur', () => setTimeout(closeSuggest, 130));
  searchEl.addEventListener('keydown', e => {
    if (e.key === 'ArrowDown' && sugList.length) {
      e.preventDefault(); sugIdx = (sugIdx + 1) % sugList.length; renderSuggest();
    } else if (e.key === 'ArrowUp' && sugList.length) {
      e.preventDefault(); sugIdx = (sugIdx - 1 + sugList.length) % sugList.length; renderSuggest();
    } else if (e.key === 'Enter') {
      const pick = sugIdx >= 0 ? sugList[sugIdx] : (sugList[0] || visibleLocations()[0]);
      if (pick) chooseSuggestion(pick);
    } else if (e.key === 'Escape') {
      if (suggestEl && suggestEl.classList.contains('open')) closeSuggest();
      else { searchEl.value = ''; query = ''; render(); }
    }
  });
}

const surpriseEl = document.getElementById('surprise-btn');
if (surpriseEl) surpriseEl.addEventListener('click', surpriseMe);

const dropInEl = document.getElementById('dropin-btn');
if (dropInEl) dropInEl.addEventListener('click', toggleDropIn);

const journeyEl = document.getElementById('journey-btn');
if (journeyEl) journeyEl.addEventListener('click', toggleJourney);

const dayNightEl = document.getElementById('daynight-btn');
if (dayNightEl) dayNightEl.addEventListener('click', toggleDayNight);

const tripBtnEl = document.getElementById('trip-btn');
if (tripBtnEl) tripBtnEl.addEventListener('click', toggleTripPanel);

const tripCloseEl = document.getElementById('trip-close');
if (tripCloseEl) tripCloseEl.addEventListener('click', toggleTripPanel);

const tripFlyEl = document.getElementById('trip-fly');
if (tripFlyEl) tripFlyEl.addEventListener('click', flyTour);

const tripClearEl = document.getElementById('trip-clear');
if (tripClearEl) tripClearEl.addEventListener('click', () => {
  State.clearTrip(); renderTripPanel(); drawTripRoute();
});

/* Returning to the map via the browser's Back button can restore this page from
   the bfcache with STALE state: a just-started flight left `flying` true (which
   then blocks every marker click — "Berlin won't open"), and Leaflet's cached
   container size / interaction handlers can be out of sync so the map "feels
   stuck / can't zoom". Reset all of that on every show, restore or fresh. */
window.addEventListener('pageshow', () => {
  flying = false;
  if (typeof map !== 'undefined' && map) {
    // map.stop() is Leaflet's own "cancel any running pan/zoom animation and
    // clear _animatingZoom". This is the belt to the braces above: even if some
    // animation was left mid-flight, the map returns fully interactive.
    try { map.stop(); } catch (e) { /* ignore */ }
    map.invalidateSize(false);
    try {
      map.scrollWheelZoom.enable(); map.dragging.enable();
      map.touchZoom.enable(); map.doubleClickZoom.enable(); map.boxZoom.enable();
    } catch (e) { /* ignore */ }
  }
});

initMap();
