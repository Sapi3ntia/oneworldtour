/* ============================================================
   DESTINATIONS — THE shared data loader for every page.

   Reads data/index.json, fetches every enabled region in PARALLEL
   (skipping any that fail, never letting one bad file break the
   page), and returns ONE flat array of location objects.

   Cross-page cache: the merged result (plus the Windy webcam index)
   is kept in sessionStorage, so hopping map → location → window
   costs zero data refetches within a tab session. The cache expires
   after CACHE_TTL_MS, and any `?bust` query param skips it — the
   escape hatch when you're editing the data files.

   Used by ALL pages (map, location, window, guess, passport) — don't
   hand-roll region loading anywhere else.
   ============================================================ */
const Destinations = (() => {
  const CACHE_KEY    = 'owt_data_cache_v1';
  const CACHE_TTL_MS = 10 * 60 * 1000;   // 10 min — fresh enough while editing data

  let locations = null;   // in-memory for this page's lifetime
  let regionList = null;  // the enabled regions that actually loaded
  let windy = null;       // windy.json sidecar index
  let inflight = null;    // dedupe concurrent loadAll() calls

  const bust = () => new URLSearchParams(location.search).has('bust');

  function readCache() {
    if (bust()) return null;
    try {
      const raw = sessionStorage.getItem(CACHE_KEY);
      if (!raw) return null;
      const c = JSON.parse(raw);
      if (!c.at || Date.now() - c.at > CACHE_TTL_MS) return null;
      return c;
    } catch (e) { return null; }
  }

  function writeCache() {
    try {
      sessionStorage.setItem(CACHE_KEY, JSON.stringify(
        { at: Date.now(), locations, regions: regionList, windy }));
    } catch (e) { /* quota — run uncached, no harm */ }
  }

  async function fetchAll() {
    const index = await fetch('data/index.json').then(r => r.json());
    const enabled = index.regions.filter(r => r.enabled);

    // Regions + the Windy index, all in one parallel burst.
    const [settled, windyIdx] = await Promise.all([
      Promise.allSettled(enabled.map(async region => {
        const json = await fetch(region.file).then(r => {
          if (!r.ok) throw new Error(`${region.file} → ${r.status}`);
          return r.json();
        });
        return { region, json };
      })),
      fetch('data/windy.json').then(r => r.ok ? r.json() : {}).catch(() => ({}))
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
        region_flag:  region.flag      || '🌍',
        collection:   region.collection || null,
        accent:       region.accent     || null,
        country:      loc.country      || region.country || region.name,
        country_flag: loc.country_flag || region.flag
      }));
    });

    locations = all;
    regionList = regions;
    windy = windyIdx || {};
    writeCache();
  }

  async function load() {
    if (locations) return;
    const cached = readCache();
    if (cached && Array.isArray(cached.locations) && cached.locations.length) {
      locations = cached.locations;
      regionList = cached.regions || [];
      windy = cached.windy || {};
      return;
    }
    await fetchAll();
  }

  /* The one entry point: resolves to the flat location array, and (when
     webcam.js is on the page) hands the Windy index to Webcam as a side
     effect so window/live-cam resolution just works everywhere. */
  async function loadAll() {
    if (!inflight) inflight = load();
    await inflight;
    if (window.Webcam && Webcam.setWindyIndex) Webcam.setWindyIndex(windy);
    return locations;
  }

  /* The enabled regions that loaded — valid after loadAll() resolves. */
  function regions() { return regionList || []; }

  /* The raw Windy index — valid after loadAll() resolves. */
  function windyIndex() { return windy || {}; }

  return { loadAll, regions, windyIndex };
})();
