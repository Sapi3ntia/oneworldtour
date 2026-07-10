/* ============================================================
   API — every external service call. All free, keyless, CORS-open.
   Each function degrades to null/[] — callers show honest empty
   states, never spinners that spin forever.
   ============================================================ */
const BACKEND_URL = 'http://localhost:8000';

/* ---- Hero photo: Wikipedia page thumbnail ---- */
export async function arrivalPhoto(wikiSlug, size = 1400) {
  if (!wikiSlug) return null;
  try {
    const r = await fetch(
      `https://en.wikipedia.org/w/api.php?action=query&prop=pageimages` +
      `&format=json&pithumbsize=${size}` +
      `&titles=${encodeURIComponent(wikiSlug.replace(/_/g, ' '))}&origin=*`);
    const d = await r.json();
    return Object.values(d.query.pages)[0]?.thumbnail?.source || null;
  } catch { return null; }
}

/* ---- Gallery: Wikipedia media-list ---- */
export async function galleryPhotos(wikiSlug, count = 4) {
  if (!wikiSlug) return [];
  try {
    const r = await fetch(
      `https://en.wikipedia.org/api/rest_v1/page/media-list/${encodeURIComponent(wikiSlug)}`);
    const d = await r.json();
    return (d.items || [])
      .filter(it => it.type === 'image' && it.srcset?.length &&
        !it.title.match(/icon|logo|flag|map|seal|coat|arrow|commons|wiki|\.svg/i) &&
        it.title.match(/\.(jpg|jpeg|png|webp)/i))
      .slice(0, count)
      .map(it => {
        const src = it.srcset[it.srcset.length - 1]?.src;
        return src ? (src.startsWith('//') ? 'https:' + src : src) : null;
      })
      .filter(Boolean);
  } catch { return []; }
}

/* ---- Wikipedia text summary ---- */
export async function wikiSummary(slug) {
  if (!slug) return null;
  try {
    const r = await fetch(
      `https://en.wikipedia.org/api/rest_v1/page/summary/${encodeURIComponent(slug)}`);
    if (!r.ok) throw new Error(r.status);
    return (await r.json()).extract || null;
  } catch { return null; }
}

/* ---- Live weather + timezone (Open-Meteo) ---- */
export async function weather(lat, lng) {
  try {
    const r = await fetch(
      `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lng}` +
      `&current=temperature_2m,weather_code,is_day,wind_speed_10m&timezone=auto`);
    if (!r.ok) throw new Error(r.status);
    const d = await r.json();
    if (!d.current) return null;
    return {
      tempC: Math.round(d.current.temperature_2m),
      code: d.current.weather_code,
      isDay: d.current.is_day,
      windKmh: Math.round(d.current.wind_speed_10m),
      timezone: d.timezone,
      offsetSec: d.utc_offset_seconds,
    };
  } catch { return null; }
}

/* ---- Exchange rates (open.er-api.com) ---- */
export async function rates(base = 'USD') {
  try {
    const r = await fetch(`https://open.er-api.com/v6/latest/${base}`);
    if (!r.ok) throw new Error(r.status);
    const d = await r.json();
    return d.result === 'success' ? d.rates : null;
  } catch { return null; }
}

/* ---- Local radio stations (Radio Browser) ---- */
export async function stations(countryCode, limit = 14) {
  const servers = [
    'https://de1.api.radio-browser.info',
    'https://fi1.api.radio-browser.info',
    'https://nl1.api.radio-browser.info',
  ];
  for (const base of servers) {
    try {
      const r = await fetch(
        `${base}/json/stations/search?countrycode=${countryCode}` +
        `&limit=${limit * 3}&order=clickcount&reverse=true&hidebroken=true`);
      if (!r.ok) continue;
      const raw = await r.json();
      if (!Array.isArray(raw) || !raw.length) continue;
      const seen = new Set(), list = [];
      for (const s of raw) {
        const name = (s.name || '').trim();
        const url = s.url_resolved || s.url;
        if (!name || !url || seen.has(name.toLowerCase())) continue;
        seen.add(name.toLowerCase());
        list.push({
          name, url,
          codec: s.codec || '', bitrate: s.bitrate || 0,
          tags: (s.tags || '').split(',').filter(Boolean).slice(0, 3),
          favicon: s.favicon || '',
        });
        if (list.length >= limit) break;
      }
      if (list.length) return list;
    } catch { /* try next mirror */ }
  }
  return [];
}

/* ---- Headlines (GDELT — rate-limits hard; callers hide on []) ---- */
export async function news(place, country, limit = 6) {
  const q = encodeURIComponent(`"${place}" ${country || ''}`.trim());
  try {
    const r = await fetch(
      `https://api.gdeltproject.org/api/v2/doc/doc?query=${q}` +
      `&mode=artlist&maxrecords=${limit * 3}&format=json&sort=datedesc`);
    if (!r.ok) throw new Error(r.status);
    const d = await r.json();
    const seen = new Set(), out = [];
    for (const a of (Array.isArray(d.articles) ? d.articles : [])) {
      const title = (a.title || '').trim();
      if (!title || !a.url || seen.has(title.toLowerCase())) continue;
      seen.add(title.toLowerCase());
      out.push({ title, url: a.url, domain: a.domain || '', seendate: a.seendate || '' });
      if (out.length >= limit) break;
    }
    return out;
  } catch { return []; }
}

/* ---- Claude guide Q&A via optional backend proxy ---- */
export async function askGuide(locationName, question, context) {
  try {
    const r = await fetch(`${BACKEND_URL}/ask`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ locationName, question, context }),
    });
    if (!r.ok) throw new Error(r.status);
    return (await r.json()).answer || 'No answer available.';
  } catch {
    return 'Guide unavailable — make sure the backend is running on port 8000.';
  }
}
