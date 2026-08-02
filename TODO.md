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
- **More monuments** — **301 of 507 places (59%) now have them**, up from 30 (8%)
  before the 2026-07-18 sweep: 633 auto + 48 curated tabs, almost all 2160p.
  Remaining gaps are mostly small towns and nature sites where there is no
  monument to shoot. Re-run with `--per-city 3` to deepen the marquee cities
  rather than widen coverage — but **run `prune_monuments.py` dry straight
  afterwards**, because the highlight-as-search-term fault (see 2026-08-02 below)
  will resurface in any region whose highlights name people, dishes or dynasties.
  Each pick stores its `height` and, since 2026-08-02, its `title`, so a future
  pass can audit the whole set for quality *and* honesty with no network. The
  pre-2026-08-02 picks that survived the backfill all have both; anything written
  before the `MIN_HEIGHT = 720` floor has no height and would need re-querying.
- **Author `highlights`/`blurb`** for content-thin new countries.
- **More places for thin routes.** The 13 that were blocking trips are now in
  (2026-07-18) — see "Recently landed". Remaining candidates, in rough order of
  how much they'd add: **Winslow AZ and Galena KS** (Route 66 has the big towns
  now but none of the small ones), **Khiva** (completes the Uzbek trio with
  Samarkand and Bukhara), **Lake Titicaca / Puno** (the natural Gringo Trail leg
  between Cusco and La Paz, currently a 400 km jump), and **Ulan-Ude** (the
  Trans-Mongolian branch point). Add via the normal path — region JSON entry +
  `enrich_media.py --only` + `enrich_monuments.py --only` + a `check_trips.py`
  run — then extend the affected trips' `stops`.

### Product ideas (additive)
- **Day/night terminator** on the SVG map (v1 had one on Leaflet) — project the
  solar terminator as a translucent SVG path; cheap math, nice "alive" signal.
- **Fly the Tour** — the *animated* half of v1's trip planner: a plane gliding
  leg by leg along the route. 🧭 **Trips shipped** (`data/trips.json`, 18 curated
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

- **🏞️ The Grand River watershed — 19 places + a trip (2026-08-01):** every Grand
  River Conservation Area is now a place (`canada.json` 17 → 36), Luther Marsh at
  the source down to Byng Island at Lake Erie, with facts taken from GRCA's own
  property pages. 🏞️ **The Grand River Run** walks all 21 in river order, source to
  mouth, 274 km as the crow flies. Where GRCA owns something Wikipedia has never
  heard of, `wikipedia_slug` points at the **containing** settlement or watercourse
  (same precedent as `big-bear-eagles → Big_Bear_Lake,_California`) and never at a
  namesake elsewhere — Wikipedia's "Pinehurst Lake" is in **Alberta**, so Ontario's
  kettle lake points at `County_of_Brant`. Enrichment got a scene for **6 of the
  21 stops** (Elora Gorge, Elora Quarry, Snyder's Flats, Guelph Lake, Hanlon
  Creek, and the Grand River itself); the other **15** returned **nothing
  verifiable**, most of them twice. Small Ontario conservation areas mostly aren't
  on YouTube in a form that passes the vetter. That is the honest gap working;
  don't re-run those hoping.

  Four of those gaps were *scenes that got deleted later the same night* — the
  vetting overhaul below found them borrowing footage from whatever was nearby.
  Apps' Mill was showing Papermill Lake in **Halifax, Nova Scotia**; Brant was
  showing a **Brantford** city walk and an **Elora** day-trip drive matched on
  nothing but the word "conservation"; Luther Marsh had the same Elora video.
  Refills found nothing honest. Expect this corner of the map to stay thin.

- **🇨🇳 China, properly — 111 new places (2026-08-01):** `asia.json` 79 → 190, and
  China alone is now 117 places. The six we had (Beijing, Shanghai, Badaling,
  Xi'an, Guilin, Hong Kong) were name-and-coordinate **skeletons** — empty
  `blurb`, empty `fun_fact`, empty `highlights`, null `hidden_gem_tip` — and are
  filled. New: the tier-one four, the "new first-tier" cities (Chengdu, Hangzhou,
  Wuhan, Xi'an, Chongqing, Suzhou…), tier-2 and tier-3/4 cities, the water towns
  (Wuzhen, Zhouzhuang, Xitang, Tongli), rural China (Hongcun, Xidi, Wuyuan,
  Zhaoxing, Xijiang, Chengyang, Cuandixia, Shaxi, Longji and Yuanyang terraces,
  Hemu, Jiaju, Yubeng), the big nature (Zhangjiajie, Jiuzhaigou, Huangshan, Tai,
  Emei, Tiger Leaping Gorge, Kanas, Qinghai Lake, Namtso, Rongbuk, Zhangye Danxia,
  Hukou, Detian, Fanjingshan, Li River), the grottoes (Mogao, Longmen, Yungang,
  Leshan, Wudang), Tibet (Lhasa, Shigatse), **ten Hong Kong** districts and
  outlying islands (Victoria Peak, TST, Mong Kok, Sham Shui Po, Sai Kung, Tai O,
  Cheung Chau, Lamma, Tai Mo Shan, Tian Tan Buddha) and **Macau** (plus Taipa and
  Coloane). Rules that cost time to work out are in README → *Filling a region
  out*: **Wikidata P625, never an OSM administrative centroid** (OSM's "Chongqing"
  node is ~200 km out in the rural east); every slug checked live and stored
  **canonical**, because `arrivalPhoto()` omits `redirects=1` so a redirect slug
  silently loses the card photo; **city tiers stay in the prose, hedged** — there
  is no government tier list, it's a business magazine's yearly ranking, and a
  `tier:` field would read as official. Hong Kong and Macau keep `country: China`
  because the pre-existing `hong-kong` entry already did.

- **🚄 Two trip changes off the back of it (2026-08-01):** the Silk Road jumped
  Samarkand straight to Xi'an because the entire Chinese corridor was missing; it
  now runs Kashgar → Turpan → Dunhuang → Mogao → Jiayuguan → Zhangye Danxia →
  Lanzhou (10 → 17 stops). New 🚄 **The Middle Kingdom Line**, the first-timer's
  rail route, Beijing round to Shanghai, 17 stops / 4,911 km. Atlas totals:
  **507 places · 94 countries · 18 trips.**

- **🔍 The China sweep finished, and broke the vetter open (2026-08-01, overnight):**
  all 117 China places have been swept. Watching that batch — the biggest the
  vetter had ever faced — turned up a **systemic** bug, not a handful of bad
  videos, so the fix went into the shared rules and then ran back over all 507
  places. `prune_media.py` exists for exactly this: rules get stricter, and
  `media.json` is a checkpoint, so a pick made under looser rules lives forever
  unless something re-applies today's rules to yesterday's data.

  The root cause: `mentions_place` matched a place on **any** word of its name
  over three letters, by substring. So `mount` won Mount Tai a Greek monastery,
  `river` won Li River the Yellow River, `island` won car-free Lamma Island a
  Hong Kong Island drive, and `brant` — inside "**Brant**ford" — won Brant
  Conservation Area a walk through the city next door. Now only tokens outside
  `GENERIC_TOKENS` count; tokens under six letters must match whole words, longer
  ones may still match loosely because cam operators write "SedonaLiveCam.com".

  Seven more guards came out of the same pass, each named in README's guard
  table with the video that earned it: **Canadian provinces** (`Ross Bay,
  Victoria BC` was Victoria Peak's window — and no comma is required, Canadians
  write "Victoria BC" bare), **lottery studios** (`LIVE DRAW TOTO MACAU`),
  **`abandoned`/`urbex`** (a Nanchang urbex video as its driving tour),
  **`city_tour_of_the_wild`** (Zhangye's streets for the geopark outside town),
  **`music_loop_not_a_cam`** (a chill-music loop spanning Amalfi *and* Lake Como,
  700 km apart, as Amalfi's live seat), **possessive apostrophes** (`Mallorca's`
  searched for `mallorcas`, so the Balearics had been losing genuine Mallorca
  footage), and the big one — **`INHERITS_HIGHLIGHTS`**.

  That last one closes the hole the previous handoff left open. A place used to
  be able to match on any of its own `highlights`, which regions genuinely need
  (Catalonia is only ever filmed as Barcelona), but a *site* whose highlights
  list the nearby city was quietly borrowing that city's footage. Nothing in the
  data separates the two cases — `type` calls both `catalonia` and
  `zhangye-danxia` `nature`, and `region` is administrative, so the French
  Riviera's says "Provence-Alpes-Côte d'Azur" — so it is now an **explicit list**
  of 21 container ids. Leaving an id out costs a scene; putting a wrong one in
  ships a lie, so when in doubt leave it out. Four good picks the rule would have
  cost were kept by adding the uploader's spelling to `ALIASES` instead (`Nam co`,
  `爨底下`, `Fanjing`).

  **13 scenes were deleted** across the corpus, several of them long-standing and
  invisible until now: Cusco's live cam was *"Plaza de Armas de Querétaro en
  vivo"* — **Mexico**, 5,000 km away, on a plaza name half of Latin America
  shares. Apps' Mill's walk was Papermill Lake in **Halifax, Nova Scotia**.
  Antelope Canyon's live was a **Lake Powell marina**. Refilling recovered three
  (Longmen Grottoes a drive, Churchill a walk, Namib a window); the other ten are
  honest gaps now. `prune_media.py` reports **0 drops** and the whole corpus
  passes.

  All of it is frozen in **`tools/test_vetting.py`** — 44 cases then, no network,
  run it in a second. Every `want=False` is a scene that actually shipped; every
  `want=True` is honest footage some rule refused until it was loosened
  correctly. Run it after touching any regex in `enrich_media.py`, because the
  rules only ever get stricter and each tightening is one character away from
  killing good picks (this pass alone produced four false-positive rounds before
  it settled — `Kauaʻi`, `SedonaLiveCam.com`, Malta's "chilling by night", and a
  Hukou drive that merely starts downtown).

- **🏛️ 337 monument tabs for China, 73 of which were not monuments (2026-08-02):**
  `enrich_monuments.py` swept all 118 China places, and reviewing the result found
  a systemic fault rather than a few bad videos. `candidate_landmarks()` spends
  every `highlight` as a search term, but highlights are written for the *blurbs*,
  so the China ones carry people, dishes, dynasties, ethnic groups and species
  beside the buildings — Foshan's "Ip Man" tab was the 2008 feature film, Haikou's
  "Hainanese chicken rice" tab was a food walk in **Singapore**, Wudang's "Tai chi"
  tab was a 40-minute workout, Langzhong's "Sichuan" tab was a different town
  250 km away. `NOT_A_MONUMENT` now covers those categories, and a new
  `is_a_region()` rejects any highlight naming a country, province or region,
  filled from the corpus so it needs no per-country list. **73 tabs deleted:**
  633 auto + 48 curated across 301 places.

  Four durable lessons from it:

  - **Monument tabs store their `title` now.** `find_monument()` always returned
    one and the caller dropped it, so unlike a media seat a monument could not be
    re-vetted offline — auditing this batch cost 637 network calls to learn what
    had already shipped. `prune_monuments.py` is the monument counterpart to
    `prune_media.py`, and its **name** rules run without a title because they are
    the strong ones: a landmark that is a dish has no honest video *whatever the
    search returned*.
  - **Put the rule at the right layer, and prefer the narrow signal.** A bare
    `\(\d{4}\)` is a terrible film detector — uploaders stamp the upload year in
    parens constantly, and it killed Macau's "SENADO Square Walking Tour (2023)"
    and Pyongyang's "INSIDE Ryugyong Hotel … (2021)". A film puts the year at the
    *front*. A blanket *person* rule was the other tempting mistake: 6 of the 8
    person-named tabs show a real site named after them (Lu Xun's native place,
    Foshan's Yip-man museum, Tashilhunpo), so it would have traded six honest tabs
    for one film. A *deity* rule is fair — Leshan's "Maitreya" was in Indonesia.
  - **`region` being empty silently disables a guard.** Six US places (the Route
    66 additions of 2026-07-18) had no `region`, and `wrong_place_title` compares
    a title's state against it, so their own-state exemption was simply dead.
  - **A one-token place name matches things that merely contain it.**
    `mexico-city` reduces to `mexico` ("city" is generic), so *any* title with
    **"New Mexico"** read as Mexico City, 1,600 km from Albuquerque. The guard is
    asymmetric on purpose: "New Mexico" is not Mexico, but "New York" *is* New
    York City (`new-york-city` reduces to `york`), so a place may be found inside
    a `New <token>` phrase only when its own name starts with "New".

  `test_vetting.py` is at **50 cases**. All five tools load the gazetteer through
  `em.register_place()` instead of repeating the three-line dance — that
  duplication is exactly how a new global like `NEW_NAMED` ends up loaded in one
  caller and missing from four.

- **🗺️ 13 places + the Gringo Trail (2026-07-18):** Cusco and Machu Picchu (Peru
  had only two `ancient.json` sites and no cities at all), Route 66's missing
  middle (Tulsa, Oklahoma City, Amarillo, Albuquerque, Flagstaff, Santa Monica
  Pier), the Trans-Siberian's three (Yekaterinburg, Novosibirsk, Irkutsk) and the
  Silk Road's Samarkand + Bukhara — Uzbekistan is a new country, taking the atlas
  to 375 places / 94 countries. Route 66 went 5 → 11 stops, Trans-Siberian 5 → 8,
  Silk Road 8 → 10, plus a new 🦙 **Gringo Trail** (Paracas → Cusco →
  Sacsayhuamán → Machu Picchu → La Paz → Uyuni). Enrichment on just these 13
  returned 12 walks, 11 drives, 3 live, 3 window and 37 monument tabs — a far
  better hit rate than sweeping places that had already failed, which is the
  argument for `--only` over another broad sweep.

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
