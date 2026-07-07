/* ============================================================
   WALKTHROUGH — shared in-app scene player.

   The core is renderScene(): it paints a place's best available scene
   into ANY element and is reused everywhere a "video from there" is shown:
     • the location page (▶ Virtual Walk button)  — via open()  (modal)
     • the map page ("Drop In": tap → nearest place) — via open()  (modal)
     • the City Guesser (guess.html)                — renderScene(blind)
     • the Virtual Window (window.html)             — renderScene()

   Tiers, best first:
     Tier 1  curated video (loc.walk = "<ytid>" | { yt })  → embedded YouTube
             via the IFrame API, so native controls stay on (skippable /
             seekable) AND we get an onError signal: a deleted / private /
             embedding-disabled video falls back to Tier 5 instead of
             showing YouTube's broken "Video unavailable" frame.
     Tier 5  Ken Burns photo flythrough from Wikimedia imagery (universal
             floor, clickable dots so you can jump around)

   Depends on: API (js/api.js). Lazy-loads the YouTube IFrame API.
   ============================================================ */
const Walkthrough = (() => {
  let mounted = false;
  let overlay, stage, label, sub, closeB;
  let sceneHandle = null;            // the modal's current scene

  /* Lazy-load the YouTube IFrame Player API exactly once. */
  let ytReady = null;
  function loadYT() {
    if (window.YT && window.YT.Player) return Promise.resolve();
    if (ytReady) return ytReady;
    ytReady = new Promise(resolve => {
      const prev = window.onYouTubeIframeAPIReady;
      window.onYouTubeIframeAPIReady = () => { try { prev && prev(); } catch (_) {} resolve(); };
      const s = document.createElement('script');
      s.src = 'https://www.youtube.com/iframe_api';
      document.head.appendChild(s);
    });
    return ytReady;
  }

  /* --------------------------------------------------------------
     renderScene(el, loc, opts) — paint a scene into `el`.
     opts.blind   === true → hide every name-revealing caption.
     opts.noVideo === true → never use the curated YouTube walk (its title bar
                             would reveal the place) — force the photo flythrough.
                             Used by the City Guesser, which needs both.
     Returns a handle: { kind:'video'|'photos', ready:Promise<bool>, destroy() }
     `ready` resolves true once real content is on screen (false if none).
  -------------------------------------------------------------- */
  function renderScene(el, loc, opts = {}) {
    const blind = !!opts.blind;
    let timer = null, alive = true, player = null;
    let resolveReady;
    const ready = new Promise(r => (resolveReady = r));

    const stop = () => {
      alive = false;
      if (timer) { clearInterval(timer); timer = null; }
      if (player && player.destroy) { try { player.destroy(); } catch (_) {} player = null; }
    };

    const vid = !opts.noVideo && (typeof loc.walk === 'string' ? loc.walk : (loc.walk && loc.walk.yt));

    /* Tier 5 — Ken Burns photo flythrough. Also the fallback if a curated
       video turns out to be gone or non-embeddable. */
    function startKen() {
      el.innerHTML =
        `<div class="walk-loading">${blind ? 'Opening a view…' : 'Gathering a view of ' + esc(loc.name) + '…'}</div>`;
      (async () => {
        const photos = await API.getGalleryPhotos(loc.wikipedia_slug, 8);
        if (!alive) { resolveReady(false); return; }
        if (!photos.length) {
          el.innerHTML =
            `<div class="walk-loading">${blind ? 'No imagery for this place yet.' : 'No imagery to walk through for this place yet.'}</div>`;
          resolveReady(false);
          return;
        }
        const caps = blind ? [] : captions(loc, photos.length);
        el.innerHTML = `
          <div class="ken-track">
            ${photos.map((p, i) => `<div class="ken-slide${i === 0 ? ' on' : ''}" style="background-image:url(${p})"></div>`).join('')}
          </div>
          <div class="ken-dots">${photos.map((_, i) => `<i${i === 0 ? ' class="on"' : ''} data-i="${i}"></i>`).join('')}</div>
          ${blind ? '' : '<div class="ken-cap" id="ken-cap"></div>'}`;

        const slides = [...el.querySelectorAll('.ken-slide')];
        const dots   = [...el.querySelectorAll('.ken-dots i')];
        const capEl  = el.querySelector('#ken-cap');
        let idx = -1;
        const show = (n) => {
          if (idx >= 0) { slides[idx].classList.remove('on'); dots[idx].classList.remove('on'); }
          idx = n;
          slides[idx].style.animationName = idx % 2 ? 'ken-pan-b' : 'ken-pan-a';
          slides[idx].classList.add('on');
          dots[idx].classList.add('on');
          if (capEl) capEl.textContent = caps[idx] || '';
        };
        const advance = () => show((idx + 1) % slides.length);
        show(0);
        timer = setInterval(advance, 5200);
        // Click a dot to jump — "click where to adjust".
        dots.forEach(d => d.addEventListener('click', () => {
          if (timer) clearInterval(timer);
          show(+d.dataset.i);
          timer = setInterval(advance, 5200);
        }));
        resolveReady(true);
      })();
    }

    /* Tier 1 — curated YouTube walk via the IFrame API (for onError). */
    function startVideo() {
      el.innerHTML = `<div class="walk-video walk-yt-host"></div>`;
      resolveReady(true);   // a vetted video counts as ready immediately
      loadYT().then(() => {
        if (!alive) return;
        const host = el.querySelector('.walk-yt-host');
        if (!host) return;
        player = new YT.Player(host, {
          videoId: vid,
          // rel=0 + modestbranding + no annotations = least YouTube chrome / fewest
          // links out. (Platform limit: a YouTube embed always keeps *some* of its
          // own links — see DEVNOTES. The onError fallback covers non-embeddable ones.)
          playerVars: { autoplay: 1, rel: 0, playsinline: 1, modestbranding: 1, iv_load_policy: 3 },
          events: {
            onReady: e => { try { e.target.getIframe().classList.add('walk-video'); } catch (_) {} },
            onError: () => {                       // deleted / private / embedding off
              if (!alive) return;
              try { player.destroy(); } catch (_) {} player = null;
              startKen();                          // never leave a broken YouTube frame
            }
          }
        });
      });
    }

    if (vid) { startVideo(); return { kind: 'video', ready, destroy: stop }; }
    startKen();
    return { kind: 'photos', ready, destroy: stop };
  }

  /* ---------------- Modal wrapper (location ▶ button + map Drop In) -------- */
  function mount() {
    if (mounted) return;
    overlay = document.createElement('div');
    overlay.id = 'walk-overlay';
    overlay.innerHTML = `
      <div class="walk-modal">
        <button class="walk-close" id="walk-close" title="Close">✕</button>
        <div class="walk-stage" id="walk-stage"></div>
        <div class="walk-bar">
          <span class="walk-title" id="walk-mode-label"></span>
          <span class="walk-sub" id="walk-sub"></span>
        </div>
      </div>`;
    document.body.appendChild(overlay);
    stage  = overlay.querySelector('#walk-stage');
    label  = overlay.querySelector('#walk-mode-label');
    sub    = overlay.querySelector('#walk-sub');
    closeB = overlay.querySelector('#walk-close');

    closeB.addEventListener('click', close);
    overlay.addEventListener('click', e => { if (e.target === overlay) close(); });
    document.addEventListener('keydown', e => {
      if (e.key === 'Escape' && overlay.classList.contains('show')) close();
    });
    mounted = true;
  }

  function close() {
    if (!overlay) return;
    overlay.classList.remove('show');
    if (sceneHandle) { sceneHandle.destroy(); sceneHandle = null; }
    stage.innerHTML = '';   // tear down the iframe / images
  }

  /* Open the walkthrough modal for a location object.
     opts.subtitle — small note shown in the bar (e.g. "nearest to your tap · 12 km"). */
  function open(loc, opts = {}) {
    if (!loc) return;
    mount();
    overlay.classList.add('show');
    if (sceneHandle) sceneHandle.destroy();
    if (sub) sub.textContent = opts.subtitle || '';
    sceneHandle = renderScene(stage, loc, opts);
    label.textContent = sceneHandle.kind === 'video' ? '▶ Guided walking tour' : '🎞️ Photo flythrough';
  }

  /* Captions: title → blurb sentences → highlights → fun fact → (Ancient) claim. */
  function captions(loc, n) {
    const caps = [loc.name + (loc.country ? ` · ${loc.country}` : '')];
    if (loc.blurb) loc.blurb.split(/(?<=[.!?])\s+/).forEach(s => { if (s.trim()) caps.push(s.trim()); });
    (loc.highlights || []).forEach(h => caps.push('✦ ' + h.name));
    if (loc.fun_fact) caps.push('Did you know? ' + loc.fun_fact);
    if (loc.aa_claim) caps.push('🤫 ' + loc.aa_claim);
    while (caps.length < n) caps.push(loc.name);
    return caps.slice(0, n);
  }

  function esc(s) {
    return String(s).replace(/[&<>"']/g, c =>
      ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  }

  return { open, close, renderScene };
})();

// The app's one shared scene player — expose it for cross-module use / devtools.
window.Walkthrough = Walkthrough;
