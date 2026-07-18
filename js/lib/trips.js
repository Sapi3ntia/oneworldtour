/* ============================================================
   TRIPS — curated multi-stop routes over the places we already have.

   A trip is editorial, not generated: a human ordered the stops and
   wrote why each one is on the route. data/trips.json holds only
   place *ids*, so a trip can never invent a destination — it can only
   point at somewhere the atlas already goes.

   HONESTY (same rule as the four scenes)
     A stop whose id doesn't resolve is DROPPED, loudly, to the console
     — never rendered as a placeholder. tools/check_trips.py makes that
     path unreachable in a shipped build, but the runtime still refuses
     to draw a city it can't actually take you to.

   DISTANCE is computed here from the real coordinates, never authored.
   It is point-to-point great-circle: the sum of straight lines between
   consecutive stops. That is NOT the road/rail distance (the Grand
   Circle drives ~2,250 km but measures ~1,127 km this way), so the UI
   must always label it "as the crow flies". Authored mileage would rot
   the moment a stop changed; this can't.
   ============================================================ */
import { loadAll } from './data.js';
import { km } from './geo.js';
import { sceneFlags } from './media.js';
import { State } from './state.js';

let trips = null, inflight = null;

async function build() {
  const [places, doc] = await Promise.all([
    loadAll(),
    fetch('data/trips.json', { cache: 'no-cache' })
      .then(r => (r.ok ? r.json() : null)).catch(() => null),
  ]);
  if (!doc?.trips) { trips = []; return; }

  const byId = new Map(places.map(p => [p.id, p]));

  trips = doc.trips.map(t => {
    const stops = [], missing = [];
    for (const s of t.stops || []) {
      const place = byId.get(s.id);
      if (place) stops.push({ place, note: s.note || '', flags: sceneFlags(place) });
      else missing.push(s.id);
    }
    if (missing.length) {
      console.warn(`[trip ${t.id}] dropped unknown stop(s): ${missing.join(', ')} — ` +
                   'run tools/check_trips.py');
    }

    let distance = 0;
    for (let i = 1; i < stops.length; i++) {
      distance += km(stops[i - 1].place.coordinates, stops[i].place.coordinates);
    }

    const scenes = { walk: 0, drive: 0, live: 0, window: 0, monuments: 0 };
    for (const s of stops) for (const k of Object.keys(scenes)) if (s.flags[k]) scenes[k]++;

    /* Card photo. Stop 1 is the honest default, but it's the trailhead,
       not the point — the Grand Circle starts in a Las Vegas car park.
       An optional `hero` stop id overrides it. */
    const hero = stops.find(s => s.place.id === t.hero) || stops[0];

    return { ...t, stops, missing, distance: Math.round(distance), scenes,
             heroPlace: hero ? hero.place : null };
  }).filter(t => t.stops.length >= 2);   // fewer than two stops isn't a route
}

export async function loadTrips() {
  if (!inflight) inflight = build();
  await inflight;
  return trips;
}

export async function tripById(id) {
  return (await loadTrips()).find(t => t.id === id) || null;
}

/* Trips passing through a place, with this place's index in each —
   powers the "you're on a route" strip on the location page. */
export async function tripsThrough(placeId) {
  const all = await loadTrips();
  const out = [];
  for (const t of all) {
    const i = t.stops.findIndex(s => s.place.id === placeId);
    if (i >= 0) out.push({ trip: t, index: i });
  }
  return out;
}

/* How far through a trip you've actually been. Reads the same
   owt_visited passport key everything else stamps. */
export function progress(trip) {
  const done = trip.stops.filter(s => State.isVisited(s.place.id)).length;
  return { done, total: trip.stops.length,
           pct: Math.round((done / trip.stops.length) * 100) };
}
