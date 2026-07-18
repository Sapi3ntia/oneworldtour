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
  **Diminishing returns are real** (measured 2026-07-18): a 23-minute phase over
  the 150 places that every prior sweep already failed on yielded 3 scene slots
  (`washington-dc` +window, `nashville` +window, `addis-ababa` +live). Walk/drive
  sit at 88% and live/window at 40%/26%, and those last percentages are mostly
  *not* findable — the cities left genuinely lack a dedicated embeddable 24/7 cam.
  Prefer `--only` on specific new places over another broad sweep.
  Consider a `--reverify` mode that re-checks `is_live` on previously-found cams
  and drops dead ones (currently they only die honestly at runtime via onError).
- **Review auto-picks.** `media.json` quality is good but not curated-good; promote
  great finds into the region JSON (`walk`/`webcam`/`window`) and they become
  permanent.
- **More monuments** — **175 of 362 places (48%) now have them**, up from 30 (8%)
  before the 2026-07-18 sweep: `tools/enrich_monuments.py` added 239 tabs across
  two phases (famous-tagged first at 3/city, then everywhere else at 2/city),
  almost all 2160p. Remaining gaps are mostly small towns and nature sites where
  there is no monument to shoot. Re-run with `--per-city 3` to deepen the marquee
  cities rather than widen coverage.
- **Author `highlights`/`blurb`** for content-thin new countries.
- **Places the curated trips are missing.** Building `data/trips.json` surfaced
  real gaps — these routes are honest but thin, and each named place would make
  one materially better:
  - *Route 66* runs Chicago → St. Louis → Santa Fe → Grand Canyon → LA. The whole
    small-town middle is absent: **Tulsa, Oklahoma City, Amarillo, Albuquerque,
    Flagstaff**, and the actual finish line, **Santa Monica Pier**.
  - *Trans-Siberian* skips **Yekaterinburg, Novosibirsk and Irkutsk** — Irkutsk is
    the classic stop before Baikal.
  - *Silk Road* has no **Samarkand or Bukhara**, which is most of the point of it.
  - **Cusco and Machu Picchu are missing from the atlas entirely** (Peru has only
    two `ancient.json` sites). That's the biggest single hole in the dataset and
    it blocks an obvious "Gringo Trail" trip.
  Add via the normal path — region JSON entry + `enrich_media.py` + a
  `check_trips.py` run — then extend the affected trips' `stops`.

### Product ideas (additive)
- **Day/night terminator** on the SVG map (v1 had one on Leaflet) — project the
  solar terminator as a translucent SVG path; cheap math, nice "alive" signal.
- **Fly the Tour** — the *animated* half of v1's trip planner: a plane gliding
  leg by leg along the route. 🧭 **Trips shipped** (`data/trips.json`, 15 curated
  routes drawn with `drawLine` + numbered `addStop` markers), so the data and the
  map work are done; what's left is the animation — a dot interpolated along each
  leg (`geo.interpolate` already exists) with the stop list scrolling to follow.
  Also still open: **user-built** routes, as opposed to the curated ones.
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

- **🧹 `tools/prune_media.py` + 9 deletions (2026-07-18):** a rule-checker for
  media.json that flags picks violating principle #2 and deletes them. It removed
  9: nest-box cams standing in for cities (`vienna`, `ghent`, `san-jose` ×2 —
  kestrels and peregrine falcons), an aquarium tank (`seattle`), multi-cam
  rotators (`sicily` Etna, `glacier-np` "Montana Webcam Tour"), and the worst
  offender — `manchester` (England) serving a hawk camera in Manchester, **Iowa**
  and a falcon feed in Manchester, **New Hampshire**. Coverage dropped live 41→40%
  and window 27→26% as a result. That drop is the tool working, not a regression;
  don't "fix" it by restoring the picks.

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
