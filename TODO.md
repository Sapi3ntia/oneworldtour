# 🌍 One World Tour — Ideas & Guardrails (v2)

Two parts: **ideas not yet built** and the compact **don't-break-these** list.
The architecture itself is documented in [`README.md`](README.md).

---

## The four principles (every feature honors these)

1. **In-app, no off-site redirects.** Embed the real thing or honestly say it
   doesn't exist yet.
2. **Live means live.** 🔴 live cams and 🪟 windows are real streams verified
   `is_live` — never a loop, timelapse, still, or frozen widget. (Owner decision
   2026-07: the v1 recorded-"ambient" and Windy day-timelapse window tiers were
   removed. Later that month Windy was dropped *entirely* — its embed player is
   a poster that links out to windy.com and never autoplays. Legacy `ambient`
   fields and `data/windy.json` remain in the repo but are not rendered/loaded.)
3. **Skippable / seekable.** Walks keep native controls — our edge over
   virtualvacation.us.
4. **Alive.** Local time, weather, radio, headlines — a place should feel like
   *right now*.

---

## 🎯 Ideas not yet built

### Content depth (the steady grind)
- **Run `tools/enrich_media.py` regularly.** It checkpoints into `data/media.json`
  and skips finished cities — a weekly sweep keeps cams fresh and fills gaps.
  Consider a `--reverify` mode that re-checks `is_live` on previously-found cams
  and drops dead ones (currently they only die honestly at runtime via onError).
- **Review auto-picks.** `media.json` quality is good but not curated-good; promote
  great finds into the region JSON (`walk`/`webcam`/`window`) and they become
  permanent.
- **More monuments** — 30 cities have them (2026-07-17 batch added NYC, Sydney
  Opera House, the Kremlin, Trevi, SF ×3, Rio ×3, Santorini, Gateway Arch; cap
  is now 5/city). Next marquee candidates: Dubai → Burj Khalifa, Cape Town →
  Table Mountain, Istanbul → Hagia Sophia, Athens → Acropolis.
- **Author `highlights`/`blurb`** for content-thin new countries.

### Product ideas (additive)
- **Day/night terminator** on the SVG map (v1 had one on Leaflet) — project the
  solar terminator as a translucent SVG path; cheap math, nice "alive" signal.
- **Trip planner / Fly the Tour** — v1's ordered multi-stop route with a plane
  gliding leg by leg. The SVG engine can do this beautifully (`drawLine` +
  animated dot along the great circle). Deliberately not ported yet.
- **Drop In** — v1's "tap anywhere → nearest place's scene". Trivial now:
  `unproject(click)` + nearest-by-km.
- **Visited tint** — dim/star city dots you've already stamped (`State.visited`).
- **Cluster live badges** — country nodes could show a tiny red tick when they
  contain a live cam and the 🔴 filter is on.
- **Back in Time** — historical/Indigenous borders timeline (native-land.ca API,
  historical-basemaps). Big lift; its own mode.

**Parked / declined:** multiplayer Guesser rooms; postcard studio (v1 feature,
dropped in v2 — resurrect from git if missed); satellite descend-from-orbit.

---

## 🛑 Don't break these (measured, learned the hard way)

**The owner's machine renders in SOFTWARE (VM, no GPU).**
- No `backdrop-filter` anywhere. No infinite paint animations. Transitions on
  transform/opacity/color only.
- When something "feels slow/glitchy": measure frame times (rAF) and *look at
  screenshots at real widths*. A console-error sweep proves nothing about lag.

**The map (js/worldmap.js):**
- It's ours — no Leaflet, no tiles, no markercluster. Keep it that way; every v1
  map bug traced back to those.
- Camera moves are viewBox tweens only. **Never** fit a bounding box on a click
  the user didn't aim (that was v1's "thrown into the ocean" bug — `flyToPlaces`
  only runs on explicit country clicks / guess reveals).
- `assets/world.json` and `js/lib/geo.js` share projection constants
  (W=1000, H=520, Natural Earth I). If you regenerate one, keep the other in sync.
- Strokes use `vector-effect: non-scaling-stroke`; dot radii update once per zoom
  change. Don't attach per-dot listeners — events delegate from the container.

**Media honesty (js/lib/media.js + yt.js):**
- "Live" must be `is_live` — an oEmbed 200 only proves *public*.
- No still, loop, or timelapse may ever fill a 🔴/🪟 slot.
- Every curated YouTube surface mounts through `yt.mount` so a rotted id removes
  its own tab (never a dead iframe).
- Hand-curated region-JSON fields always outrank `media.json`. Fix a bad auto-pick
  by curating, not by hand-editing `media.json` (a future sweep may overwrite it).

**Env / tooling:**
- Serve on `127.0.0.1:8099`, **not** `0.0.0.0` (sandbox classifier blocks it).
- Keyless at runtime. `tools/windy.key` is build-time only, gitignored.
- Data fetches use `cache: 'no-cache'` (always revalidate) + sessionStorage
  (10 min, key `owt_data_cache_v5`). Worst-case staleness after editing a data
  file is 10 min in an already-open tab; `?bust` or a reload skips it. (The old
  default-cache fetches let Chrome's heuristic HTTP cache resurrect purged
  media.json picks — the "Churchill still shows Mississauga" bug, 2026-07-10.)
- Don't re-run the stale v1 one-off builders (`build_europe.py`, `build_usa.py`) —
  they clobber the normalized live JSON. `fetch_windy.py`/`windy.json` are retired
  (Windy embeds never autoplay); live cams come from `tools/enrich_media.py`.
- Verify headlessly: `chromium --headless --disable-gpu --screenshot=… 
  --virtual-time-budget=10000 http://127.0.0.1:8099/…` — and *look* at the shot.

---

## Recently landed (so it isn't re-litigated)

- **📺 Live TV + 🦁 Wildlife (2026-07-15):** `data/tv.json` (country → national
  channels; CN: CGTN/CCTV-4/CCTV-13 · KP: KCTV · RU: RT · plus NHK/KBS/Al
  Jazeera/DW/France 24/TRT) rendered as a Location-page panel via `js/lib/tv.js`;
  YouTube TV mounts through `yt.mount`, RT/KCTV play from broadcaster HLS through
  lazy-loaded hls.js (both verified CORS-open). TV stops the radio and vice versa;
  a dead channel removes itself with a toast. `data/wild.json` adds 14 live nature
  cams as places (Brooks Falls, GRACE gorillas, Lola ya Bonobo, Tembe, Djuma,
  Mpala, Amboseli, ol Donyo, Okaukuejo, Namib, Victoria Falls waterhole, Big Bear
  + Decorah eagles, Chengdu pandas) + Pyongyang joins asia.json with a 2026 walk.
  Home gets a 🦁 filter + "Wild live cams" rail (`region wild` ∪ live `nature`
  places). Every id/stream vetted actually-live via yt-dlp/curl on 2026-07-15 —
  future sweeps should re-verify `tv.json` and `wild.json` the same way.

- **v2 rebuild (2026-07):** framework-free ES modules; custom SVG map engine
  (country nodes → city dots, wheel/drag/glide camera); tabbed scene stage
  (walk / monuments / live / window); live-only window policy; Netflix-style
  photo rails; search-first home; passport + guesser ported (guesser now uses the
  SVG map's projection inverse for picks).
- **`tools/enrich_media.py`:** yt-dlp auto-curation with vetting (embeddable,
  is_live at vet time, title/duration/recency checks, street-vs-window
  classification). First sweeps found fresh 2024–2026 walks and live cams across
  Asia, Africa, the Americas; places with nothing verifiable stay honestly empty.
- **v1 → git history:** Leaflet map, ambient loops, Windy day-timelapses, trip
  planner, postcard studio. Resurrect from git if ever wanted.
