/* ============================================================
   DATA — THE shared loader for every page.

   Reads data/index.json, fetches every enabled region in parallel
   (one bad file never breaks the page), merges in one sidecar:

     • data/media.json — yt-dlp enrichment sidecar (auto-found walking
       tours + live cams, vetted at build time by tools/enrich_media.py)

   and returns ONE flat array of place objects. Merge policy:
   hand-curated fields in the region JSON always win; media.json only
   fills gaps. (data/windy.json is no longer loaded — Windy's embed
   player doesn't actually autoplay live video; see js/lib/media.js.)

   Cross-page cache in sessionStorage; `?bust` skips it while editing.
   ============================================================ */

const CACHE_KEY = 'owt_data_cache_v5';   // v5: wild region + tv.json era
const CACHE_TTL_MS = 10 * 60 * 1000;

/* Always revalidate data files with the server (cheap 304s). Without
   this the browser's heuristic HTTP cache can keep serving a stale
   media.json for many minutes after it changed on disk — and each
   load re-stamps the sessionStorage cache, keeping purged picks
   (e.g. a wrong-city walk) alive in an open tab indefinitely. */
const FRESH = { cache: 'no-cache' };

let places = null, regionList = null, media = null, inflight = null;

const bust = () => new URLSearchParams(location.search).has('bust');

function readCache() {
  if (bust()) return null;
  try {
    const c = JSON.parse(sessionStorage.getItem(CACHE_KEY));
    if (!c?.at || Date.now() - c.at > CACHE_TTL_MS) return null;
    return c;
  } catch { return null; }
}
function writeCache() {
  try {
    sessionStorage.setItem(CACHE_KEY, JSON.stringify(
      { at: Date.now(), places, regions: regionList, media }));
  } catch { /* quota — run uncached */ }
}

async function fetchAll() {
  const index = await fetch('data/index.json', FRESH).then(r => r.json());
  const enabled = index.regions.filter(r => r.enabled);

  const [settled, mediaIdx] = await Promise.all([
    Promise.allSettled(enabled.map(async region => {
      const json = await fetch(region.file, FRESH).then(r => {
        if (!r.ok) throw new Error(`${region.file} → ${r.status}`);
        return r.json();
      });
      return { region, json };
    })),
    fetch('data/media.json', FRESH).then(r => r.ok ? r.json() : null).catch(() => null),
  ]);

  const all = [], regions = [];
  settled.forEach(s => {
    if (s.status !== 'fulfilled') { console.warn('[region skipped]', s.reason); return; }
    const { region, json } = s.value;
    regions.push(region);
    json.locations.forEach(loc => all.push({
      ...loc,
      region_id:    region.id,
      region_name:  region.name,
      region_flag:  region.flag || '🌍',
      collection:   region.collection || null,
      accent:       region.accent || null,
      country:      loc.country || region.country || region.name,
      country_flag: loc.country_flag || region.flag,
    }));
  });

  places = all;
  regionList = regions;
  media = (mediaIdx && mediaIdx.places) || {};
  writeCache();
}

async function load() {
  if (places) return;
  const cached = readCache();
  if (cached?.places?.length) {
    places = cached.places;
    regionList = cached.regions || [];
    media = cached.media || {};
    return;
  }
  await fetchAll();
}

/* The one entry point — resolves to the flat place array. */
export async function loadAll() {
  if (!inflight) inflight = load();
  await inflight;
  return places;
}

export function regions() { return regionList || []; }
export function mediaIndex() { return media || {}; }

export async function byId(id) {
  const all = await loadAll();
  return all.find(p => p.id === id) || null;
}

/* ---- Search: simple ranked substring match over name/country/
   monuments/highlights. Good enough at 345 records, zero deps. ---- */
export function search(all, q, limit = 8) {
  const s = q.trim().toLowerCase();
  if (!s) return [];
  const scored = [];
  for (const p of all) {
    const name = p.name.toLowerCase();
    const country = (p.country || '').toLowerCase();
    let score = -1, label = null;
    if (name.startsWith(s)) score = 100;
    else if (name.includes(s)) score = 80;
    else if (country.startsWith(s)) score = 60;
    else if (country.includes(s)) score = 45;
    else {
      const m = (p.monuments || []).find(m => m.name.toLowerCase().includes(s));
      const h = m ? null : (p.highlights || []).find(h => h.name.toLowerCase().includes(s));
      if (m) { score = 55; label = m.name; }
      else if (h) { score = 30; label = h.name; }
    }
    if (score >= 0) scored.push({ p, score, label });
  }
  scored.sort((a, b) => b.score - a.score || (b.p.tag === 'famous') - (a.p.tag === 'famous'));
  return scored.slice(0, limit);
}
