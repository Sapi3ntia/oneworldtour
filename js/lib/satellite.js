/* ============================================================
   SATELLITE — the sky over a place right now, seen from orbit.

   WHY THIS EXISTS
     1,018 of the 1,126 places have no window cam, and 82 have
     nothing on the stage at all. Some of them never will: nobody is
     going to point a webcam at Bikini Atoll, Kiritimati or Rennell
     Island, and the honest empty pane says so four times over on
     those pages.

     But something IS looking at every one of them, every ten
     minutes, right now: the geostationary weather satellites. Four
     of them see the whole inhabited world between them, they are
     free, keyless and CORS-open, and their newest scan is minutes
     old. That is a real live view of a real place — the clouds over
     your atoll this morning, the city lights of Cairo before dawn —
     and it is available for every one of the 1,126.

   WHAT THIS IS NOT
     It is NOT a window, and it must never be offered as one. The
     owner rule in media.js stands: no still, no loop and no
     timelapse ever stands in for a live camera. So this seat wears
     its own badge (🛰️ Satellite), never the 🪟 one; it never carries
     the red live dot; it is not in sceneFlags, so it cannot leak
     into the live rails, the map badges or the window page; and the
     pane says out loud that there is no window cam here. It fills
     dead space with something true, which is the opposite of a
     stand-in.

   THE FOUR EYES (sub-satellite longitude in brackets)
     Himawari-9   [140.7°E]  JMA tiles, true colour by day, clean
                             infrared by night. Asia · Australia ·
                             the western Pacific.
     GOES-West    [137.0°W]  NASA GIBS, GeoColor — city lights at
                             night. The eastern Pacific · Hawai'i ·
                             Polynesia · western Americas.
     GOES-East    [75.2°W]   NASA GIBS, GeoColor. The Americas ·
                             the Atlantic.
     Meteosat MTG [0.0°]     EUMETSAT, geocolour. Europe · Africa ·
                             the Middle East.

     A place is handed to whichever eye is closest in longitude —
     the boundaries below are the midpoints between neighbours, so
     Sāmoa (172°W) goes to GOES-West and Fiji (178°E) to Himawari
     even though they are neighbours, because that really is which
     satellite has the better look at each.

   TWO REQUEST SHAPES, ONE GEOMETRY
     GIBS and JMA serve Web-Mercator XYZ tiles, so we mosaic a 3×3
     block centred on the place. EUMETSAT is a WMS: it renders any
     EPSG:3857 bounding box we ask for, so it gets the same block as
     ONE image instead of nine requests to a government GeoServer.
     Either way the geometry is computed identically and the place's
     exact pixel lands in the centre of the frame.
   ============================================================ */
import { el } from './dom.js';

const TILE = 256;                       // Web Mercator tile, px
const R = 20037508.342789244;           // EPSG:3857 half-extent, m
const REFRESH_MS = 5 * 60 * 1000;       // sources update every 10 min

/* ---------------- tile math ---------------- */
const rad = d => d * Math.PI / 180;
const tileX = (lng, z) => (lng + 180) / 360 * 2 ** z;
const tileY = (lat, z) => {
  const s = Math.sin(rad(lat));
  return (0.5 - Math.log((1 + s) / (1 - s)) / (4 * Math.PI)) * 2 ** z;
};

/* The top-left index of an n-wide block that keeps `f` centred:
   odd n straddles the tile f is in, even n straddles its boundary.
   Either way the place ends up at least half a tile from every edge,
   which is what lets the mosaic be scaled to cover any frame. */
const originIndex = (f, n) =>
  (n % 2 ? Math.floor(f) - (n - 1) / 2 : Math.round(f) - n / 2);

const wrapX = (x, z) => ((x % 2 ** z) + 2 ** z) % 2 ** z;   // across ±180°

/* ---------------- is the sun up there? ----------------
   Low-precision NOAA solar position — good to a fraction of a
   degree, which is all "is it light enough for a true-colour image"
   needs. Civil twilight (-6°) is the cutoff: below it the visible
   channels are black and the infrared ones are the honest picture. */
export function sunAltitude(lat, lng, when = new Date()) {
  const d = when.getTime() / 86400000 - 10957.5;      // days since J2000.0
  const g = rad(357.529 + 0.98560028 * d);            // mean anomaly
  const q = 280.459 + 0.98564736 * d;                 // mean longitude
  const L = rad(q + 1.915 * Math.sin(g) + 0.020 * Math.sin(2 * g));
  const e = rad(23.439 - 0.00000036 * d);             // obliquity
  const dec = Math.asin(Math.sin(e) * Math.sin(L));   // declination
  const ra = Math.atan2(Math.cos(e) * Math.sin(L), Math.cos(L));
  const gmst = (18.697374558 + 24.06570982441908 * d) % 24;
  const ha = rad(((gmst + lng / 15) % 24) * 15) - ra; // hour angle
  return Math.asin(Math.sin(rad(lat)) * Math.sin(dec) +
                   Math.cos(rad(lat)) * Math.cos(dec) * Math.cos(ha)) / Math.PI * 180;
}

/* ---------------- the four eyes ---------------- */

/* JMA publishes the list of scans it has; the last one is the newest,
   typically two to four minutes old. Cached because every pane on a
   page would otherwise ask again. */
let jmaAt = { time: 0, base: null };
async function jmaBase() {
  if (jmaAt.base && Date.now() - jmaAt.time < REFRESH_MS) return jmaAt.base;
  try {
    const r = await fetch('https://www.jma.go.jp/bosai/himawari/data/satimg/targetTimes_fd.json',
                          { cache: 'no-store' });
    const list = await r.json();
    const base = list[list.length - 1].basetime;
    if (/^\d{14}$/.test(base)) { jmaAt = { time: Date.now(), base }; return base; }
  } catch { /* fall through to the clock */ }
  // no list? the naming is UTC on a ten-minute grid — guess conservatively
  const t = new Date(Date.now() - 20 * 60 * 1000);
  const p = n => String(n).padStart(2, '0');
  return `${t.getUTCFullYear()}${p(t.getUTCMonth() + 1)}${p(t.getUTCDate())}` +
         `${p(t.getUTCHours())}${p(Math.floor(t.getUTCMinutes() / 10) * 10)}00`;
}

const gibs = (layer, level) => (z, x, y, ctx) =>
  `https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/${layer}/default/default/` +
  `GoogleMapsCompatible_Level${level}/${z}/${y}/${x}.png?_=${ctx.stamp}`;

const SOURCES = {
  himawari: {
    name: 'Himawari-9', credit: 'JMA', kind: 'tiles', zoom: 5,
    band: day => (day ? 'true colour' : 'infrared'),
    async context({ day }) { return { base: await jmaBase(), day }; },
    stampText: ctx => {
      const [, Y, M, D, h, m] = ctx.base.match(/(\d{4})(\d\d)(\d\d)(\d\d)(\d\d)/);
      const at = Date.UTC(+Y, +M - 1, +D, +h, +m);
      const mins = Math.max(0, Math.round((Date.now() - at) / 60000));
      return `${h}:${m} UTC · ${mins} min ago`;
    },
    url: (z, x, y, ctx) =>
      `https://www.jma.go.jp/bosai/himawari/data/satimg/${ctx.base}/fd/${ctx.base}/` +
      `${ctx.day ? 'REP/ETC' : 'B13/TBB'}/${z}/${x}/${y}.jpg`,
  },
  'goes-west': {
    name: 'GOES-West', credit: 'NOAA · NASA GIBS', kind: 'tiles', zoom: 6,
    band: () => 'GeoColor',
    url: gibs('GOES-West_ABI_GeoColor', 7),
  },
  'goes-east': {
    name: 'GOES-East', credit: 'NOAA · NASA GIBS', kind: 'tiles', zoom: 6,
    band: () => 'GeoColor',
    url: gibs('GOES-East_ABI_GeoColor', 7),
  },
  meteosat: {
    name: 'Meteosat', credit: 'EUMETSAT', kind: 'wms', zoom: 6,
    band: () => 'geocolour',
    url: (bbox, w, h, ctx) =>
      'https://view.eumetsat.int/geoserver/ows?service=WMS&request=GetMap&version=1.3.0' +
      '&layers=mtg_fd:rgb_geocolour&styles=&format=image/jpeg&crs=EPSG:3857' +
      `&bbox=${bbox.join(',')}&width=${w}&height=${h}&_=${ctx.stamp}`,
  },
};

/* Whichever eye has the best look at this longitude. The cuts are the
   midpoints between neighbouring sub-satellite points. */
export function sourceFor(lng) {
  const L = ((lng + 180) % 360 + 360) % 360 - 180;
  if (L >= 70.35 || L <= -178.15) return SOURCES.himawari;
  if (L <= -106.1) return SOURCES['goes-west'];
  if (L <= -37.6) return SOURCES['goes-east'];
  return SOURCES.meteosat;
}

/* What the caption will say, without mounting anything — handy for
   deciding whether a pane is worth offering at all. */
export function satelliteFor(lat, lng, when = new Date()) {
  if (!Number.isFinite(lat) || !Number.isFinite(lng)) return null;
  const src = sourceFor(lng);
  const day = sunAltitude(lat, lng, when) > -6;
  return { id: src.name, name: src.name, credit: src.credit, band: src.band(day), day };
}

/* ---------------- the pane ----------------
   `frame` is any positioned element (the .frame contract). Returns a
   handle with destroy(), same as yt.mount, so a pane can swap this
   out the way it swaps out a video. */
export function mountSatellite(frame, { lat, lng, cols = 3, rows = 3 } = {}) {
  const src = sourceFor(lng);
  const z = src.zoom;
  const day = sunAltitude(lat, lng) > -6;

  const stage = el('div', { class: 'sat' });
  const stamp = el('span', { class: 'sat-stamp' }, 'loading the latest scan…');
  const caption = el('div', { class: 'sat-cap' },
    el('span', { class: 'sat-src' }, `🛰️ ${src.name} · ${src.band(day)}`), stamp);

  frame.append(stage, caption);
  stage.append(el('div', { class: 'sat-pin' }));

  /* geometry: a cols×rows block of tiles with the place dead centre */
  const fx = tileX(lng, z), fy = tileY(lat, z);
  const x0 = originIndex(fx, cols), y0 = originIndex(fy, rows);
  const W = cols * TILE, H = rows * TILE;
  const px = (fx - x0) * TILE, py = (fy - y0) * TILE;   // the place, in mosaic px


  /* Scale so the mosaic covers the frame in every direction from the
     place, then offset so the place sits at the frame's centre. The
     frame resizes when a pane is enlarged, so recompute on resize. */
  const place = () => {
    const w = frame.clientWidth, h = frame.clientHeight;
    if (!w || !h) return;
    const s = Math.max(w / 2 / px, w / 2 / (W - px), h / 2 / py, h / 2 / (H - py));
    const t = `translate(${w / 2 - px * s}px, ${h / 2 - py * s}px) scale(${s})`;
    for (const m of stage.querySelectorAll('.sat-mosaic')) m.style.transform = t;
  };

  let ro = null;
  if (typeof ResizeObserver === 'function') {
    ro = new ResizeObserver(place);
    ro.observe(frame);
  } else {
    addEventListener('resize', place);
  }

  const bbox3857 = (x, y, n) => {
    const s = 2 * R / 2 ** z;
    return [-R + x * s, R - (y + n) * s, -R + (x + n) * s, R - y * s];
  };

  let alive = true, timer = null;

  async function draw() {
    if (!alive) return;
    const ctx = { stamp: Date.now(), day,
                  ...(src.context ? await src.context({ day }) : {}) };
    if (!alive) return;

    /* Double-buffered: the new scan is built underneath, and the one
       already on screen is only removed once every tile has settled.
       Otherwise every refresh would blink the pane black for a second. */
    const fresh = el('div', { class: 'sat-mosaic',
      style: `width:${W}px;height:${H}px` });
    const waits = [];

    const tile = (attrs) => {
      const img = el('img', { class: 'sat-tile', alt: '', ...attrs });
      waits.push(new Promise(done => {
        img.addEventListener('load', done, { once: true });
        // off the satellite's disk, or a scan that hasn't landed yet —
        // hide that tile rather than show a broken-image glyph
        img.addEventListener('error', () => { img.style.visibility = 'hidden'; done(); },
                             { once: true });
      }));
      fresh.append(img);
    };

    if (src.kind === 'wms') {
      tile({ src: src.url(bbox3857(x0, y0, cols), W, H, ctx),
             style: `left:0;top:0;width:${W}px;height:${H}px` });
    } else {
      for (let r = 0; r < rows; r++) {
        for (let c = 0; c < cols; c++) {
          const y = y0 + r;
          if (y < 0 || y >= 2 ** z) continue;              // past the poles
          tile({ src: src.url(z, wrapX(x0 + c, z), y, ctx),
                 style: `left:${c * TILE}px;top:${r * TILE}px` });
        }
      }
    }

    const old = [...stage.querySelectorAll('.sat-mosaic')];
    stage.prepend(fresh);
    place();
    stamp.textContent = src.stampText
      ? `${src.stampText(ctx)} · ${src.credit}`
      : `latest scan · ${src.credit}`;

    await Promise.all(waits);
    if (!alive) { fresh.remove(); return; }
    for (const m of old) m.remove();
  }

  draw();
  setTimeout(place, 0);      // frames are usually still unsized at mount
  /* Only keep asking while the tab is actually being looked at. */
  const tick = () => { if (document.visibilityState === 'visible') draw(); };
  timer = setInterval(tick, REFRESH_MS);
  document.addEventListener('visibilitychange', tick);

  return {
    destroy() {
      alive = false;
      clearInterval(timer);
      document.removeEventListener('visibilitychange', tick);
      if (ro) ro.disconnect(); else removeEventListener('resize', place);
      stage.remove(); caption.remove();
    },
  };
}
