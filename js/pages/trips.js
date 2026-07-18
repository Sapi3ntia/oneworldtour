/* ============================================================
   TRIPS — the index of curated routes, and one route in detail.

   Two views in one page, chosen by ?id=:
     • no id  → every trip as a card, with what it can actually show
     • ?id=x  → the route drawn on the world map, then stop by stop.

   Arriving from here carries &trip= into the location page, which is
   what turns a place into "stop 4 of 10" with an onward link. Nothing
   is stored for that — the route lives in the URL, so a shared link
   drops someone into the same place on the same trip.
   ============================================================ */
import { loadTrips, tripById, progress } from '../lib/trips.js';
import { loadAll } from '../lib/data.js';
import { State } from '../lib/state.js';
import { WorldMap } from '../worldmap.js';
import { el, qs } from '../lib/dom.js';
import { lazyPhoto } from '../lib/photos.js';

const stopHref = (trip, stop) =>
  `location.html?id=${encodeURIComponent(stop.place.id)}&trip=${encodeURIComponent(trip.id)}`;

function toast(msg) {
  const t = qs('#toast');
  t.textContent = msg;
  t.classList.add('show');
  clearTimeout(t._h);
  t._h = setTimeout(() => t.classList.remove('show'), 2600);
}

/* Scene tally as icons — honest about what a route can actually show. */
function sceneLine(scenes, total) {
  const bits = [
    ['🚶', scenes.walk], ['🚗', scenes.drive], ['🔴', scenes.live],
    ['🪟', scenes.window], ['🏛️', scenes.monuments],
  ];
  return el('span', { class: 'scene-tally' },
    bits.map(([icon, n]) => el('span', {
      class: 'tally' + (n ? '' : ' zero'),
      title: `${n} of ${total} stops`,
    }, `${icon} ${n}`)),
  );
}

/* ---------------- index view ---------------- */
function tripCard(trip) {
  const pr = progress(trip);
  const card = el('a', { class: 'card trip-card', href: `trips.html?id=${encodeURIComponent(trip.id)}` },
    /* lazyPhoto clears its target's text once a photo lands, so the
       badge lives beside the photo layer, never inside it. */
    el('div', { class: 'tc-media' },
      el('div', { class: 'tc-ph' }, trip.emoji || '🧭'),
      pr.done ? el('span', { class: 'tc-progress' }, `${pr.done}/${pr.total}`) : null,
    ),
    el('div', { class: 'tc-body' },
      el('div', { class: 'tc-kicker' }, `${trip.region} · ${trip.days}`),
      el('div', { class: 'tc-name' }, trip.name),
      el('div', { class: 'tc-tagline' }, trip.tagline),
      el('div', { class: 'tc-foot' },
        el('span', {}, `${trip.stops.length} stops · ${trip.distance.toLocaleString()} km`),
        sceneLine(trip.scenes, trip.stops.length),
      ),
    ),
  );
  lazyPhoto(card.querySelector('.tc-ph'), trip.heroPlace, 640);
  return card;
}

function renderIndex(trips) {
  qs('#index-view').hidden = false;
  document.title = 'Trips — One World Tour';

  const stops = trips.reduce((n, t) => n + t.stops.length, 0);
  const totalKm = trips.reduce((n, t) => n + t.distance, 0);
  qs('#trips-stats').append(
    el('span', {}, el('b', {}, String(trips.length)), ' routes'),
    el('span', {}, el('b', {}, String(stops)), ' stops'),
    el('span', {}, el('b', {}, totalKm.toLocaleString()), ' km end to end'),
  );
  qs('#trip-grid').append(...trips.map(tripCard));
}

/* ---------------- detail view ---------------- */
function factRow(dl, k, v) {
  dl.append(el('dt', {}, k), el('dd', {}, v));
}

function stopRow(trip, stop, i) {
  const { place: p, flags: f } = stop;
  const visited = State.isVisited(p.id);
  const row = el('li', { class: 'stop' + (visited ? ' stop-done' : '') },
    el('a', { class: 'stop-link', href: stopHref(trip, stop) },
      el('span', { class: 'stop-n' }, String(i + 1)),
      el('span', { class: 'stop-ph' }, p.emoji || '📍'),
      el('span', { class: 'stop-text' },
        el('span', { class: 'stop-name' },
          p.name,
          visited ? el('span', { class: 'stop-stamp', title: 'Visited' }, '📘') : null,
        ),
        el('span', { class: 'stop-where' }, `${p.country_flag || ''} ${p.country}`.trim()),
        stop.note ? el('span', { class: 'stop-note' }, stop.note) : null,
      ),
      el('span', { class: 'stop-scenes' },
        f.walk ? el('span', { class: 'badge badge-walk' }, '🚶') : null,
        f.drive ? el('span', { class: 'badge badge-drive' }, '🚗') : null,
        f.live ? el('span', { class: 'badge badge-live' }, el('span', { class: 'dot' }), 'Live') : null,
        f.window ? el('span', { class: 'badge badge-window' }, '🪟') : null,
        f.monuments ? el('span', { class: 'badge badge-monu' }, '🏛️') : null,
      ),
    ),
  );
  lazyPhoto(row.querySelector('.stop-ph'), p, 320);
  return row;
}

async function renderTrip(trip) {
  qs('#trip-view').hidden = false;
  document.title = `${trip.name} — One World Tour`;

  qs('#trip-kicker').textContent = `${trip.emoji} ${trip.region} · ${trip.mode}`;
  qs('#trip-name').textContent = trip.name;
  qs('#trip-tagline').textContent = trip.tagline;
  qs('#trip-blurb').textContent = trip.blurb;

  /* facts */
  const dl = qs('#trip-facts');
  factRow(dl, 'Stops', String(trip.stops.length));
  factRow(dl, 'Distance', `${trip.distance.toLocaleString()} km as the crow flies`);
  factRow(dl, 'Unhurried', trip.days);
  factRow(dl, 'Getting around', trip.mode);
  factRow(dl, 'From', trip.stops[0].place.name);
  factRow(dl, 'To', trip.stops[trip.stops.length - 1].place.name);

  /* progress + start/resume */
  const pr = progress(trip);
  qs('#trip-progress').append(
    el('div', { class: 'bar' }, el('div', { class: 'bar-fill', style: `width:${pr.pct}%` })),
    el('div', { class: 'bar-label faint' },
      pr.done ? `${pr.done} of ${pr.total} stops stamped in your passport`
              : 'No stops stamped yet'),
  );
  qs('#start-btn').href = stopHref(trip, trip.stops[0]);
  const nextUp = trip.stops.find(s => !State.isVisited(s.place.id));
  if (pr.done && nextUp) {
    const rb = qs('#resume-btn');
    rb.hidden = false;
    rb.href = stopHref(trip, nextUp);
    rb.textContent = `↻ Resume at ${nextUp.place.name}`;
  }

  /* stop list */
  qs('#stops-count').textContent =
    `${trip.stops.length} stops · ${trip.distance.toLocaleString()} km`;
  qs('#stop-list').append(...trip.stops.map((s, i) => stopRow(trip, s, i)));

  /* map: the route only — no country nodes, no unrelated cities */
  const map = new WorldMap(qs('#trip-map'), {});
  await map.loadWorld();
  map.setPlaces([]);
  const pts = trip.stops.map(s => s.place);
  for (let i = 1; i < pts.length; i++) {
    map.drawLine(pts[i - 1].coordinates, pts[i].coordinates, 'wmap-route');
  }
  trip.stops.forEach((s, i) => {
    map.addStop(s.place.coordinates.lat, s.place.coordinates.lng, String(i + 1), {
      cls: State.isVisited(s.place.id) ? 'wmap-stop-done' : '',
      title: `${i + 1}. ${s.place.name}`,
      onClick: () => { location.href = stopHref(trip, s); },
    });
  });
  /* minW keeps a compact route (the Grand Circle spans ~10 map units) from
     zooming into featureless space — assets/world.json is country-level, so
     there are no state borders down there to orient by. */
  map.flyToPlaces(pts, 900, false, 105);
}

/* ---------------- boot ---------------- */
async function boot() {
  const id = new URLSearchParams(location.search).get('id');
  const trips = await loadTrips();

  qs('#surprise-top').addEventListener('click', async () => {
    const all = await loadAll();
    const p = all[Math.floor(Math.random() * all.length)];
    location.href = `location.html?id=${encodeURIComponent(p.id)}`;
  });

  qs('#foot-stats').textContent =
    `${trips.length} routes · ${State.visited.length} places visited`;

  if (!id) return renderIndex(trips);

  const trip = await tripById(id);
  if (!trip) { qs('#notfound').hidden = false; return; }
  await renderTrip(trip);
}

boot().catch(err => {
  console.error(err);
  toast('Something broke loading the trips — check the console.');
});
