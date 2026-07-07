/* ============================================================
   YTEMBED — mount a YouTube embed through the IFrame Player API so we
   get an onError signal, then fall back HONESTLY when a curated id has
   rotted (deleted / private / embedding disabled).

   Why this exists (HANDOFF issue I-7): a curated cam / ambient / walk /
   monument id can rot over time. A bare <iframe> then shows a broken
   frame forever — a silent lie by omission. walkthrough.js already
   guards its walk via the IFrame API's onError → Ken Burns; this packages
   the same guard so the location page (hero + More Views + monuments) and
   the Virtual Window can share one honest fallback path.

   Named YTEmbed on purpose — NOT `YT`, which is the global object the
   YouTube IFrame API itself installs. Colliding with it would break the API.

   YTEmbed.mount(host, { videoId, start?, loop?, muted?, frameClass?, onReady?, onError? })
     → { destroy() }. Replaces `host`'s contents with a YT.Player. On a
       deleted / private / non-embeddable video it fires onError() exactly
       once, so the caller can drop to the place's Windy window or an honest
       empty state. A non-YouTube surface (Windy) is self-healing and never
       needs this — callers mount those as a plain iframe.
   ============================================================ */
const YTEmbed = (() => {
  /* Lazy-load the IFrame Player API exactly once, chaining any existing
     onYouTubeIframeAPIReady (walkthrough.js) so we never stomp it. */
  let apiReady = null;
  function loadAPI() {
    if (window.YT && window.YT.Player) return Promise.resolve();
    if (apiReady) return apiReady;
    apiReady = new Promise(resolve => {
      const prev = window.onYouTubeIframeAPIReady;
      window.onYouTubeIframeAPIReady = () => { try { prev && prev(); } catch (_) {} resolve(); };
      const s = document.createElement('script');
      s.src = 'https://www.youtube.com/iframe_api';
      document.head.appendChild(s);
    });
    return apiReady;
  }

  function mount(host, opts = {}) {
    const { videoId, start = 0, loop = false, muted = true,
            frameClass = '', onReady, onError } = opts;
    let player = null, alive = true, fired = false;

    const fail = () => {
      if (!alive || fired) return;
      fired = true;
      if (player && player.destroy) { try { player.destroy(); } catch (_) {} }
      player = null;
      if (onError) { try { onError(); } catch (_) {} }
    };

    if (!host || !videoId) { fail(); return { destroy() { alive = false; } }; }

    // The API replaces its target node with the <iframe>. Give it a throwaway
    // child so we own `host`'s contents and never clobber sibling UI.
    host.innerHTML = '<div></div>';
    const slot = host.firstChild;

    loadAPI().then(() => {
      if (!alive) return;
      // rel=0 + modestbranding + no annotations = least YouTube chrome. mute=1
      // guarantees muted autoplay is allowed without a user gesture (the page
      // already has radio + soundscape — a second audio source would clash).
      const playerVars = { autoplay: 1, rel: 0, playsinline: 1, modestbranding: 1, iv_load_policy: 3 };
      if (muted) playerVars.mute = 1;
      if (start) playerVars.start = start;
      if (loop)  { playerVars.loop = 1; playerVars.playlist = videoId; }   // single-video loop trick
      try {
        player = new YT.Player(slot, {
          videoId,
          playerVars,
          events: {
            onReady: e => {
              try {
                if (muted) e.target.mute();
                e.target.playVideo();
                const ifr = e.target.getIframe();
                if (ifr) {
                  if (frameClass) ifr.className = frameClass;
                  ifr.allow = 'autoplay; encrypted-media; picture-in-picture; fullscreen';
                  ifr.allowFullscreen = true;
                }
              } catch (_) {}
              if (onReady) { try { onReady(e); } catch (_) {} }
            },
            // Error codes 2/5/100/101/150 = bad param / HTML5 / removed /
            // private / embedding-disabled — every "rotted" case lands here.
            onError: fail,
          },
        });
      } catch (_) {
        fail();
      }
    });

    return {
      destroy() {
        alive = false;
        if (player && player.destroy) { try { player.destroy(); } catch (_) {} player = null; }
      },
    };
  }

  return { mount, loadAPI };
})();

window.YTEmbed = YTEmbed;
