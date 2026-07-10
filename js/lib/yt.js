/* ============================================================
   YT — YouTube embeds with an HONEST failure path.

   Curated ids rot (deleted / private / embed-disabled). A bare
   <iframe> then shows a broken frame forever. So every curated
   YouTube surface mounts through the IFrame Player API, which
   gives us onError → the caller drops to an honest empty state.

   mount(host, { videoId, start?, loop?, muted?, controls?, onReady?, onError? })
     → { destroy() }
   ============================================================ */

let apiReady = null;
export function loadAPI() {
  if (window.YT && window.YT.Player) return Promise.resolve();
  if (apiReady) return apiReady;
  apiReady = new Promise(resolve => {
    const prev = window.onYouTubeIframeAPIReady;
    window.onYouTubeIframeAPIReady = () => { try { prev && prev(); } catch {} resolve(); };
    const s = document.createElement('script');
    s.src = 'https://www.youtube.com/iframe_api';
    document.head.appendChild(s);
  });
  return apiReady;
}

export function mount(host, opts = {}) {
  const { videoId, start = 0, loop = false, muted = true,
          controls = 1, onReady, onError } = opts;
  let player = null, alive = true, fired = false;

  const fail = () => {
    if (!alive || fired) return;
    fired = true;
    if (player?.destroy) { try { player.destroy(); } catch {} }
    player = null;
    if (onError) { try { onError(); } catch {} }
  };

  if (!host || !videoId) { fail(); return { destroy() { alive = false; } }; }

  // The API replaces its target node — give it a throwaway child so we
  // own host's contents and never clobber sibling UI.
  host.innerHTML = '<div></div>';
  const slot = host.firstChild;

  loadAPI().then(() => {
    if (!alive) return;
    const playerVars = { autoplay: 1, rel: 0, playsinline: 1, modestbranding: 1, iv_load_policy: 3 };
    if (muted) playerVars.mute = 1;
    if (start) playerVars.start = start;
    // controls=0 = the chrome-free "looking out a window" frame.
    if (controls === 0) { playerVars.controls = 0; playerVars.disablekb = 1; }
    if (loop) { playerVars.loop = 1; playerVars.playlist = videoId; }   // single-video loop trick
    try {
      player = new YT.Player(slot, {
        videoId, playerVars,
        events: {
          onReady: e => {
            try {
              if (muted) e.target.mute();
              e.target.playVideo();
              const ifr = e.target.getIframe();
              if (ifr) {
                ifr.className = 'yt-frame';
                ifr.allow = 'autoplay; encrypted-media; picture-in-picture; fullscreen';
                ifr.allowFullscreen = true;
              }
            } catch {}
            if (onReady) { try { onReady(e); } catch {} }
          },
          // 2/5/100/101/150 = bad param / HTML5 / removed / private /
          // embed-disabled — every "rotted" case lands here.
          onError: fail,
        },
      });
    } catch { fail(); }
  });

  return {
    destroy() {
      alive = false;
      if (player?.destroy) { try { player.destroy(); } catch {} player = null; }
    },
  };
}
