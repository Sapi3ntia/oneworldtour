/* ============================================================
   TV — live national television, honestly labelled.

   data/tv.json maps country code → channels. Every channel was
   verified ACTUALLY LIVE when the file was generated (yt-dlp for
   YouTube ids, curl + CORS check for HLS playlists) — same honesty
   rule as the stage scenes: a feed either streams for real or it
   isn't offered. A channel that rots at runtime removes itself.

   Channel kinds:
     yt  : a 24/7 YouTube live stream (specific video id) — mounted
           through yt.js so a rotted id fails into onError honestly.
     hls : an .m3u8 the broadcaster serves with CORS enabled — for
           state TV that YouTube removed (RT) or that never had an
           official channel there (KCTV). Played natively where the
           browser can (Safari), else through hls.js, lazy-loaded
           only when someone actually presses play.
   ============================================================ */

let tv = null, inflight = null;

async function load() {
  if (tv) return;
  try {
    tv = await fetch('data/tv.json', { cache: 'no-cache' }).then(r => r.ok ? r.json() : null);
  } catch { tv = null; }
  tv = tv || { countries: {} };
}

/* Channels for a country code ('CN', 'KP', …) — [] when none. */
export async function channelsFor(code) {
  if (!inflight) inflight = load();
  await inflight;
  if (!code) return [];
  return (tv.countries[code.toUpperCase()] || []).filter(c => c && c.name && (c.yt || c.url));
}

export async function tvGeneratedDate() {
  if (!inflight) inflight = load();
  await inflight;
  return tv.generated || null;
}

/* ---------------- HLS playback ---------------- */

let hlsLib = null;
function loadHlsLib() {
  if (window.Hls) return Promise.resolve();
  if (!hlsLib) {
    hlsLib = new Promise((resolve, reject) => {
      const s = document.createElement('script');
      s.src = 'https://cdn.jsdelivr.net/npm/hls.js@1/dist/hls.min.js';
      s.onload = resolve;
      s.onerror = () => { hlsLib = null; reject(new Error('hls.js failed to load')); };
      document.head.appendChild(s);
    });
  }
  return hlsLib;
}

/* mount an .m3u8 into host → { destroy() }. onError fires once if the
   stream can't play (offline, geo-blocked, CORS revoked) so the caller
   can drop the channel honestly instead of showing a dead player. */
export function mountHls(host, url, { onError } = {}) {
  const video = document.createElement('video');
  video.className = 'tv-video';
  video.playsInline = true;
  video.controls = true;
  video.autoplay = true;
  host.appendChild(video);

  let hls = null, dead = false, failed = false;
  const fail = () => {
    if (dead || failed) return;
    failed = true;
    cleanup();
    if (onError) { try { onError(); } catch {} }
  };
  const cleanup = () => {
    if (hls) { try { hls.destroy(); } catch {} hls = null; }
    try { video.pause(); } catch {}
    video.remove();
  };

  if (video.canPlayType('application/vnd.apple.mpegurl')) {
    video.src = url;
    video.addEventListener('error', fail);
    video.play().catch(() => { /* autoplay veto ≠ dead stream; controls remain */ });
  } else {
    loadHlsLib().then(() => {
      if (dead) return;
      hls = new window.Hls({ liveDurationInfinity: true });
      hls.on(window.Hls.Events.ERROR, (_ev, data) => { if (data?.fatal) fail(); });
      hls.loadSource(url);
      hls.attachMedia(video);
      video.play().catch(() => {});
    }).catch(fail);
  }

  return { destroy() { dead = true; cleanup(); } };
}
