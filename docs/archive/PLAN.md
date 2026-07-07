# 🛠️ One World Tour — Active Plan

The working roadmap (distinct from `IDEAS.md`, which is the long-term parking lot).
Reflects direction set by the project owner. **Read this at the start of each session.**
For *how* things work (the scene player, the walk-id curation method, verification recipes,
and known tech debt), see the developer manual: [`DEVNOTES.md`](DEVNOTES.md).

---

## 🎯 Guiding principles (owner's intent)

1. **Immersive, in-app, no off-site redirects.** Either embed the real thing (video, cam,
   photos) *inside* the app, or honestly state it doesn't exist. **No "browse on YouTube",
   no "watch on Netflix", no launcher links** standing in for a feature. Content links that
   ARE the feature (a news headline's source article) are fine; redirects that *replace* a
   feature are not.
2. **No fake/forever-loading states.** If there's no data (photos, cam, etc.), say so
   plainly. Never leave a perpetual shimmer/spinner.
3. **Inspiration: [virtualvacation.us](https://virtualvacation.us/)** — match its best modes
   (videarth "click a map point → video", **City Guesser**, **Virtual Window / "open a
   window"**), but **do them better**: every scene must be **skippable / seekable** — their
   videos and windows give you no controls and no length. Skippability is *the* differentiator.
4. **Creative, surprising, alive** — the radio feature is the bar (real, live, local, in-app).

---

## ✅ Done

- 🪟🔴 **WINDOWS + LIVE CAMS at scale via Windy Webcams API — ~25 → 247 windows, ~17 → 105 live
  (owner: "keep going with more windows, live cams…").** Hand-curating YouTube cams doesn't scale to
  345 cities (and ids rot); the Windy catalogue (~70k geolocated cams) does. `tools/fetch_windy.py`
  does a **build-time** `nearby` lookup per city (key read from gitignored `tools/windy.key`, never
  shipped), picks the best in-city cam by distance+`viewCount`, and bakes the **`data/windy.json`**
  sidecar `{ id: { window, live?, title, km } }`. Runtime embeds the **keyless public player**
  (`webcams.windy.com/.../embed/player/<id>/<day|live>`, verified iframe-able). `webcam.js` gained
  `liveFor`/`windowFor`/`forWindow` with precedence **curated-YouTube → Windy** (curated always wins),
  and a third honest tier **`kind:'timelapse'`** for Windy's `/day` view (a real *current* look out the
  window — labelled as such, never passed off as a 24/7 stream or a fake loop). Wired into all three
  surfaces: map marker badges + search dropdown (`map.js`), the **Virtual Window** legend/chips/badge
  (`window.js` + `.w-kind.timelapse` CSS), and the per-place **Step Outside** Live-cam + Window tiles
  (`location.js`). **Verified live (CDP):** Window browser now lists 247 cams (116 live / 125
  timelapse / 6 ambient), embeds render with their own seek/fullscreen controls (bonus: satisfies the
  "skippable" rule), and the Oslo/Sydney/Tokyo location pages show real Windy windows. Bonus: the
  Windy player's built-in scrubber/timelapse selector gives the seekability virtualvacation lacks.
  Full method in `DEVNOTES.md` §3f. Re-run anytime with `python3 tools/fetch_windy.py` (cached).
- 🌍 **WORLD COVERAGE — 39 → 89 countries, 191 → 345 locations (owner ask: "full parity first,
  then validate the new model").** Studied virtualvacation's full country set (84, from `/videarth`'s
  `countriesAndCities`), gap-analysed vs ours, and built a **country-first data model** to expand into:
  (1) `data/countries.json` — a canonical 89-country registry (ISO code, flag, continent, live/backlog
  status) via `tools/build_countries.py`; (2) normalized the existing data — **England/Scotland folded
  into United Kingdom** (Edinburgh was mis-tagged "England"), Faroe→Denmark, every record stamped
  `country_code`+`continent` (`tools/normalize_countries.py`); (3) generated all **50 missing countries
  / 154 new destinations** with **every coordinate + Wikipedia slug verified live against the MediaWiki
  API** — never recalled from memory (`tools/build_world.py`, new files `asia/africa/oceania/
  latinamerica.json` + appends to `europe.json`, registered as 4 new map regions); (4) extended
  `culture.js` so all 89 countries have a culture profile + currency code + facts (currency converter
  works everywhere) via `tools/build_culture.py`. Full record: **`COUNTRIES.md`** (coverage matrix) +
  **`OVERHAUL.md`** (architecture, migration path, build log, issues). New countries are coordinates-
  verified but content-thin (no curated windows/walks/highlights yet; culture phrases need a review) —
  see OVERHAUL §4 I-9/I-10.
- 🤫 Ancient Apocalypse collection (25 sites, violet markers, 🤫 filter, per-site episode +
  Hancock claim).
- Themed collections are **data-driven** — a region's `"accent"` hex drives both its chip and
  its markers; no per-collection CSS. (Adds the next collection for ~free.)
- `street_view` is **optional** — falls back to coordinates, can't crash a page.
- In-page **Virtual Walkthrough** (no redirect): curated tour video OR Ken Burns photo
  flythrough. Embedded YouTube keeps native controls, so it's already **seekable/skippable**.
- **No external redirect links:** removed the Netflix link, the webcam "browse on YouTube"
  launcher, and the walkthrough "more on YouTube" link.
- **Honest empty states:** webcam with no real cam says "No live webcam of this place";
  photo gallery with no images says so instead of shimmering forever.
- Webcam, when curated, **plays directly** (muted autoplay, native controls).
- 🌍 **FLAGSHIP — "Drop In" (videarth, but better):** toggle it on, tap anywhere on the map →
  the shared player opens with the **nearest** place's walkthrough. Curated video keeps native
  YouTube controls (seek/skip/length); the photo flythrough has **clickable dots to jump
  around**. v1 = snap-to-nearest.
- 🧱 **Extracted the player into `js/walkthrough.js`** — one shared, self-mounting module. Its
  core `renderScene(el, loc, {blind})` paints a place's video/photo flythrough into *any*
  element, so the location page, Drop In, City Guesser and Virtual Window all share one player.
- 🧱 **`js/destinations.js`** — shared region loader (`Destinations.loadAll()`), so new pages
  stop re-implementing the data fetch. Next step of de-monolithing.
- 🌍 **City Guesser (`guess.html`):** dropped into a mystery place's *blind* scene (name
  hidden), click the world map to guess, scored GeoGuessr-style on great-circle distance
  (5 rounds, 5 000 pts max each, live scorecard). **Better than theirs:** the clip is fully
  skippable/seekable, no forced timer, and reveal links straight to "Visit this place".
- 🪟 **Virtual Window (`window.html`):** a framed window onto somewhere, with a live
  local-time + day/night + temperature plate (Open-Meteo) so it feels like a real moment.
  "Open another window" hops at random; a chip row drops by curated spots. Skippable/seekable.
- 🎥 **Curated `"walk"` ids on 29 marquee cities** (1 CA, 4 US, 24 EU) — upgrades all four
  scene consumers (location page, Drop In, City Guesser, Window) from photo flythrough to real
  walking-tour footage at once. Each id was **research-vetted, never recalled from memory**
  (WebSearch → oEmbed confirm → write), and re-checkable via `tools/revet_walks.py` (29/29
  alive). The player now embeds via the **YouTube IFrame API** so a dead / private /
  non-embeddable video fires `onError` → **falls back to Ken Burns**, never a broken frame.
  City Guesser passes `noVideo:true` (a video's title bar would leak the answer); Window passes
  only `blind:true` (wants the video, no captions). Full method + caveats in `DEVNOTES.md`.
- 🌍 **City Guesser polish:** a **start screen** to pick which slice of the world to play
  (Everywhere / Europe / USA / Ancient / Canada — built from the data, with live counts, so new
  regions appear automatically), plus a **Wordle-style shareable score** (🟩🟨🟧⬛ per round,
  copied to clipboard, no spoilers) and a "Change region" button on the scorecard.
- 🎬 **Drop In honest empty state:** tapping open ocean / empty interior (nearest place
  > 1 500 km) now shows "Nothing close enough out here" instead of snapping you to a city
  thousands of km away.
- 🪟 **Virtual Window — fixed (was conceptually wrong), then made fully honest.** A window is a
  *live, fixed view you look out of*, so it must NOT be a walking tour or a panning slideshow
  (the old version reused the walkthrough player → a walkable YouTube tour showed up inside the
  frame). Rebuilt with its own renderer. Owner then flagged the still fallback as wrong too ("it's
  just an image of the earth" — a Wikipedia/Wikimedia lead image is often a map/satellite/globe
  shot, the opposite of a window), so it was made **live-webcam-only** (`🔴 Live view`): the pool
  filtered to cam-bearing places, and with no cams it says so plainly — **no still ever stands in
  for a window**. *(Later extended to **hybrid live + ambient** once we inspected virtualvacation
  and saw its windows are all recorded — see the "Window goes HYBRID" entry below. The no-still
  rule still holds.)* Plus opt-in **ambient soundscape** that follows the view, **remembers the
  last window** (localStorage `owt_last_window`), and a "Drop by" chip row. (Audio is opt-in by
  design — Web Audio needs a user gesture, so a toggle avoids a "button says on, nothing plays".)
- 🧱 **`js/webcam.js`** — shared `Webcam.resolve()` for the optional `webcam` field, used by both
  the location page's Live View and the Window (was duplicated in `location.js`). Also tightened
  every YouTube embed (`webcam.js` + `walkthrough.js`): `modestbranding` + `rel=0` +
  `iv_load_policy=3` to minimise YouTube's own links/chrome (can't be fully removed — platform
  limit; the `onError`→Ken Burns fallback still covers genuinely non-embeddable videos).
- 🚶🪟 **"Step Outside" on every place page (replaces the old ▶ Virtual Walk button + the separate
  Live View panel).** Side by side, no click required: an **auto-starting walking tour** (curated
  footage, muted so it doesn't fight the radio/ambient; native YT controls → still seekable/
  skippable) *or* an honest "not available", next to a **real window** of the place — a live
  webcam (🔴) when one exists, otherwise an honest "window not available" (🪟) — **no still photo
  posing as a window** (same honesty rule as the Virtual Window). The walk tile
  deliberately has **no Ken Burns fallback** (a real walk or nothing — we don't dress a slideshow
  up as a "walk"), so the location page no longer loads `walkthrough.js` at all: the shared scene
  player now powers **only Drop In + City Guesser**, while the Window and Step Outside each have
  their own renderer. Verified headless across walk-only / cam-only / neither cases.
- 🇨🇦 **Ontario conservation areas added (Canada 12 → 17):** Point Farms Provincial Park (Lake
  Huron bluff, north of Goderich), the **Grand River** (Canadian Heritage River, pinned at Paris),
  **Elora Gorge**, **Pinery Provincial Park** (Lake Huron oak savanna), and **Rondeau Provincial
  Park** (Lake Erie Carolinian forest). Coordinates + Wikipedia slugs were research-vetted, not
  recalled (Point Farms has no Wikipedia article → it uses `Lake_Huron` imagery with a
  hand-written blurb; all five resolve real gallery photos).
- 🔎 **Map search → autocomplete dropdown (owner ask).** The home-map search is now a real
  combobox: typing surfaces a ranked **suggestion list you pick from** (name-prefix beats
  name-substring beats region/country beats highlight match, top 8), so e.g. `poi` puts **Point
  Farms** right at the top instead of just thinning the markers. Live-cam places are flagged
  `🔴 LIVE` in the list; keyboard ↑/↓/Enter/Esc supported; choosing flies the map there.
  (`index.html` now also loads `webcam.js` for the badge.)
- 🪟 **Window honesty refinement (owner ask): stills are not windows.** Owner reported the window
  showing "just an image of the earth" for a no-cam place. Removed the still-photo fallback
  everywhere a "window" is shown — both the **Virtual Window page** and the location page's
  **Step Outside** window tile now show a live webcam (🔴) or honestly say "window not available"
  (🪟), exactly like virtualvacation.us/window. A Wikipedia lead image is frequently a
  map/satellite/globe shot, which is the opposite of looking out a window — so we never substitute
  one. (Dropped `renderStill` / `.w-pane-still` / `.outside-still` and the night-tint along with it.)
- 🗺️ **Map legibility (owner ask): "places look wrong."** Owner saw pins reading as the wrong
  country (Lake Louise looking like it was in the US). Verified the markers are pixel-perfect
  (DOM centre lands exactly on the projected coordinate, `dx:0,dy:0`) and every coordinate is
  correct — the real problem was the plain dark basemap drawing **no visible country borders or
  labels**. Fix: base is now CARTO `dark_nolabels` with an **Esri "Dark Gray Reference" borders +
  labels overlay** on top (keyless, CORS-safe, dark-themed), so city/country placement reads true.
- 🪟🚶 **Live-content filters (owner ask): "filter to know which have windows / tours / both."**
  Added **🪟 Window / 🚶 Tour / ✨ Both** filters to the map (after a divider from the curation
  filters), driven by `hasWindow` (resolvable webcam) + `hasWalk` (curated `walk`). Filtering now
  also `fitToVisible()` so the few window/both places come on-screen. Same predicates power
  at-a-glance hints — a gold dot on the pin, a "🪟 live window · 🚶 walking tour" tooltip line, and
  🪟/🚶 badges in the search dropdown. Counts: ~29 tours, 12 windows, 4 both (popular places have
  them, most don't — as the owner expected).
- 🗺️ **Map follow-ups (owner round 2): "filters don't work · placement keeps changing on zoom."**
  Two real bugs: (1) the 7-button filter bar **wrapped to 2 rows**, grew upward into the stats bar
  and overlapped the bottom-left FABs, so clicks hit the wrong control — fixed by making it a
  single **scrollable** row (`flex-wrap:nowrap; overflow-x:auto`). (2) markercluster's zoom
  animation **slid** markers from the cluster-centroid to their true spot (~114px of transient
  drift, shrinking as you zoom in) — read as "pins keep moving / are misplaced." Fixed with
  `animate:false` so markers **snap** to position; resting placement was always pixel-perfect.
- 🪟 **Windows 3 → 12 (owner ask): "find obscure live windows, search deep."** Researched +
  **verified-live** (oEmbed *plus* `isLiveNow` on the watch page — most "live cam" uploads are
  archived recordings or seasonal) and added 9: Key West, Honolulu, San Diego, Nashville, Lake
  Tahoe, Tofino (Cox Bay), Rome, Cinque Terre (Vernazza), Amsterdam. Re-confirmed the original 3
  (Niagara, NYC, Venice) are still live. Re-vet periodically with `tools/revet_walks.py --webcam`.
- 🪟🎬 **Window goes HYBRID — live + ambient (owner ask, after we inspected virtualvacation).**
  The owner asked us to actually *visit* `virtualvacation.us/videarth` + `/window` and learn from
  the DOM. We pulled the source: **both are recorded YouTube videos seeked to a `?start=` offset
  and looped — none are live** (videarth = ~1,000 `circleMarker`s over Esri satellite, 3 parallel
  arrays `coords`/`vidids`/`countriesAndCities`, one shared YT player; window = a flat
  `[[name,'id?start=ss'],…]` list, ~120 entries, single player, loops on `ended`). That's how they
  reach hundreds. So the owner chose **Hybrid**: keep our verified 🔴 **live** cams *and* add 🎬
  **ambient** recorded views (seeked + looped) — **always labelled which is which** (pane badge,
  chip prefix, a legend line, and map marker tips/search badges). Built: `Webcam.resolveAmbient` +
  `Webcam.forWindow` (live wins) with the `loop=1&playlist=<id>&start=<s>` loop trick; `window.js`
  hybrid pool + legend; `map.js` `windowKind()` so filters/tooltips distinguish tiers; new
  `tools/verify_ambient.py` (public via oEmbed + `playableInEmbed` + live-vs-recorded). Added **13
  ambient** views (London, Paris, Berlin, Barcelona, Kraków, Stockholm, Toronto, Vancouver,
  Seattle, San Francisco, Washington DC, San Antonio, LA) → **25 windows total**. Rejected walking
  tours / drone montages / geographically-vague "rain on a window" clips — a window must be a
  *stationary* view of the *named* place. The location page **Step Outside** tile stays live-only
  by design (a place's own page promises a real live cam; ambient is for the standalone Window's
  "hop the world").
- 🏛️🔴🚶 **Step Outside → three SEPARATE categories + monument tours (owner round 3).** Owner: the
  "🔴 Live walk" label was dishonest (a walking tour is recorded, never live), the window frame
  must mean *live footage only*, and each city should get **up to 3 named monument tours** (Eiffel
  Tower for Paris, etc.), each category kept clearly separate. Fixed all of it: (1) **label
  honesty** — walking tour is now "🚶 Walking tour" in gold (recorded), and 🔴 is *reserved* for
  real live cams (`location.js`; `.outside-recorded` style). (2) **Window = live-only** on the
  location page again — a live cam (🔴) or an honest "no live cam yet"; recorded loops stay on the
  standalone Window explorer, never passed off as a window here. (3) **Monuments** are a new
  category: `loc.monuments` = up to 3 `{name, yt, start}`, rendered as a tab-picker feeding one
  player (`#monuments-section`, `setupMonuments()`, `.mon-tab*` CSS), hidden when none. Seeded
  **24 real monument tours across 16 cities** (Paris & Rome get the full 3) — harvested from
  `virtualvacation.us/monument` (anonymous `ytid?start=ss` list), *identified by real YouTube
  oEmbed title*, given clean names, and **expanded** into per-city sets; every id confirmed
  embeddable via keyless oEmbed. Tool: `tools/build_monuments.py` (idempotent; re-vet via oEmbed).
- 🔴🚶 **Step Outside layout + live-cam pass (owner round 3 follow-up).** Owner: "still says 🔴
  Live walk — should be just walk; make the walk bigger and put it under; the slot it freed becomes
  just 'Live cam' from one of the hundreds of real live cams out there." Done: (1) **layout** —
  Step Outside top row is now **📹 Live cam + 🪟 Window side by side** (`.outside-top-row`, two
  equal columns), with **🚶 Walk full-width and bigger underneath**; walk label shortened to "Walk".
  (First cut had stacked the live cam full-width and *dropped* the window — owner flagged it; the
  window is back beside the live cam.) The three frames stay distinct: 🔴 Live cam =
  `Webcam.resolve(loc.webcam)` (live only), 🪟 Window = `Webcam.resolveAmbient(loc.ambient)` (a
  stationary recorded loop, 13 cities have one), 🚶 Walk = recorded stroll — each with an honest
  empty state, verified via headless screenshots (London = all three; Rome = live cam + empty
  window). (2) **live-cam content** — built a keyless
  live verifier (`tools/verify_ambient.py`: oEmbed + watch-page `playableInEmbed` + `isLiveNow`),
  web-searched real city cams, and added **5 new verified pub+embed+LIVE cams** (Tokyo Shibuya,
  London Abbey Rd, New Orleans, Chicago Skydeck, SF Bay Bridge) via idempotent
  `tools/build_webcams.py` → **17 cities now have a real live cam** (was 12). Cams that only
  verified "rec" (Berlin/Prague 24/7 streams currently between broadcasts) were **deliberately
  excluded** — a recorded frame must never sit under "🔴 streaming now". Re-vetted all 12 existing
  cams: 0 dead, all still live.
- 🗺️ **Map sizing fix (owner round 3): "Stockholm sits mid-Europe at rest, snaps right on zoom;
  can't pan after I zoom until I click."** Both are classic stale-container-size symptoms (Leaflet
  caches pixel size at init; offset markers + mis-computed drag origin). Added
  `map.invalidateSize()` before fit, again after first paint, and a `ResizeObserver` on `#map`
  (`map.js`). ✅ Owner confirmed pan/scroll works now; resting placement still reads slightly off
  until you zoom (that's marker-cluster centroids, not a size bug — see below).
- 🗺️🐛 **Map click + zoom bugs (owner round 3 follow-up): "clicking Berlin while zoomed doesn't
  open it (search does); after I click a place in China I can't zoom — map's stuck."** Root cause:
  every single marker click ran `flyTo` → a ~3s plane-flight with an animated `fitBounds` that
  zoomed the map *away* from the pin, then navigated. It (a) made the click look dead, (b) left a
  `flying` lock that blocked re-clicks (search bypassed it → "search works"), and (c) when the
  animated zoom was interrupted, stranded Leaflet's `_animatingZoom` state → "can't zoom". Fix in
  `map.js`: a single click now does a short safe `flyTo` ease then navigates on a **guaranteed
  timer** (no fitBounds, no plane, no strandable lock); the plane flight stays only in Fly-the-Tour
  (which removes layers, never navigates). Added a **`pageshow` handler** that resets `flying` and
  re-runs `invalidateSize` + re-enables zoom/drag when the map is restored from the bfcache (Back
  button). Removed now-dead `getDeparture`. ⚠️ Interactive click/zoom could NOT be auto-verified —
  the sandbox kills any Chrome launched with a remote-debugging port, so headless is screenshot-only
  (page loads clean, syntax OK, logic reviewed); owner to re-test the two interactions.
  - **Round 4 (owner: "still misbehaves, worse now — click germany cluster → resizes → click a
    city → centralizes → 3rd click finally opens").** BREAKTHROUGH: got a **real interactive
    browser** working — `chromium --remote-debugging-port` IS allowed if the Bash call sets
    `dangerouslyDisableSandbox`. Drove it over CDP (websocket-client) and reproduced live. Findings:
    (a) the marker click **handler is fine** — `markerById['berlin'].fire('click')` navigates every
    time; (b) the bug is **clustering**: at the zooms the owner uses, cities are still inside
    clusters, so a click hits the *cluster* (zoom-to-bounds) not the pin → the multi-click drill;
    (c) my round-3/round-4 `disableClusteringAtZoom: 8` made it WORSE — kept dense Europe clustered
    until zoom 8, so you drill 8→ before a pin is individual. Fixes in `map.js`: **`maxClusterRadius
    44→32`** + **`disableClusteringAtZoom 8→5`** (cities become individual, one-click-open pins by
    "looking at one country" zoom — screenshot-confirmed: at zoom 5 `clusterBlobs:0`, Berlin renders
    as its own pin over its label). Plus `flyTo` **navigates immediately, zero map animation** (=
    the search path, which the owner confirms works), and `pageshow` calls **`map.stop()`** +
    re-enables all zoom handlers. **Verified live:** back-to-map → wheel zoom 2→4 WORKS, drag
    enabled, `flying=False` (the "can't zoom after back" bug is fixed). NOT auto-verifiable: the
    exact pixel click-to-open — markercluster + headless CDP wheel desyncs marker Y rendering (a
    test-harness artifact; page is correctly viewport-locked, no scroll), so the final "click a city
    → it opens" is for the owner to confirm in a real browser.
  - **Round 5 (owner: "even worse — zoom in and EVERYTHING disappears; the FIRST version was best:
    click one circle → it opens up to the places inside").** The round-4 `disableClusteringAtZoom: 5`
    was itself the regression. Proved it with a live CDP zoom-sweep over Germany: at z4 there are 79
    cluster bubbles; the instant you cross **z5 the count snaps to 0** and all 345 markers become
    loose pins, which then scatter off the small viewport as you keep zooming (`pinsOnScreen` z10=0,
    `pinDivs` z12+=0 → *"everything disappears."*). **Root cause = forcing declustering at a fixed
    zoom at all.** Fix in `map.js`: **deleted `disableClusteringAtZoom` entirely** and set
    **`maxClusterRadius 32→60`**. Now clustering degrades by pixel-distance only (z4→8 bubbles
    65→49→26→5→1 then individual), so you ALWAYS see guiding bubbles, a cluster click zoom-to-bounds
    reveals its members (never blank), and a lone city already renders as its own one-click pin. This
    restores the original behaviour the owner liked. **Verified live in a real browser (CDP):**
    (1) real DOM click on a Germany cluster (count=4) zoomed 4→6 and expanded into 8 bubbles + 7 pins;
    (2) one real click at the *projected* pixel of Berlin / Paris / Madrid → `nav=<city>` = opens in
    ONE click; (3) screenshot `verify_berlin_z11.png` shows the Berlin pin sitting exactly on the
    projected coordinate (so a real user's click lands on it); (4) full round-trip open-place →
    back-to-map → wheel zoom 2→6 works, drag enabled, `flying=False`, and a synthetic bfcache
    `pageshow(persisted)` keeps it interactive. Both headline bugs now reproduced-then-fixed against
    a live browser, not just reasoned about. (Test scripts: `scratchpad/{sweep,flow2,verify2,
    backflow2}.py`; the CDP-via-`dangerouslyDisableSandbox` harness is the reusable win here.)

---

## 🔜 Next up (prioritized)

### 0. 🗺️ Map — headline bugs FIXED & live-verified (round 5); owner to sanity-check in their browser
- ✅ **Both map bugs reproduced live and fixed** (clustering config: removed `disableClusteringAtZoom`,
  `maxClusterRadius 32→60`). One-click-open, click-circle-expands, zoom-after-back all verified over
  CDP — see the Round-5 entry above. **Owner: hard-refresh `http://127.0.0.1:8099` and confirm** the
  feel is right; the only thing a headless browser can't fully stand in for is the human "does the
  click land where I expect" — every measurement says yes.
- 🔎 **Findability dropdown.** Vienna/Prague/Budapest *already exist* but the owner couldn't find
  them — add a continent→country→city filter dropdown (and surface the existing search better).
- 💡 **Creative map ideas (further development).** (a) **Cluster hover/long-press preview** — a small
  popover listing the city names inside a bubble, so you know what's in there before drilling.
  (b) **"Spin the globe" / Surprise-region** — zoom-fly to a random *cluster* (not just a pin) to
  encourage exploration. (c) **Visited-progress heat** — tint clusters by how many of their cities
  you've explored (we already track `_visited`; `owt-cluster-done` exists for all-visited — add a
  partial gradient). (d) **Live-content clusters** — when the 🔴/🪟 filter is on, badge clusters with
  a count of live cams inside. (e) **Mini-map "you are here" graticule** on deep zoom so a lone pin in
  empty terrain still feels located. All are additive; none require touching the now-stable core.
- ✅ **Windows + live cams — DONE at scale via Windy** (247 windows / 105 live; see the Done entry +
  `DEVNOTES.md` §3f). Re-run `python3 tools/fetch_windy.py` periodically to refresh (cams change).
- 🚶 **Walks — 29 → 51 (22 added, web-searched + oEmbed-verified, render-confirmed).** New marquee/major
  cities now have a guided walk: Tokyo, Kyoto, Osaka, Sydney, Dubai, Bangkok, Singapore, Hanoi,
  Hong Kong, Shanghai, Beijing, Kuala Lumpur, Manila, Taipei, New Delhi, Mumbai, Seoul, Cape Town,
  Marrakesh, Cairo, Nairobi, Buenos Aires. Method in §4; ids applied via `scratchpad/apply_walks.py`,
  vetted with `scratchpad/vet.py`. **Still to do:** the rest of the 294 without walks (next obvious set:
  more LatAm/Africa/SE-Asia capitals), and a periodic `tools/revet_walks.py` to swap rotted ids.
- 🏛️ **Monuments/tours — still sparse (manual, same vetted process).** Most cities have 0 `monuments`
  (Tokyo M2, Cairo/Seoul M1). Author 1–3 landmark videos each for the marquee cities (Sydney→Opera
  House/Harbour Bridge, Dubai→Burj Khalifa, Cape Town→Table Mountain, Agra→Taj Mahal, etc.). Next up.
- 🔴 **Curated live-cam upgrades (optional, quality over the Windy default).** Where a famous YouTube
  live cam beats the nearest Windy cam, add it as `loc.webcam` (it auto-outranks Windy). Re-check
  Berlin Brandenburg Gate `v5OUHl8c9Es`, Prague `0FvTdT3EJY4` when they flip LIVE; Times Square,
  Venice, Shibuya, Bondi are usually strong.

### 1. 🌍 City Guesser & 🪟 Window polish (virtualvacation parity, then past it)
Region filter + shareable score, the Drop-In empty state, and the Window rebuild — now **hybrid
live + ambient**, labelled which-is-which, ambient sound, remember-last — are done (see ✅ above).
Remaining:
- 🪟 **`onError`→"window not available" fallback on the YouTube window iframe.** Curated YT cam ids
  rot, so a dead id shows a broken frame. Add the same `onError` guard `walkthrough.js` has, degrading
  to the honest empty state — or, with the tiers we now have, **auto-fall-back to the place's Windy
  window** (`windowFor` already resolves it) before giving up. (Windy embeds self-handle an offline cam
  with their own message, so this is now mainly about the curated-YouTube cams.)
- 🪟🎬 **Windows — 247/345 now have one (via Windy, see Done).** The 98 still empty are mostly remote
  (no cam within 50km). For the marquee ones, a hand-curated ambient still beats nothing where a Windy
  cam is too far; the curated-wins-over-Windy precedence means any `loc.ambient`/`loc.webcam` you add
  auto-takes priority. `tools/verify_ambient.py` (public + `playableInEmbed`, a *stationary* view of
  the *named* place) is still the vetting tool for curated ambients.
- 🪟 Window: optionally let the ambient bed be the place's **live local radio** (via `radio.js`)
  instead of the synth, for the cities that have stations.
- Guesser: optional **timed / "no skipping" hard mode** (opt-in tension; the scene stays
  skippable by default — that's still the differentiator). Maybe remember the last region picked.
- More curated `walk` ids beyond the current 29 (esp. as new regions land), and a periodic
  `tools/revet_walks.py` run to swap any that rot.

### 2. 🧱 Code organization (continue the split)
`walkthrough.js` + `destinations.js` are extracted ✅. `location.js` is still ~840 lines.
Peel off more pieces alongside a visible feature (never solo): `webcam.js`, `postcard.js`,
`culture-panel.js`. Defer a slim generated `data/locations-index.json` until 2–3 more regions
land (so pages stop fetching *every* region JSON on every load).

### 3. 🌏 World coverage — ✅ BREADTH DONE, now DEPTH
All 89 countries / 345 locations are on the map (Asia, Africa, Oceania, Latin America added;
see the Done entry + `COUNTRIES.md` + `OVERHAUL.md`). Remaining is *depth* on the new countries:
- **Curate windows + walks for marquee new cities** (Tokyo, Sydney, Dubai, Buenos Aires, Cape Town,
  Bangkok…) — same verified-live process as the existing 12 windows / 29 walks. (Widens the Window +
  City Guesser pool too.)
- **Author `highlights` + `blurb`/`fun_fact`** for the strongest new places (today they fall back to
  the live Wikipedia summary — honest, but the marquee ones deserve curated copy).
- **Native-speaker review of the 50 new culture profiles** (phrases/dishes) — `OVERHAUL.md` I-10.
- Structural follow-ups (not blocking): convert `ancient` from a region to a `collections` tag (I-3),
  land the slim `data/index.geo.json` lazy index now that 8 region files load (I-5).

---

## 🅿️ Parked (see IDEAS.md)
- **Satellite "descend from orbit" — dropped by owner:** we already have the map; it'd be a
  lot of work for little gain. Not doing it.
- "Back in Time" historical/Indigenous borders timeline (big lift, own mode).
- Multiplayer / private rooms for City Guesser (virtualvacation has these — big lift).
- 360° photosphere & Mapillary street-level tiers for the walkthrough.
- Curating many more live-cam ids.
