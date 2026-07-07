/* ============================================================
   WEBCAM — resolve a location's window view into an embeddable URL.
   Shared by the location page (Live View) and the Virtual Window.

   Two tiers, kept deliberately distinct so the UI can always say
   WHICH ONE IS WHICH (see window.js badges + map.js marker tips):

     • LIVE   — `webcam` field: a real public webcam, streaming now.
                Accepts a YouTube id string, or { yt } / { channel } / { poster }.
     • AMBIENT — `ambient` field: a curated *recorded* "out the window" video,
                seeked to a good moment and looped. Not live, and never
                presented as live. This is how virtualvacation.us/window
                reaches hundreds of places — we adopt the technique but
                label it honestly. Accepts 'id', 'id?start=SS', or { yt, start }.

   `OPTS` keeps the least YouTube chrome we can: rel=0 (no foreign related
   videos), modestbranding (smaller logo), iv_load_policy=3 (no annotations).
   We can't fully remove YouTube's own links — a platform limit, noted in
   DEVNOTES — but this minimises the "redirect" surface.
   ============================================================ */
const Webcam = (() => {
  const OPTS = 'autoplay=1&mute=1&rel=0&playsinline=1&modestbranding=1&iv_load_policy=3';

  /* ---- Windy public webcams (keyless embeds) ------------------------------
     A build-time lookup (tools/fetch_windy.py) bakes the nearest good cam per
     place into data/windy.json: { <id>: { window, live?, title, km } }. We
     embed Windy's PUBLIC player (no API key in the client). Two tiers:
       • live      — a real continuous stream (the cam's /live player), when one
                     exists. Same tier as a curated YouTube live cam.
       • timelapse — the cam's /day player: its latest frame + a timelapse of the
                     day. A real, CURRENT look out the window — not a 24/7 stream
                     and not a fake recorded loop, so it gets its own honest kind.
     This is what scales 🪟 Window + 🔴 Live from a couple-dozen curated places to
     hundreds. Windy branding lives in the embed itself (ToS attribution). */
  let WINDY = {};
  function setWindyIndex(obj) { WINDY = obj || {}; }
  const windyEmbed = (id, type) =>
    `https://webcams.windy.com/webcams/public/embed/player/${id}/${type}`;

  /* LIVE only. Returns { src, video?, poster? } or null. */
  function resolve(w) {
    if (!w) return null;
    if (typeof w === 'string') return { video: w, src: `https://www.youtube.com/embed/${w}?${OPTS}` };
    if (w.channel) return { src: `https://www.youtube.com/embed/live_stream?channel=${w.channel}&autoplay=1&mute=1&modestbranding=1`, poster: w.poster };
    if (w.yt) return { video: w.yt, src: `https://www.youtube.com/embed/${w.yt}?${OPTS}`, poster: w.poster };
    return null;
  }

  /* AMBIENT only. Returns { src, video, start } or null.
     The loop trick for a single video is loop=1 + playlist=<same id>. */
  function resolveAmbient(a) {
    if (!a) return null;
    let id, start = 0;
    if (typeof a === 'string') {
      const m = a.match(/^([A-Za-z0-9_-]{11})(?:[?&].*?start=(\d+))?/);
      if (!m) return null;
      id = m[1];
      start = parseInt(m[2], 10) || 0;
    } else if (a.yt) {
      id = a.yt;
      start = parseInt(a.start, 10) || 0;
    } else {
      return null;
    }
    const src = `https://www.youtube.com/embed/${id}?${OPTS}&start=${start}&loop=1&playlist=${id}`;
    return { video: id, src, start };
  }

  /* LIVE tier only: curated YouTube live cam → Windy live stream.
     Returns { src, kind:'live', source, title? } or null. */
  function liveFor(loc) {
    if (!loc) return null;
    const yt = resolve(loc.webcam);
    if (yt) return { ...yt, kind: 'live', source: 'youtube' };
    const w = WINDY[loc.id];
    if (w && w.live) return { src: windyEmbed(w.live, 'live'), kind: 'live', source: 'windy', title: w.title };
    return null;
  }

  /* WINDOW tier only: curated recorded ambient loop → Windy /day timelapse.
     Returns { src, kind:'ambient'|'timelapse', source, title? } or null. */
  function windowFor(loc) {
    if (!loc) return null;
    const amb = resolveAmbient(loc.ambient);
    if (amb) return { ...amb, kind: 'ambient', source: 'youtube' };
    const w = WINDY[loc.id];
    if (w && w.window) return { src: windyEmbed(w.window, 'day'), kind: 'timelapse', source: 'windy', title: w.title };
    return null;
  }

  /* The single best window view, whichever tier it has — LIVE always outranks
     the recorded/timelapse window. Used by the map badges + the Window feature. */
  function forWindow(loc) {
    return liveFor(loc) || windowFor(loc);
  }

  /* Windy-ONLY resolvers — the honest fallback when a curated YouTube surface
     (a live cam or a recorded ambient window) rots. Unlike liveFor/windowFor
     these skip the curated id entirely and resolve straight to Windy, whose
     own player self-handles an offline cam — so they can never re-introduce a
     broken frame. Return the same { src, kind, source, title } shape or null. */
  function windyLiveFor(loc) {
    const w = loc && WINDY[loc.id];
    return w && w.live ? { src: windyEmbed(w.live, 'live'), kind: 'live', source: 'windy', title: w.title } : null;
  }
  function windyWindowFor(loc) {
    const w = loc && WINDY[loc.id];
    return w && w.window ? { src: windyEmbed(w.window, 'day'), kind: 'timelapse', source: 'windy', title: w.title } : null;
  }

  return { resolve, resolveAmbient, forWindow, liveFor, windowFor,
           windyLiveFor, windyWindowFor, setWindyIndex };
})();

window.Webcam = Webcam;
