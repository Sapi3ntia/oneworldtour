/* ============================================================
   API — Wikimedia (free, no key needed) + optional Unsplash upgrade
   Photos now pull from Wikipedia/Wikimedia Commons
   Set UNSPLASH_KEY if you want higher-quality arrival shots later
   ============================================================ */
const UNSPLASH_KEY = 'YOUR_UNSPLASH_ACCESS_KEY';   // optional
const BACKEND_URL  = 'http://localhost:8000';

const API = {

  /* ---- Arrival hero: Wikipedia page thumbnail (no key) ---- */
  async getArrivalPhoto(wikiSlug) {
    try {
      const r = await fetch(
        `https://en.wikipedia.org/w/api.php?action=query&prop=pageimages` +
        `&format=json&pithumbsize=1400` +
        `&titles=${encodeURIComponent(wikiSlug.replace(/_/g, ' '))}&origin=*`
      );
      const d = await r.json();
      const pages = Object.values(d.query.pages);
      const url = pages[0]?.thumbnail?.source;
      if (url) return url;
    } catch (e) { console.warn('[Wiki arrival]', e); }

    // Optional Unsplash upgrade
    if (UNSPLASH_KEY !== 'YOUR_UNSPLASH_ACCESS_KEY') {
      return this._unsplashSingle(wikiSlug.replace(/_/g, ' '));
    }
    return null;
  },

  /* ---- Gallery: Wikipedia media-list (no key) ---- */
  async getGalleryPhotos(wikiSlug, count = 4) {
    try {
      const r = await fetch(
        `https://en.wikipedia.org/api/rest_v1/page/media-list/${encodeURIComponent(wikiSlug)}`
      );
      const d = await r.json();

      const photos = (d.items || [])
        .filter(item =>
          item.type === 'image' &&
          item.srcset && item.srcset.length > 0 &&
          // Skip non-photo assets
          !item.title.match(/icon|logo|flag|map|seal|coat|arrow|commons|wiki|\.svg/i) &&
          item.title.match(/\.(jpg|jpeg|png|webp)/i)
        )
        .slice(0, count)
        .map(item => {
          // Take the largest srcset entry
          const src = item.srcset[item.srcset.length - 1]?.src;
          return src ? (src.startsWith('//') ? 'https:' + src : src) : null;
        })
        .filter(Boolean);

      if (photos.length > 0) return photos;
    } catch (e) { console.warn('[Wiki gallery]', e); }

    // Optional Unsplash upgrade
    if (UNSPLASH_KEY !== 'YOUR_UNSPLASH_ACCESS_KEY') {
      return this._unsplashGallery(wikiSlug.replace(/_/g, ' '), count);
    }
    return [];
  },

  /* ---- Wikipedia text summary (no key) ---- */
  async getWikiSummary(slug) {
    try {
      const r = await fetch(
        `https://en.wikipedia.org/api/rest_v1/page/summary/${encodeURIComponent(slug)}`
      );
      if (!r.ok) throw new Error(r.status);
      return (await r.json()).extract || null;
    } catch (e) { console.warn('[Wikipedia]', e); return null; }
  },

  /* ---- Live local weather + timezone (Open-Meteo, free, no key) ---- */
  async getWeather(lat, lng) {
    try {
      const r = await fetch(
        `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lng}` +
        `&current=temperature_2m,weather_code,is_day,wind_speed_10m&timezone=auto`
      );
      if (!r.ok) throw new Error(r.status);
      const d = await r.json();
      if (!d.current) return null;
      return {
        tempC:    Math.round(d.current.temperature_2m),
        code:     d.current.weather_code,
        isDay:    d.current.is_day,
        windKmh:  Math.round(d.current.wind_speed_10m),
        timezone: d.timezone,
        offsetSec: d.utc_offset_seconds
      };
    } catch (e) { console.warn('[Weather]', e); return null; }
  },

  /* ---- Live exchange rates (open.er-api.com, free, no key) ---- */
  async getRates(base = 'USD') {
    try {
      const r = await fetch(`https://open.er-api.com/v6/latest/${base}`);
      if (!r.ok) throw new Error(r.status);
      const d = await r.json();
      return d.result === 'success' ? d.rates : null;
    } catch (e) { console.warn('[Rates]', e); return null; }
  },

  /* ---- Local radio stations (Radio Browser, free, no key) ---- */
  async getStations(countryCode, limit = 14) {
    const servers = [
      'https://de1.api.radio-browser.info',
      'https://fi1.api.radio-browser.info',
      'https://nl1.api.radio-browser.info'
    ];
    for (const base of servers) {
      try {
        const r = await fetch(
          `${base}/json/stations/search?countrycode=${countryCode}` +
          `&limit=${limit * 3}&order=clickcount&reverse=true&hidebroken=true`
        );
        if (!r.ok) continue;
        const raw = await r.json();
        if (!Array.isArray(raw) || !raw.length) continue;

        // Dedupe by name, keep working stream URLs, cap the list.
        const seen = new Set();
        const list = [];
        for (const s of raw) {
          const name = (s.name || '').trim();
          const url  = s.url_resolved || s.url;
          if (!name || !url || seen.has(name.toLowerCase())) continue;
          seen.add(name.toLowerCase());
          list.push({
            name,
            url,
            codec:   s.codec || '',
            bitrate: s.bitrate || 0,
            tags:    (s.tags || '').split(',').filter(Boolean).slice(0, 3),
            favicon: s.favicon || ''
          });
          if (list.length >= limit) break;
        }
        if (list.length) return list;
      } catch (e) { console.warn('[Radio]', base, e); }
    }
    return [];
  },

  /* ---- Local news headlines (GDELT, free, no key, CORS-open) ---- */
  async getNews(place, country, limit = 6) {
    const q = encodeURIComponent(`"${place}" ${country || ''}`.trim());
    const url = `https://api.gdeltproject.org/api/v2/doc/doc?query=${q}` +
                `&mode=artlist&maxrecords=${limit * 3}&format=json&sort=datedesc`;
    try {
      const r = await fetch(url);
      if (!r.ok) throw new Error(r.status);
      const d = await r.json();
      const arts = Array.isArray(d.articles) ? d.articles : [];
      const seen = new Set();
      const out = [];
      for (const a of arts) {
        const title = (a.title || '').trim();
        if (!title || !a.url || seen.has(title.toLowerCase())) continue;
        seen.add(title.toLowerCase());
        out.push({ title, url: a.url, domain: a.domain || '', seendate: a.seendate || '' });
        if (out.length >= limit) break;
      }
      return out;
    } catch (e) { console.warn('[News]', e); return []; }
  },

  /* ---- Claude guide Q&A via backend proxy ---- */
  async askGuide(locationName, question, context) {
    try {
      const r = await fetch(`${BACKEND_URL}/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ locationName, question, context })
      });
      if (!r.ok) throw new Error(r.status);
      return (await r.json()).answer || 'No answer available.';
    } catch (e) {
      console.warn('[Guide]', e);
      return 'Guide unavailable — make sure the backend is running on port 8000.';
    }
  },

  /* ---- Private: Unsplash fallbacks (used only if key is set) ---- */
  async _unsplashSingle(query) {
    try {
      const r = await fetch(
        `https://api.unsplash.com/photos/random?query=${encodeURIComponent(query)}&orientation=landscape&client_id=${UNSPLASH_KEY}`
      );
      return (await r.json()).urls?.regular || null;
    } catch (e) { return null; }
  },

  async _unsplashGallery(query, count) {
    try {
      const r = await fetch(
        `https://api.unsplash.com/photos/random?query=${encodeURIComponent(query)}&count=${count}&orientation=landscape&client_id=${UNSPLASH_KEY}`
      );
      const d = await r.json();
      return Array.isArray(d) ? d.map(p => p.urls?.regular).filter(Boolean) : [];
    } catch (e) { return []; }
  }
};
