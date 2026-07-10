/* ============================================================
   GEO — the app's one projection + earth-math module.

   The map is a pre-projected SVG (assets/world.json, built by
   tools/build_worldmap.py). These constants MUST match that script:
   Natural Earth I raw polynomial × S onto a 1000×520 canvas.
   ============================================================ */

export const MAP_W = 1000;
export const MAP_H = 520;
const S = (MAP_W / 2) / (Math.PI * 0.8707);   // raw → svg scale

/* lat/lng (deg) → svg {x, y}. Same math as the Python builder. */
export function project(lat, lng) {
  const lam = lng * Math.PI / 180;
  const phi = lat * Math.PI / 180;
  const p2 = phi * phi, p4 = p2 * p2;
  const rx = lam * (0.8707 - 0.131979 * p2 + p4 * (-0.013791 + p4 * (0.003971 * p2 - 0.001529 * p4)));
  const ry = phi * (1.007226 + p2 * (0.015085 + p4 * (-0.044475 + 0.028874 * p2 - 0.005916 * p4)));
  return { x: MAP_W / 2 + rx * S, y: MAP_H / 2 - ry * S };
}

/* svg {x,y} → {lat, lng} (deg). Newton iteration on the y-polynomial
   (d3-geo's approach) — used by City Guesser map clicks. */
export function unproject(x, y) {
  const rx = (x - MAP_W / 2) / S;
  const ry = (MAP_H / 2 - y) / S;
  let phi = ry, i = 25, delta;
  do {
    const p2 = phi * phi, p4 = p2 * p2;
    delta = (phi * (1.007226 + p2 * (0.015085 + p4 * (-0.044475 + 0.028874 * p2 - 0.005916 * p4))) - ry) /
            (1.007226 + p2 * (0.015085 * 3 + p4 * (-0.044475 * 7 + 0.028874 * 9 * p2 - 0.005916 * 11 * p4)));
    phi -= delta;
  } while (Math.abs(delta) > 1e-6 && --i > 0);
  const p2 = phi * phi, p4 = p2 * p2;
  const lam = rx / (0.8707 - 0.131979 * p2 + p4 * (-0.013791 + p4 * (0.003971 * p2 - 0.001529 * p4)));
  return { lat: phi * 180 / Math.PI, lng: lam * 180 / Math.PI };
}

/* Great-circle distance in km. */
export function km(a, b) {
  const R = 6371, toRad = d => d * Math.PI / 180;
  const dLat = toRad(b.lat - a.lat), dLng = toRad(b.lng - a.lng);
  const s = Math.sin(dLat / 2) ** 2 +
    Math.cos(toRad(a.lat)) * Math.cos(toRad(b.lat)) * Math.sin(dLng / 2) ** 2;
  return Math.round(2 * R * Math.asin(Math.sqrt(s)));
}

/* Point a fraction f (0..1) along the great circle a→b. */
export function interpolate(a, b, f) {
  const toRad = d => d * Math.PI / 180, toDeg = r => r * 180 / Math.PI;
  const lat1 = toRad(a.lat), lng1 = toRad(a.lng);
  const lat2 = toRad(b.lat), lng2 = toRad(b.lng);
  const d = 2 * Math.asin(Math.sqrt(
    Math.sin((lat2 - lat1) / 2) ** 2 +
    Math.cos(lat1) * Math.cos(lat2) * Math.sin((lng2 - lng1) / 2) ** 2));
  if (!d) return { lat: a.lat, lng: a.lng };
  const A = Math.sin((1 - f) * d) / Math.sin(d);
  const B = Math.sin(f * d) / Math.sin(d);
  const x = A * Math.cos(lat1) * Math.cos(lng1) + B * Math.cos(lat2) * Math.cos(lng2);
  const y = A * Math.cos(lat1) * Math.sin(lng1) + B * Math.cos(lat2) * Math.sin(lng2);
  const z = A * Math.sin(lat1) + B * Math.sin(lat2);
  return { lat: toDeg(Math.atan2(z, Math.hypot(x, y))), lng: toDeg(Math.atan2(y, x)) };
}
